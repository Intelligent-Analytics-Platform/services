"""HTTP clients for downstream services (vessel, meta).

Uses httpx for synchronous calls. Ship-type map is cached in-process
since meta data rarely changes.
"""

from __future__ import annotations

import logging

import httpx
from fastapi import HTTPException

from analytics.config import settings

logger = logging.getLogger(__name__)

# ── Vessel client ────────────────────────────────────────────────────────────


def get_vessel(vessel_id: int) -> dict:
    """Fetch vessel details from the vessel service."""
    try:
        resp = httpx.get(
            f"{settings.vessel_service_url}/vessel/{vessel_id}",
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()["data"]
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"vessel {vessel_id} not found") from exc
        raise HTTPException(status_code=502, detail="vessel service error") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail="vessel service unavailable") from exc


# ── Meta client ──────────────────────────────────────────────────────────────

_ship_type_cache: dict[int, str] | None = None


def get_ship_type_map() -> dict[int, str]:
    """Return {ship_type_id → code}.  Cached for the process lifetime."""
    global _ship_type_cache  # noqa: PLW0603
    if _ship_type_cache is not None:
        return _ship_type_cache
    try:
        resp = httpx.get(f"{settings.meta_service_url}/meta/ship_type", timeout=10)
        resp.raise_for_status()
        _ship_type_cache = {t["id"]: t["code"] for t in resp.json()["data"]}
        return _ship_type_cache
    except Exception as exc:
        logger.warning("Cannot reach meta service: %s — using fallback ship_type map", exc)
        return {}


# ── Combined vessel info ─────────────────────────────────────────────────────


class VesselInfo:
    """Vessel fields needed by the analytics service."""

    def __init__(
        self,
        vessel_id: int,
        dead_weight: float,
        gross_tone: float,
        ship_type_code: str,
        pitch: float,
    ):
        self.vessel_id = vessel_id
        self.dead_weight = dead_weight
        self.gross_tone = gross_tone
        self.ship_type_code = ship_type_code
        self.pitch = pitch


def get_vessel_info(vessel_id: int) -> VesselInfo:
    """Fetch vessel details and resolve ship_type → code."""
    vessel = get_vessel(vessel_id)
    ship_type_map = get_ship_type_map()
    ship_type_code = ship_type_map.get(vessel["ship_type"], "I001")
    return VesselInfo(
        vessel_id=vessel_id,
        dead_weight=vessel["dead_weight"],
        gross_tone=vessel["gross_tone"],
        ship_type_code=ship_type_code,
        pitch=vessel.get("pitch", 6.058),
    )
