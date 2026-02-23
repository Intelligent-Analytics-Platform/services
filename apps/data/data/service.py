"""Business logic for data upload and processing pipeline."""

import logging
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pandas as pd
from sqlalchemy.orm import Session

from data import pipeline
from data.database import _SessionFactory, get_duck_conn
from data.models import VesselDataUpload
from data.repository import UploadRepository

logger = logging.getLogger(__name__)

# Fuel consumption columns (actual, not accumulated) used for CII_temp calculation
_CONS_COLS = [
    "me_hfo_act_cons",
    "me_mgo_act_cons",
    "blr_hfo_act_cons",
    "blr_mgo_act_cons",
    "dg_hfo_act_cons",
    "dg_mgo_act_cons",
]


class DataService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = UploadRepository(session)

    # ── Upload record management ─────────────────────────────────────────────

    def create_upload_record(self, vessel_id: int, file_path: str) -> VesselDataUpload:
        upload = VesselDataUpload(vessel_id=vessel_id, file_path=file_path)
        return self.repo.create(upload)

    def get_upload_status(self, upload_id: int) -> VesselDataUpload:
        return self.repo.get_or_raise(upload_id)

    def list_upload_history(
        self, vessel_id: int, offset: int, limit: int
    ) -> list[VesselDataUpload]:
        return self.repo.list_by_vessel(vessel_id, offset=offset, limit=limit)

    # ── Background processing pipeline ──────────────────────────────────────

    @staticmethod
    def process_upload(
        upload_id: int,
        vessel_id: int,
        file_path: str,
        pitch: float,
        vessel_capacity: float | None,
    ) -> None:
        """Full data processing pipeline. Runs as a FastAPI BackgroundTask.

        Creates its own DB sessions so it works after the request completes.
        Steps:
          1. status = processing
          2. Read CSV → insert original data to DuckDB
          3. Clean data → insert standard data to DuckDB
          4. Aggregate by day → upsert vessel_data_per_day
          5. Calculate CII_temp (if vessel_capacity provided)
          6. Calculate cumulative CII via SQL window function
          7. status = done (or failed + error_message on exception)
        """
        session = _SessionFactory()
        try:
            repo = UploadRepository(session)
            upload = repo.get_or_raise(upload_id)
            repo.update(upload, {"status": "processing"})
            session.commit()

            df = pd.read_csv(file_path)
            logger.info("upload %d: read %d rows from %s", upload_id, len(df), file_path)

            with get_duck_conn() as conn:
                # Step 1: raw data
                DataService._insert_telemetry(conn, "vessel_original_data", vessel_id, df)
                logger.info("upload %d: inserted %d original rows", upload_id, len(df))

                # Step 2: cleaned data
                df_clean = pipeline.data_preparation(df.copy(), pitch)
                logger.info("upload %d: %d rows after cleaning", upload_id, len(df_clean))
                if not df_clean.empty:
                    DataService._insert_telemetry(
                        conn, "vessel_standard_data", vessel_id, df_clean
                    )
                    DataService._upsert_per_day(conn, vessel_id, df_clean)

                    # Step 3: CII
                    if vessel_capacity and vessel_capacity > 0:
                        DataService._calculate_cii_temp(conn, vessel_id, vessel_capacity)
                        DataService._calculate_cii(conn, vessel_id)

            # Derive date range from raw data
            date_col = df.get("date") if "date" in df.columns else None
            date_start = pd.to_datetime(date_col, errors="coerce").min().date() if date_col is not None else None
            date_end = pd.to_datetime(date_col, errors="coerce").max().date() if date_col is not None else None

            repo.update(
                upload,
                {
                    "status": "done",
                    "date_start": date_start,
                    "date_end": date_end,
                    "completed_at": datetime.now(tz=timezone.utc),
                },
            )
            session.commit()
            logger.info("upload %d: completed successfully", upload_id)

        except Exception as exc:
            logger.exception("upload %d: failed - %s", upload_id, exc)
            try:
                repo = UploadRepository(session)
                upload = repo.get_or_raise(upload_id)
                repo.update(
                    upload,
                    {
                        "status": "failed",
                        "error_message": str(exc)[:1000],
                        "completed_at": datetime.now(tz=timezone.utc),
                    },
                )
                session.commit()
            except Exception:
                session.rollback()
        finally:
            session.close()

    # ── DuckDB helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _insert_telemetry(
        conn: duckdb.DuckDBPyConnection,
        table: str,
        vessel_id: int,
        df: pd.DataFrame,
    ) -> None:
        """Insert DataFrame rows into a DuckDB telemetry table.

        DuckDB can reference local pandas DataFrames by variable name directly.
        INSERT BY NAME maps DataFrame columns to table columns by name.
        """
        df = df.copy()
        df["vessel_id"] = vessel_id
        df["created_at"] = pd.Timestamp.now()
        conn.register("_telemetry_df", df)
        conn.execute(
            f"INSERT INTO {table} BY NAME "  # noqa: S608
            f"SELECT nextval('{table}_seq') AS id, * FROM _telemetry_df"
        )
        conn.unregister("_telemetry_df")

    @staticmethod
    def _upsert_per_day(
        conn: duckdb.DuckDBPyConnection, vessel_id: int, df: pd.DataFrame
    ) -> None:
        """Aggregate df by date (mean) and upsert into vessel_data_per_day."""
        daily = df.groupby("date").mean(numeric_only=True).reset_index()
        daily["vessel_id"] = vessel_id

        # Remove existing rows for these dates, then insert
        conn.register("_daily_df", daily)
        conn.execute(
            "DELETE FROM vessel_data_per_day "
            "WHERE vessel_id = $1 AND date IN (SELECT date FROM _daily_df)",
            [vessel_id],
        )
        conn.execute(
            "INSERT INTO vessel_data_per_day BY NAME SELECT * FROM _daily_df"
        )
        conn.unregister("_daily_df")

    @staticmethod
    def _calculate_cii_temp(
        conn: duckdb.DuckDBPyConnection, vessel_id: int, c: float
    ) -> None:
        """Calculate CII_temp for daily records using SQL.

        CII_temp = Σ (cons_col / speed_water) * (CF * 1000 / C)
        """
        parts = []
        for col in _CONS_COLS:
            cf = pipeline.get_cf(col)
            if cf > 0:
                factor = cf * 1000 / c
                parts.append(
                    f"CASE WHEN speed_water > 0 THEN ({col} / speed_water) * {factor} ELSE 0 END"
                )
        if not parts:
            return

        formula = " + ".join(parts)
        conn.execute(
            f"UPDATE vessel_data_per_day SET cii_temp = {formula} "  # noqa: S608
            f"WHERE vessel_id = {vessel_id} AND cii_temp = 0"
        )

    @staticmethod
    def _calculate_cii(conn: duckdb.DuckDBPyConnection, vessel_id: int) -> None:
        """Calculate cumulative annual CII using a SQL window function.

        CII = running average of cii_temp within each calendar year,
        ordered by date (IMO rolling average approach).
        """
        conn.execute(
            """
            UPDATE vessel_data_per_day AS d
            SET cii = sub.cii
            FROM (
                SELECT vessel_id, date,
                       AVG(cii_temp) OVER (
                           PARTITION BY vessel_id, YEAR(date)
                           ORDER BY date
                           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                       ) AS cii
                FROM vessel_data_per_day
                WHERE vessel_id = $1
            ) AS sub
            WHERE d.vessel_id = sub.vessel_id AND d.date = sub.date
            """,
            [vessel_id],
        )

    # ── Query helpers ────────────────────────────────────────────────────────

    @staticmethod
    def get_daily_data(
        vessel_id: int, offset: int = 0, limit: int = 100
    ) -> list[dict]:
        """Return daily aggregated data for a vessel from DuckDB."""
        with get_duck_conn() as conn:
            result = conn.execute(
                """
                SELECT vessel_id, date,
                       speed_ground, speed_water, me_shaft_power, me_rpm,
                       me_fuel_consumption_nmile,
                       me_hfo_act_cons, me_mgo_act_cons,
                       blr_hfo_act_cons, blr_mgo_act_cons,
                       dg_hfo_act_cons, dg_mgo_act_cons,
                       slip_ratio, draft, wind_speed,
                       cii_temp, cii
                FROM vessel_data_per_day
                WHERE vessel_id = $1
                ORDER BY date DESC
                LIMIT $2 OFFSET $3
                """,
                [vessel_id, limit, offset],
            ).df()
        return result.to_dict(orient="records")

    @staticmethod
    def save_upload_file(file_bytes: bytes, vessel_name: str, upload_dir: str) -> str:
        """Write uploaded bytes to disk and return the relative file path."""
        today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
        ts = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
        rel_path = f"{upload_dir}/{today}/{vessel_name}-{ts}.csv"
        full_path = Path(rel_path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(file_bytes)
        return rel_path
