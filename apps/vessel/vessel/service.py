"""Business logic for the vessel service."""

import json
from urllib.request import urlopen

from common.exceptions import EntityNotFoundError
from sqlalchemy.orm import Session

from vessel.config import settings
from vessel.models import CurveData, Equipment, EquipmentFuel, PowerSpeedCurve, Vessel
from vessel.repository import VesselRepository
from vessel.schemas import (
    CurveDataSchema,
    EquipmentCreate,
    EquipmentSchema,
    PowerSpeedCurveCreate,
    PowerSpeedCurveSchema,
    VesselCreate,
    VesselSchema,
    VesselUpdate,
)


class VesselService:
    def __init__(self, repo: VesselRepository):
        self.repo = repo

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _get_analytics_metrics(self, vessel_id: int) -> dict:
        """Fetch old-style analytics fields from analytics service with safe fallbacks."""
        metrics = {
            "speed_water": 0.0,
            "me_fuel_consumption_nmile": 0.0,
            "latest_cii": 0.0,
            "cii_rating": "N/A",
        }

        # Average speed and nmile consumption
        try:
            avg_url = f"{settings.analytics_service_url}/optimization/vessel/{vessel_id}/average"
            with urlopen(avg_url, timeout=settings.analytics_timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
                data = payload.get("data") or {}
                metrics["speed_water"] = float(data.get("speed_water") or 0.0)
                metrics["me_fuel_consumption_nmile"] = float(
                    data.get("me_fuel_consumption_nmile") or 0.0
                )
        except Exception:
            pass

        # Latest CII and rating
        try:
            cii_url = f"{settings.analytics_service_url}/statistic/vessel/{vessel_id}/cii"
            with urlopen(cii_url, timeout=settings.analytics_timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
                items = payload.get("data") or []
                if items:
                    latest = items[-1]
                    metrics["latest_cii"] = float(latest.get("cii") or 0.0)
                    metrics["cii_rating"] = latest.get("rating") or "N/A"
        except Exception:
            pass

        return metrics

    def _build_schema(self, vessel: Vessel) -> VesselSchema:
        """Assemble VesselSchema from ORM relationships."""
        equipments = [
            EquipmentSchema(
                name=e.name,
                type=e.type,
                fuel_type_ids=[ef.fuel_type_id for ef in e.fuel_entries],
            )
            for e in vessel.equipments
        ]
        curves = [
            PowerSpeedCurveSchema(
                id=c.id,
                curve_name=c.curve_name,
                draft_astern=c.draft_astern,
                draft_bow=c.draft_bow,
                curve_data=[CurveDataSchema.model_validate(cd) for cd in c.curve_data],
            )
            for c in vessel.curves
        ]
        metrics = self._get_analytics_metrics(vessel.id)

        return VesselSchema(
            id=vessel.id,
            name=vessel.name,
            mmsi=vessel.mmsi,
            ship_type=vessel.ship_type,
            build_date=vessel.build_date,
            gross_tone=vessel.gross_tone,
            dead_weight=vessel.dead_weight,
            new_vessel=vessel.new_vessel,
            pitch=vessel.pitch,
            hull_clean_date=vessel.hull_clean_date,
            engine_overhaul_date=vessel.engine_overhaul_date,
            newly_paint_date=vessel.newly_paint_date,
            propeller_polish_date=vessel.propeller_polish_date,
            time_zone=vessel.time_zone,
            company_id=vessel.company_id,
            created_at=vessel.created_at,
            equipments=equipments,
            curves=curves,
            # Old response aliases
            equipment_fuel=equipments,
            power_speed_curve=curves,
            speed_water=metrics["speed_water"],
            me_fuel_consumption_nmile=metrics["me_fuel_consumption_nmile"],
            latest_cii=metrics["latest_cii"],
            cii_rating=metrics["cii_rating"],
            engine_state="Good",
            hull_propeller_state="Anomaly",
        )

    def _create_equipments(
        self, session: Session, vessel_id: int, items: list[EquipmentCreate]
    ) -> None:
        for eq_data in items:
            eq = Equipment(name=eq_data.name, type=eq_data.type, vessel_id=vessel_id)
            session.add(eq)
            session.flush()
            for fuel_id in eq_data.fuel_type_ids:
                session.add(EquipmentFuel(equipment_id=eq.id, fuel_type_id=fuel_id))

    def _create_curves(
        self, session: Session, vessel_id: int, items: list[PowerSpeedCurveCreate]
    ) -> None:
        for curve_data in items:
            curve = PowerSpeedCurve(
                curve_name=curve_data.curve_name,
                draft_astern=curve_data.draft_astern,
                draft_bow=curve_data.draft_bow,
                vessel_id=vessel_id,
            )
            session.add(curve)
            session.flush()
            for cd in curve_data.curve_data:
                # Append to the ORM collection so the in-memory state stays consistent
                curve.curve_data.append(
                    CurveData(
                        speed_water=cd.speed_water,
                        me_power=cd.me_power,
                        power_speed_curve_id=curve.id,
                    )
                )

    # ── CRUD ───────────────────────────────────────────────────────────────────

    def get_vessel_list(
        self,
        name: str | None = None,
        company_id: int | None = None,
        offset: int = 0,
        limit: int = 10,
    ) -> list[VesselSchema]:
        vessels = self.repo.list_vessels(name, company_id, offset, limit)
        return [self._build_schema(v) for v in vessels]

    def get_vessel_by_id(self, vessel_id: int) -> VesselSchema:
        vessel = self.repo.get_or_raise(vessel_id)
        return self._build_schema(vessel)

    def create_vessel(self, data: VesselCreate) -> VesselSchema:
        vessel = Vessel(**data.model_dump(exclude={"equipments", "curves"}))
        self.repo.session.add(vessel)
        self.repo.session.flush()

        self._create_equipments(self.repo.session, vessel.id, data.equipments)
        self._create_curves(self.repo.session, vessel.id, data.curves)

        self.repo.session.flush()  # assign IDs to all pending objects
        self.repo.session.refresh(vessel)
        return self._build_schema(vessel)

    def update_vessel(self, vessel_id: int, data: VesselUpdate) -> VesselSchema:
        vessel = self.repo.get_or_raise(vessel_id)

        # Update scalar fields
        base_fields = data.model_dump(exclude={"equipments", "curves"}, exclude_unset=True)
        for key, value in base_fields.items():
            setattr(vessel, key, value)

        # Replace equipment and curves
        vessel.equipments.clear()
        vessel.curves.clear()
        self.repo.session.flush()

        self._create_equipments(self.repo.session, vessel.id, data.equipments)
        self._create_curves(self.repo.session, vessel.id, data.curves)

        self.repo.session.refresh(vessel)
        return self._build_schema(vessel)

    def delete_vessel(self, vessel_id: int) -> None:
        vessel = self.repo.get_or_raise(vessel_id)
        self.repo.session.delete(vessel)
        if not vessel:
            raise EntityNotFoundError("Vessel", vessel_id)
