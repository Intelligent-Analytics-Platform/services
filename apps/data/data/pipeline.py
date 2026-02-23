"""Data cleaning pipeline for vessel CSV uploads.

Ported from backend/app/core/data_utils.py.
"""

import pandas as pd


# ── CO2 emission factor ──────────────────────────────────────────────────────


def get_cf(fuel_col_name: str) -> float:
    """Return CO2 emission factor (CF) for a fuel column name.

    Based on IMO guidelines for CII calculation.
    Returns 0.0 if the fuel type is not recognized.
    """
    name = fuel_col_name.lower()
    if "hfo" in name:
        return 3.114
    if "lfo" in name:
        return 3.151
    if "mgo" in name or "mdo" in name:
        return 3.206
    if "lng" in name:
        return 2.75
    if "lpg_p" in name:
        return 3.0
    if "lpg_b" in name:
        return 3.03
    if "methanol" in name:
        return 1.375
    if "ethanol" in name:
        return 1.913
    if "ethane" in name:
        return 2.927
    return 0.0


# ── Derived field calculations ───────────────────────────────────────────────


def draft_calculation(df: pd.DataFrame) -> None:
    """Calculate average draft from bow and stern drafts (in-place).

    If draft columns are absent (minimal test DataFrames), draft defaults to 0.
    """
    for col in ("draught_astern", "draught_bow"):
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["draft"] = 0.5 * (df["draught_astern"].fillna(0) + df["draught_bow"].fillna(0))


def slip_ratio_calculation(df: pd.DataFrame, pitch: float = 6.058) -> None:
    """Calculate propeller slip ratio (in-place).

    slip_ratio = (1 - speed_water / (rpm * pitch * 60) * 1852) * 100
    """
    for col in ("me_rpm", "speed_water"):
        if col not in df.columns:
            df[col] = 0.0
    df["me_rpm"] = pd.to_numeric(df["me_rpm"], errors="coerce")
    df["speed_water"] = pd.to_numeric(df["speed_water"], errors="coerce")

    valid = (df["me_rpm"] != 0) & (df["speed_water"] != 0) & df["me_rpm"].notna() & df["speed_water"].notna()
    df["slip_ratio"] = 0.0
    df.loc[valid, "slip_ratio"] = (
        1 - (df.loc[valid, "speed_water"] / (df.loc[valid, "me_rpm"] * pitch * 60)) * 1852
    ) * 100


def ship_nmile_calculation(df: pd.DataFrame) -> None:
    """Calculate fuel consumption per nautical mile (in-place)."""
    for col in ["me_hfo_act_cons", "dg_hfo_act_cons", "blr_hfo_act_cons", "speed_water"]:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce")

    valid = (df["speed_water"] != 0) & df["speed_water"].notna()
    df["ship_nmile"] = 0.0
    if valid.any():
        df.loc[valid, "ship_nmile"] = (
            df.loc[valid, "me_hfo_act_cons"].fillna(0)
            + df.loc[valid, "dg_hfo_act_cons"].fillna(0)
            + df.loc[valid, "blr_hfo_act_cons"].fillna(0)
        ) / df.loc[valid, "speed_water"]


# ── Filtering steps ──────────────────────────────────────────────────────────


def data_nulls(df: pd.DataFrame) -> pd.DataFrame:
    """Remove rows with any null value."""
    return df.dropna()


def _filter_col(df: pd.DataFrame, col: str, cond) -> pd.DataFrame:
    """Apply a filter condition only if the column exists."""
    return df[cond(df[col])] if col in df.columns else df


def data_abnormal_removal(df: pd.DataFrame) -> pd.DataFrame:
    """Remove rows with physically impossible sensor values."""
    df = _filter_col(df, "me_fuel_consumption_nmile", lambda c: (c > 0) & (c < 250))
    df = _filter_col(df, "me_shaft_power", lambda c: (c > 0) & (c < 8000))
    df = _filter_col(df, "me_rpm", lambda c: (c < 2000) & (c != 0))
    df = _filter_col(df, "draft", lambda c: c > 0)
    df = _filter_col(df, "speed_ground", lambda c: (c != 88888) & (c >= 3))
    df = _filter_col(df, "speed_water", lambda c: c != 88888)
    df = _filter_col(df, "slip_ratio", lambda c: c != 88888)
    df = _filter_col(df, "wind_direction", lambda c: c != 88888)
    df = _filter_col(df, "wind_speed", lambda c: c < 60)
    df = _filter_col(df, "me_fuel_consumption_kwh", lambda c: c >= 0)
    # Remove rows that contain embedded newlines (data corruption indicator)
    mask = df.apply(lambda row: any("\n" in str(cell) for cell in row), axis=1)
    return df[~mask]


def data_filtering(df: pd.DataFrame) -> pd.DataFrame:
    """Apply operational filtering criteria."""
    df = df[df["me_rpm"] >= 35]
    df = df[df["speed_water"] >= 3]
    df = df[(df["slip_ratio"] <= 100.0) & (df["slip_ratio"] >= -20.0)]
    return df


# ── Main entry point ─────────────────────────────────────────────────────────

_NUMERIC_COLS = [
    "speed_water",
    "me_rpm",
    "me_hfo_act_cons",
    "dg_hfo_act_cons",
    "blr_hfo_act_cons",
    "draught_astern",
    "draught_bow",
    "wind_speed",
    "me_fuel_consumption_nmile",
    "me_fuel_consumption_kwh",
    "me_shaft_power",
]


def data_preparation(df: pd.DataFrame, pitch: float = 6.058) -> pd.DataFrame:
    """Full cleaning pipeline: null removal → type coercion → derived fields → filtering.

    Args:
        df: Raw DataFrame from CSV upload.
        pitch: Propeller pitch for slip ratio calculation.

    Returns:
        Cleaned DataFrame (may be empty if no rows pass all filters).
    """
    df = data_nulls(df)

    for col in _NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    draft_calculation(df)
    slip_ratio_calculation(df, pitch)
    ship_nmile_calculation(df)

    df = data_abnormal_removal(df)
    if df.empty:
        return df

    df = data_filtering(df)
    return df
