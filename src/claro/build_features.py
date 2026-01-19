from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import pandas as pd


@dataclass
class FeatureConfig:
    freq: str = "1H"
    tz: Optional[str] = None
    comfort_low: float = 20.0
    comfort_high: float = 23.0
    add_y_lags: bool = True
    y_lags: tuple[int, ...] = (1, 24)  # for hourly data


def _ensure_datetime_index(df: pd.DataFrame, ts_col: str, tz: Optional[str]) -> pd.DataFrame:
    df = df.copy()
    df[ts_col] = pd.to_datetime(df[ts_col], errors="coerce")
    if df[ts_col].isna().any():
        bad = df[df[ts_col].isna()]
        raise ValueError(f"Unparseable timestamps found in column '{ts_col}'. Example rows:\n{bad.head()}")
    df = df.set_index(ts_col).sort_index()

    if tz:
        if df.index.tz is None:
            df.index = df.index.tz_localize(tz)
        else:
            df.index = df.index.tz_convert(tz)

    return df


def _temp_pressure(temp_out: pd.Series, low: float, high: float) -> pd.Series:
    below = (low - temp_out).clip(lower=0)
    above = (temp_out - high).clip(lower=0)
    return below + above


def build_from_simulated(path_in: str, path_out: str, cfg: FeatureConfig = FeatureConfig()) -> pd.DataFrame:
    """
    Convert the simulated CLARO dataset into a model-ready analytical table.
    This mirrors the steps that will be applied to real inputs later.
    """
    df = pd.read_csv(path_in)
    df = _ensure_datetime_index(df, ts_col="timestamp", tz=cfg.tz)

    # Standardize names for the model-ready table
    out = pd.DataFrame(index=df.index)
    out["Y_kwh"] = df["Y_kwh"]
    out["X1_occupancy_proxy"] = df["X1_occupancy"]
    out["X2_temp_out"] = df["X2_temp_out"]
    out["X2_temp_pressure"] = _temp_pressure(out["X2_temp_out"], cfg.comfort_low, cfg.comfort_high)
    out["X3_open"] = df["X3_open"].astype(int)

    # Resample to target frequency (if needed)
    # Note: This assumes Y_kwh is already "per interval".
    out = out.resample(cfg.freq).mean()

    # Add lags (X6 proxy)
    if cfg.add_y_lags:
        for lag in cfg.y_lags:
            out[f"Y_lag_{lag}"] = out["Y_kwh"].shift(lag)

    out = out.dropna()
    out.to_csv(path_out, index=True)
    return out

