"""IMO CII rating calculation functions.

Ported from backend/app/core/cii_rating.py.
Pure Python — no DB dependency.
"""

from __future__ import annotations


def _get_capacity_a_c(ship_type_code: str, dwt: float, gt: float) -> tuple[float, float, float]:
    """Return (capacity, a, c) for CII reference calculation."""
    capacity = dwt  # default
    a = 0.0
    c = 0.0

    if ship_type_code == "I001":
        capacity = min(dwt, 279000)
        a, c = 4745, 0.622
    elif ship_type_code == "I002":
        if dwt >= 65000:
            a, c = 14405e7, 2.071
        else:
            a, c = 8104, 0.639
        capacity = dwt
    elif ship_type_code == "I003":
        a, c = 5247, 0.610
    elif ship_type_code == "I004":
        a, c = 1984, 0.489
    elif ship_type_code == "I005":
        if dwt >= 20000:
            a, c = 31948, 0.792
        else:
            a, c = 588, 0.3885
    elif ship_type_code == "I006":
        a, c = 4600, 0.557
    elif ship_type_code == "I007":
        a, c = 5119, 0.622
    elif ship_type_code == "I008":
        if dwt >= 100000:
            a, c = 9.827, 0.000
        elif dwt >= 65000:
            a, c = 14479e10, 2.673
        else:
            capacity = 65000
            a, c = 14779e10, 2.673
    elif ship_type_code in ("I009", "I010", "I011", "I011.1", "I012"):
        # GT-based
        if ship_type_code == "I009":
            capacity = min(gt, 57700) if gt >= 30000 else gt
            a, c = 3627, 0.590
        elif ship_type_code == "I010":
            capacity = gt
            a, c = 1967, 0.485
        elif ship_type_code == "I011":
            capacity = gt
            a, c = 2023, 0.460
        elif ship_type_code == "I011.1":
            capacity = gt
            a, c = 4196, 0.460
        elif ship_type_code == "I012":
            capacity = gt
            a, c = 930, 0.383
    return capacity, a, c


def _get_z_percentage(year: int) -> float:
    """Return the annual efficiency ratio reduction factor for a given year."""
    table = {
        2019: 0.00,
        2020: 0.01,
        2021: 0.02,
        2022: 0.03,
        2023: 0.05,
        2024: 0.07,
        2025: 0.09,
        2026: 0.11,
        2027: 0.13625,
        2028: 0.16250,
        2029: 0.18875,
        2030: 0.21500,
    }
    return table.get(year, 0.0)


def get_required_cii(year: int, ship_type_code: str, dwt: float, gt: float) -> float:
    """Return the required CII for a vessel in a given year."""
    capacity, a, c = _get_capacity_a_c(ship_type_code, dwt, gt)
    if a == 0 or capacity == 0:
        return 0.0
    cii_reference = a * pow(capacity, -c)
    return cii_reference * (1 - _get_z_percentage(year))


def get_dd_vectors(ship_type_code: str, dwt: float) -> tuple[float, float, float, float]:
    """Return (superior, lower, upper, inferior) dd boundary multipliers."""
    # Defaults
    d1, d2, d3, d4 = 0.86, 0.94, 1.06, 1.18

    if ship_type_code == "I001":
        d1, d2, d3, d4 = 0.86, 0.94, 1.06, 1.18
    elif ship_type_code == "I002":
        if dwt >= 65000:
            d1, d2, d3, d4 = 0.81, 0.91, 1.12, 1.44
        else:
            d1, d2, d3, d4 = 0.85, 0.95, 1.06, 1.25
    elif ship_type_code == "I003":
        d1, d2, d3, d4 = 0.82, 0.93, 1.08, 1.28
    elif ship_type_code == "I004":
        d1, d2, d3, d4 = 0.83, 0.94, 1.07, 1.19
    elif ship_type_code == "I005":
        d1, d2, d3, d4 = 0.83, 0.94, 1.06, 1.19
    elif ship_type_code == "I006":
        d1, d2, d3, d4 = 0.78, 0.91, 1.07, 1.20
    elif ship_type_code == "I007":
        d1, d2, d3, d4 = 0.87, 0.96, 1.06, 1.14
    elif ship_type_code == "I008":
        if dwt >= 100000:
            d1, d2, d3, d4 = 0.89, 0.98, 1.06, 1.13
        else:
            d1, d2, d3, d4 = 0.78, 0.92, 1.10, 1.37
    elif ship_type_code == "I009":
        d1, d2, d3, d4 = 0.86, 0.94, 1.06, 1.16
    elif ship_type_code == "I010":
        d1, d2, d3, d4 = 0.76, 0.89, 1.08, 1.27
    elif ship_type_code in ("I011", "I011.1"):
        d1, d2, d3, d4 = 0.76, 0.92, 1.14, 1.30
    elif ship_type_code == "I012":
        d1, d2, d3, d4 = 0.87, 0.95, 1.06, 1.16

    return d1, d2, d3, d4


def get_cii_rating(cii: float, year: int, ship_type_code: str, dwt: float, gt: float) -> str:
    """Return A/B/C/D/E rating for a given CII value."""
    required = get_required_cii(year, ship_type_code, dwt, gt)
    if required <= 0:
        return "N/A"
    d1, d2, d3, d4 = get_dd_vectors(ship_type_code, dwt)
    superior = required * d1
    lower = required * d2
    upper = required * d3
    inferior = required * d4

    if cii <= superior:
        return "A"
    if cii <= lower:
        return "B"
    if cii <= upper:
        return "C"
    if cii <= inferior:
        return "D"
    return "E"


def get_cii_boundaries(year: int, ship_type_code: str, dwt: float, gt: float) -> dict[str, float]:
    """Return {superior, lower, upper, inferior} boundary values."""
    required = get_required_cii(year, ship_type_code, dwt, gt)
    d1, d2, d3, d4 = get_dd_vectors(ship_type_code, dwt)
    return {
        "superior": required * d1,
        "lower": required * d2,
        "upper": required * d3,
        "inferior": required * d4,
    }
