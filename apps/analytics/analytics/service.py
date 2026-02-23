"""Business logic for the analytics service.

All data is read from DuckDB (vessel_standard_data, vessel_data_per_day)
opened in read-only mode.  Vessel metadata (dead_weight, gross_tone,
ship_type_code) is fetched from the vessel / meta services via HTTP.
"""

from __future__ import annotations

import glob
import logging
import math
import pickle
import re
from collections import Counter
from datetime import date

import numpy as np
import pandas as pd

from analytics.cii_rating import (
    get_cii_boundaries,
    get_cii_rating,
)
from analytics.client import get_vessel_info
from analytics.database import get_duck_conn
from analytics.schemas import (
    AttributeFrequency,
    AttributeRelation,
    AttributeValue,
    ConsumptionStatistic,
    OptimizationValues,
    TrimDataAverages,
    TrimDataPoint,
    TrimDataResponse,
    VesselCiiData,
    VesselDataPerDayAverage,
    VesselStandardDataInfo,
)

logger = logging.getLogger(__name__)

# ── Column whitelists (prevent SQL injection via attribute_name params) ───────

_PER_DAY_COLS: set[str] = {
    "speed_ground",
    "speed_water",
    "draft",
    "heel",
    "trim",
    "draught_astern",
    "draught_bow",
    "draught_mid_left",
    "draught_mid_right",
    "me_rpm",
    "wind_speed",
    "wind_direction",
    "slip_ratio",
    "me_fuel_consumption_nmile",
    "me_fuel_consumption_kwh",
    "me_shaft_power",
    "me_torque",
    "me_hfo_act_cons",
    "me_mgo_act_cons",
    "blr_hfo_act_cons",
    "blr_mgo_act_cons",
    "dg_hfo_act_cons",
    "dg_mgo_act_cons",
    "ship_nmile",
    "cii_temp",
    "cii",
}

_STD_COLS: set[str] = {
    "speed_ground",
    "speed_water",
    "draft",
    "heel",
    "trim",
    "draught_astern",
    "draught_bow",
    "draught_mid_left",
    "draught_mid_right",
    "me_rpm",
    "wind_speed",
    "wind_direction",
    "slip_ratio",
    "me_fuel_consumption_nmile",
    "me_fuel_consumption_kwh",
    "me_shaft_power",
    "me_torque",
    "latitude",
    "longitude",
    "date",
    "time",
    "ship_nmile",
}

_EQUIPMENT_TYPES = {"me", "dg", "blr"}
_FUEL_TYPES = {"hfo", "mgo", "lfo", "mdo"}


def _assert_col(col: str, allowed: set[str]) -> None:
    if col not in allowed:
        from fastapi import HTTPException  # local import to avoid circular

        raise HTTPException(status_code=400, detail=f"unsupported attribute: {col}")


# ── Helpers ──────────────────────────────────────────────────────────────────


def _nan_to_none(v):
    if isinstance(v, float) and math.isnan(v):
        return None
    return v


def _row_to_dict(row, keys: list[str]) -> dict:
    return {k: _nan_to_none(v) for k, v in zip(keys, row, strict=False)}


# ── Statistic service ────────────────────────────────────────────────────────


class StatisticService:
    # ── Attribute analysis ───────────────────────────────────────────────

    @staticmethod
    def get_attribute_frequencies(
        attribute_name: str,
        vessel_id: int,
        start_date: date,
        end_date: date,
        min_slip_ratio: float,
        max_slip_ratio: float,
    ) -> list[AttributeFrequency]:
        _assert_col(attribute_name, _STD_COLS)
        with get_duck_conn() as conn:
            rows = conn.execute(
                f"""
                SELECT {attribute_name}
                FROM vessel_standard_data
                WHERE vessel_id = $1
                  AND date BETWEEN $2 AND $3
                  AND slip_ratio BETWEEN $4 AND $5
                  AND {attribute_name} IS NOT NULL
                """,  # noqa: S608
                [vessel_id, start_date, end_date, min_slip_ratio, max_slip_ratio],
            ).fetchall()

        values = [r[0] for r in rows]
        if not values:
            return []

        # Round to 2 decimal places and count
        rounded = [round(v, 2) for v in values]
        counter = Counter(rounded)
        total = len(rounded)
        result = [
            AttributeFrequency(
                attribute_value=val,
                frequency=cnt,
                percentage=round(cnt / total * 100, 2),
            )
            for val, cnt in sorted(counter.items())
            if cnt > 1  # filter_low_frequency threshold = 1
        ]
        return result

    @staticmethod
    def get_attribute_values(
        attribute_name: str,
        vessel_id: int,
        start_date: date,
        end_date: date,
        min_slip_ratio: float,
        max_slip_ratio: float,
    ) -> list[AttributeValue]:
        _assert_col(attribute_name, _PER_DAY_COLS)
        with get_duck_conn() as conn:
            rows = conn.execute(
                f"""
                SELECT date, {attribute_name}
                FROM vessel_data_per_day
                WHERE vessel_id = $1
                  AND date BETWEEN $2 AND $3
                  AND slip_ratio BETWEEN $4 AND $5
                ORDER BY date
                """,  # noqa: S608
                [vessel_id, start_date, end_date, min_slip_ratio, max_slip_ratio],
            ).fetchall()
        return [AttributeValue(date=r[0], value=_nan_to_none(r[1])) for r in rows]

    @staticmethod
    def get_attribute_relation(
        attribute_name1: str,
        attribute_name2: str,
        vessel_id: int,
        start_date: date,
        end_date: date,
        min_slip_ratio: float,
        max_slip_ratio: float,
    ) -> list[AttributeRelation]:
        _assert_col(attribute_name1, _PER_DAY_COLS)
        _assert_col(attribute_name2, _PER_DAY_COLS)
        with get_duck_conn() as conn:
            rows = conn.execute(
                f"""
                SELECT {attribute_name1}, {attribute_name2}
                FROM vessel_data_per_day
                WHERE vessel_id = $1
                  AND date BETWEEN $2 AND $3
                  AND slip_ratio BETWEEN $4 AND $5
                """,  # noqa: S608
                [vessel_id, start_date, end_date, min_slip_ratio, max_slip_ratio],
            ).fetchall()
        return [
            AttributeRelation(value1=_nan_to_none(r[0]), value2=_nan_to_none(r[1])) for r in rows
        ]

    # ── CII ─────────────────────────────────────────────────────────────

    @staticmethod
    def get_vessel_cii(vessel_id: int) -> list[VesselCiiData]:
        info = get_vessel_info(vessel_id)
        with get_duck_conn() as conn:
            rows = conn.execute(
                """
                SELECT date, cii, cii_temp
                FROM vessel_data_per_day
                WHERE vessel_id = $1
                  AND date >= (current_date - INTERVAL 1 YEAR)
                ORDER BY date
                """,
                [vessel_id],
            ).fetchall()

        result = []
        for r in rows:
            d, cii_val, cii_temp = r[0], r[1], r[2]
            year = d.year if hasattr(d, "year") else int(str(d)[:4])
            cii_val = _nan_to_none(cii_val)
            cii_temp = _nan_to_none(cii_temp)

            if cii_val is not None and cii_val > 0:
                rating = get_cii_rating(
                    cii_val, year, info.ship_type_code, info.dead_weight, info.gross_tone
                )
                bounds = get_cii_boundaries(
                    year, info.ship_type_code, info.dead_weight, info.gross_tone
                )
            else:
                rating = "N/A"
                bounds = {"superior": 0.0, "lower": 0.0, "upper": 0.0, "inferior": 0.0}

            result.append(
                VesselCiiData(
                    cii=cii_val,
                    cii_temp=cii_temp,
                    date=d,
                    rating=rating,
                    **bounds,
                )
            )
        return result

    # ── Data completeness ────────────────────────────────────────────────

    @staticmethod
    def get_vessel_completeness(vessel_id: int) -> list[tuple[str, int]]:
        """Return [(year-month, count)] for the last 5 years."""
        with get_duck_conn() as conn:
            rows = conn.execute(
                """
                SELECT strftime(date, '%Y-%m') AS ym, COUNT(*) AS cnt
                FROM vessel_data_per_day
                WHERE vessel_id = $1
                  AND date >= (current_date - INTERVAL 5 YEAR)
                GROUP BY ym
                ORDER BY ym
                """,
                [vessel_id],
            ).fetchall()
        return [(r[0], r[1]) for r in rows]

    # ── Date-range data info (vessel_standard_data with sampling) ────────

    @staticmethod
    def get_vessel_data_info_by_date_range(
        vessel_id: int,
        start_date: date,
        end_date: date,
        sample_interval: int = 10,
    ) -> list[VesselStandardDataInfo]:
        _FIELDS = [
            "speed_ground",
            "speed_water",
            "draft",
            "heel",
            "trim",
            "draught_astern",
            "draught_bow",
            "draught_mid_left",
            "draught_mid_right",
            "me_rpm",
            "wind_speed",
            "wind_direction",
            "slip_ratio",
            "me_fuel_consumption_nmile",
            "me_fuel_consumption_kwh",
            "me_shaft_power",
            "me_torque",
            "latitude",
            "longitude",
            "date",
            "time",
            "ship_nmile",
        ]
        sel = ", ".join(_FIELDS)
        with get_duck_conn() as conn:
            if sample_interval > 1:
                rows = conn.execute(
                    f"""
                    SELECT {sel} FROM (
                        SELECT {sel},
                               ROW_NUMBER() OVER (ORDER BY date, time) AS rn
                        FROM vessel_standard_data
                        WHERE vessel_id = $1
                          AND date BETWEEN $2 AND $3
                    )
                    WHERE (rn - 1) % $4 = 0
                    ORDER BY date, time
                    """,  # noqa: S608
                    [vessel_id, start_date, end_date, sample_interval],
                ).fetchall()
            else:
                rows = conn.execute(
                    f"""
                    SELECT {sel}
                    FROM vessel_standard_data
                    WHERE vessel_id = $1
                      AND date BETWEEN $2 AND $3
                    ORDER BY date, time
                    """,  # noqa: S608
                    [vessel_id, start_date, end_date],
                ).fetchall()

        result = []
        for row in rows:
            d = _row_to_dict(row, _FIELDS)
            # time may be a datetime.time object → stringify
            if d.get("time") is not None and hasattr(d["time"], "strftime"):
                d["time"] = d["time"].strftime("%H:%M:%S")
            elif d.get("time") is not None:
                d["time"] = str(d["time"])
            # speed_ground: keep as float
            result.append(VesselStandardDataInfo(**d))
        return result

    # ── Consumption statistics ───────────────────────────────────────────

    @staticmethod
    def get_consumption_statistic_nmile(
        fuel_type: str,
        vessel_id: int,
        start_date: date,
        end_date: date,
    ) -> ConsumptionStatistic:
        """Average fuel consumption per nautical mile for each equipment type."""
        if fuel_type not in _FUEL_TYPES:
            from fastapi import HTTPException

            raise HTTPException(status_code=400, detail=f"unsupported fuel_type: {fuel_type}")

        def _col(equip: str) -> str:
            return f"{equip}_{fuel_type}_act_cons"

        with get_duck_conn() as conn:
            # date range (actual data bounds)
            dates = conn.execute(
                """
                SELECT MIN(date), MAX(date) FROM vessel_data_per_day
                WHERE vessel_id = $1 AND date BETWEEN $2 AND $3
                """,
                [vessel_id, start_date, end_date],
            ).fetchone()
            real_start = str(dates[0]) if dates and dates[0] else ""
            real_end = str(dates[1]) if dates and dates[1] else ""

            stat = ConsumptionStatistic(real_start_date=real_start, real_end_date=real_end)
            for equip in ("me", "dg", "blr"):
                col = _col(equip)
                row = conn.execute(
                    f"""
                    SELECT AVG({col} / NULLIF(speed_water, 0))
                    FROM vessel_data_per_day
                    WHERE vessel_id = $1
                      AND date BETWEEN $2 AND $3
                      AND speed_water > 0
                      AND {col} IS NOT NULL
                    """,  # noqa: S608
                    [vessel_id, start_date, end_date],
                ).fetchone()
                val = row[0] if row and row[0] is not None else 0.0
                setattr(stat, equip, round(float(val), 6))

        stat.total = round(stat.me + stat.dg + stat.blr, 6)
        return stat

    @staticmethod
    def get_consumption_statistic_total(
        fuel_type: str,
        vessel_id: int,
        start_date: date,
        end_date: date,
    ) -> ConsumptionStatistic:
        """Total fuel consumption (sum of act_cons) for each equipment type."""
        if fuel_type not in _FUEL_TYPES:
            from fastapi import HTTPException

            raise HTTPException(status_code=400, detail=f"unsupported fuel_type: {fuel_type}")

        def _col(equip: str) -> str:
            return f"{equip}_{fuel_type}_act_cons"

        with get_duck_conn() as conn:
            dates = conn.execute(
                """
                SELECT MIN(date), MAX(date) FROM vessel_data_per_day
                WHERE vessel_id = $1 AND date BETWEEN $2 AND $3
                """,
                [vessel_id, start_date, end_date],
            ).fetchone()
            real_start = str(dates[0]) if dates and dates[0] else ""
            real_end = str(dates[1]) if dates and dates[1] else ""

            stat = ConsumptionStatistic(real_start_date=real_start, real_end_date=real_end)
            for equip in ("me", "dg", "blr"):
                col = _col(equip)
                row = conn.execute(
                    f"""
                    SELECT SUM({col})
                    FROM vessel_data_per_day
                    WHERE vessel_id = $1
                      AND date BETWEEN $2 AND $3
                      AND {col} IS NOT NULL
                    """,  # noqa: S608
                    [vessel_id, start_date, end_date],
                ).fetchone()
                val = row[0] if row and row[0] is not None else 0.0
                setattr(stat, equip, round(float(val), 6))

        stat.total = round(stat.me + stat.dg + stat.blr, 6)
        return stat

    # ── Vessel average ───────────────────────────────────────────────────

    @staticmethod
    def get_vessel_average(
        vessel_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> VesselDataPerDayAverage:
        with get_duck_conn() as conn:
            if start_date and end_date:
                row = conn.execute(
                    """
                    SELECT AVG(speed_water), AVG(me_fuel_consumption_nmile)
                    FROM vessel_data_per_day
                    WHERE vessel_id = $1 AND date BETWEEN $2 AND $3
                    """,
                    [vessel_id, start_date, end_date],
                ).fetchone()
            else:
                row = conn.execute(
                    """
                    SELECT AVG(speed_water), AVG(me_fuel_consumption_nmile)
                    FROM vessel_data_per_day
                    WHERE vessel_id = $1
                      AND date >= (current_date - INTERVAL 7 DAY)
                    """,
                    [vessel_id],
                ).fetchone()

        speed = float(row[0] or 0)
        nmile = float(row[1] or 0)
        return VesselDataPerDayAverage(speed_water=speed, me_fuel_consumption_nmile=nmile)


# ── Optimisation service ─────────────────────────────────────────────────────


class OptimizationService:
    @staticmethod
    def get_optimization_values(
        vessel_id: int, start_date: date, end_date: date
    ) -> OptimizationValues:
        info = get_vessel_info(vessel_id)
        with get_duck_conn() as conn:
            row = conn.execute(
                """
                SELECT AVG(speed_water), AVG(cii), MAX(date)
                FROM vessel_data_per_day
                WHERE vessel_id = $1 AND date BETWEEN $2 AND $3
                """,
                [vessel_id, start_date, end_date],
            ).fetchone()

        if not row or row[0] is None:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="no data for this vessel / date range")

        avg_speed = float(row[0] or 0)
        avg_cii = float(row[1] or 0)
        last_date = row[2]
        year = last_date.year if last_date and hasattr(last_date, "year") else end_date.year

        cii_rating = (
            get_cii_rating(avg_cii, year, info.ship_type_code, info.dead_weight, info.gross_tone)
            if avg_cii > 0
            else "N/A"
        )

        return OptimizationValues(
            gross_ton=info.gross_tone,
            speed_water=avg_speed,
            cii=avg_cii,
            cii_rating=cii_rating,
        )

    @staticmethod
    def get_trim_data(vessel_id: int, start_date: date, end_date: date) -> TrimDataResponse:
        info = get_vessel_info(vessel_id)
        with get_duck_conn() as conn:
            trim_rows = conn.execute(
                """
                SELECT date, trim FROM vessel_data_per_day
                WHERE vessel_id = $1 AND date BETWEEN $2 AND $3
                  AND trim IS NOT NULL
                ORDER BY date
                """,
                [vessel_id, start_date, end_date],
            ).fetchall()

            avg_row = conn.execute(
                """
                SELECT AVG(trim), AVG(draft), AVG(speed_water),
                       AVG(me_fuel_consumption_nmile), AVG(cii)
                FROM vessel_data_per_day
                WHERE vessel_id = $1 AND date BETWEEN $2 AND $3
                """,
                [vessel_id, start_date, end_date],
            ).fetchone()

        trim_values = [TrimDataPoint(date=r[0], trim=float(r[1])) for r in trim_rows]

        avg_cii = float(avg_row[4] or 0)
        year = end_date.year
        cii_rating = (
            get_cii_rating(avg_cii, year, info.ship_type_code, info.dead_weight, info.gross_tone)
            if avg_cii > 0
            else "N/A"
        )

        averages = TrimDataAverages(
            trim=float(avg_row[0] or 0),
            draft=float(avg_row[1] or 0),
            speed_water=float(avg_row[2] or 0),
            me_fuel_consumption_nmile=float(avg_row[3] or 0),
            cii=avg_cii,
            cii_rating=cii_rating,
        )
        return TrimDataResponse(trim_values=trim_values, averages=averages)

    @staticmethod
    def optimize_ship_speed(
        vessel_id: int,
        start_date: date,
        end_date: date,
        models_dir: str,
    ) -> list[dict]:
        """Speed-optimisation via XGBoost model.  Requires models_dir to contain
        a file matching ``{vessel_id}_XGBoost_v*_(all|less).pkl``."""
        model_files = glob.glob(f"{models_dir}/{vessel_id}_XGBoost_*.pkl")
        if not model_files:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=404,
                detail=(
                    f"No XGBoost model found for vessel {vessel_id} "
                    f"in {models_dir}.  Train and place the model there first."
                ),
            )

        def _extract_version(f: str) -> tuple[int, str]:
            m = re.search(r"v(\d+)_(all|less)", f)
            return (int(m.group(1)), m.group(2)) if m else (0, "")

        valid = [(f, *_extract_version(f)) for f in model_files if _extract_version(f)[1]]
        valid.sort(key=lambda x: -x[1])
        selected_file, version, model_type = valid[0]
        with open(selected_file, "rb") as fh:
            model = pickle.load(fh)  # noqa: S301

        info = get_vessel_info(vessel_id)

        with get_duck_conn() as conn:
            rows = conn.execute(
                """
                SELECT date, wind_speed, wind_direction, speed_water, speed_ground,
                       draught_bow, draught_astern, draught_mid_left, draught_mid_right,
                       heel, trim, draft, me_rpm, me_shaft_power, slip_ratio,
                       cii, me_fuel_consumption_nmile, ship_nmile
                FROM vessel_data_per_day
                WHERE vessel_id = $1 AND date BETWEEN $2 AND $3
                ORDER BY date
                """,
                [vessel_id, start_date, end_date],
            ).fetchall()

        if not rows:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="no data for this vessel / date range")

        _COLS = [
            "PCTime",
            "WindSpd",
            "WindDir",
            "ShipSpdToWater",
            "ShipSpdToGroud",
            "ShipDraughtBow",
            "ShipDraughtAstern",
            "ShipDraughtMidLft",
            "ShipDraughtMidRgt",
            "ShipHeel",
            "ShipTrim",
            "ShipDraft",
            "MERpm",
            "MEShaftPow",
            "slipRatio",
            "CII",
            "MESFOC_nmile",
            "Ship_nmile",
        ]
        df = pd.DataFrame(rows, columns=_COLS)
        df["PCTime"] = pd.to_datetime(df["PCTime"])

        # Outlier removal (5th–95th percentile on nmile consumption)
        vals = df["MESFOC_nmile"].dropna()
        if not vals.empty:
            lb, ub = np.percentile(vals, 5), np.percentile(vals, 95)
            df = df[df["MESFOC_nmile"].between(lb, ub)]
        if df.empty:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="no valid data after outlier removal")

        base_features = [
            "WindSpd",
            "WindDir",
            "ShipSpdToWater",
            "ShipSpdToGroud",
            "ShipDraughtBow",
            "ShipDraughtAstern",
            "ShipDraughtMidLft",
            "ShipDraughtMidRgt",
            "ShipHeel",
            "ShipTrim",
            "ShipDraft",
            "Ship_nmile",
            "MESFOC_nmile",
            "CII",
        ]
        power_features = ["MERpm", "MEShaftPow", "slipRatio"] if model_type == "all" else []
        all_features = base_features + power_features

        latest_date = df["PCTime"].max()
        latest_cii = df[df["PCTime"] == latest_date][["CII"]]
        mean_vals = df[all_features].mean()

        df_year = latest_cii.copy()
        for col in mean_vals.index:
            df_year[col] = mean_vals[col]

        base_speed = float(df_year["ShipSpdToWater"].iloc[0])
        base_consumption = float(df_year["MESFOC_nmile"].iloc[0])
        base_cii_val = float(df_year["CII"].iloc[0])

        year = end_date.year
        results = []
        percentages = [
            -0.25,
            -0.225,
            -0.20,
            -0.175,
            -0.15,
            -0.125,
            -0.10,
            -0.075,
            -0.05,
            -0.025,
            0.025,
            0.05,
            0.075,
            0.10,
            0.125,
            0.15,
            0.175,
            0.20,
            0.225,
            0.25,
        ]
        feat_cols = [c for c in all_features if c not in ("MESFOC_nmile", "Ship_nmile", "CII")]
        base_input = df_year[feat_cols].copy()

        for p in percentages:
            adj = base_speed * p
            df_temp = base_input.copy()
            df_temp["ShipSpdToWater"] = base_speed + adj
            df_temp["ShipSpdToGroud"] = df_year["ShipSpdToGroud"].iloc[0] + adj

            pred_consumption = float(model.predict(df_temp)[0])
            pred_cii = (
                base_cii_val * (pred_consumption / base_consumption) if base_consumption else 0.0
            )
            cii_rating = get_cii_rating(
                pred_cii, year, info.ship_type_code, info.dead_weight, info.gross_tone
            )
            results.append(
                {
                    "年均对水航速": round(base_speed + adj, 4),
                    "对水航速差值": round(adj, 4),
                    "年均主机每海里油耗": round(pred_consumption, 4),
                    "节省燃料": round(base_consumption - pred_consumption, 4),
                    "CII": round(pred_cii, 4),
                    "CII评级": cii_rating,
                    "选择的模型名称": selected_file,
                }
            )

        return results

    @staticmethod
    def optimize_ship_trim(
        vessel_id: int,
        start_date: date,
        end_date: date,
        models_dir: str,
    ) -> list[dict]:
        """Trim-optimisation via XGBoost model."""
        model_files = glob.glob(f"{models_dir}/{vessel_id}_trim_*.pkl")
        if not model_files:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=404,
                detail=(f"No trim model found for vessel {vessel_id} in {models_dir}."),
            )
        selected_file = sorted(model_files)[-1]
        with open(selected_file, "rb") as fh:
            model = pickle.load(fh)  # noqa: S301

        info = get_vessel_info(vessel_id)

        with get_duck_conn() as conn:
            rows = conn.execute(
                """
                SELECT date, trim, draft, speed_water,
                       me_fuel_consumption_nmile, cii
                FROM vessel_data_per_day
                WHERE vessel_id = $1 AND date BETWEEN $2 AND $3
                  AND trim IS NOT NULL
                ORDER BY date
                """,
                [vessel_id, start_date, end_date],
            ).fetchall()

        if not rows:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="no trim data for this vessel / date range")

        df = pd.DataFrame(
            rows,
            columns=["date", "trim", "draft", "speed_water", "me_fuel_consumption_nmile", "cii"],
        )
        base_trim = float(df["trim"].mean())
        base_nmile = float(df["me_fuel_consumption_nmile"].mean())
        base_cii = float(df["cii"].mean())
        year = end_date.year

        results = []
        for delta in [-2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0]:
            adj_trim = base_trim + delta
            try:
                pred_input = pd.DataFrame(
                    [
                        {
                            "trim": adj_trim,
                            "draft": df["draft"].mean(),
                            "speed_water": df["speed_water"].mean(),
                        }
                    ]
                )
                pred_nmile = float(model.predict(pred_input)[0])
            except Exception:
                pred_nmile = base_nmile

            pred_cii = base_cii * (pred_nmile / base_nmile) if base_nmile else 0.0
            cii_rating = get_cii_rating(
                pred_cii, year, info.ship_type_code, info.dead_weight, info.gross_tone
            )
            results.append(
                {
                    "平均吃水差": round(adj_trim, 2),
                    "吃水差调整值": round(delta, 2),
                    "年均主机每海里油耗": round(pred_nmile, 4),
                    "节省燃料": round(base_nmile - pred_nmile, 4),
                    "CII值": round(pred_cii, 4),
                    "CII评级": cii_rating,
                    "选择的模型名称": selected_file,
                }
            )

        return results
