from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import math
import random
import csv
import os


@dataclass
class SimConfig:
    # Time grid
    seed: int = 123
    freq_minutes: int = 60     # 60 = hourly
    n_days: int = 60

    # X4: structural building factor (baseline shifter)
    building_factor_x4: float = 1.10  # >1 = more demanding building

    # Baseline consumption (kWh per interval)
    base_kwh_when_closed: float = 8.0
    base_kwh_when_open: float = 18.0

    # How signals translate into activation (M1)
    occ_to_activation: float = 0.020
    temp_to_activation: float = 0.060
    regime_to_activation: float = 0.35

    # How activation/pressure translate into kWh
    activation_to_kwh: float = 35.0
    direct_temp_to_kwh: float = 0.50

    # X6: inertia (memory)
    inertia_phi: float = 0.75  # 0=no memory, 1=full memory

    # Noise
    noise_sigma: float = 2.5

    # C1 proxy: academic intensity (confounder driver of occupancy + regimes)
    academic_intensity: float = 1.0  # 0.6 vacation, 1.0 normal, 1.2 exams


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def generate_time_index(start: datetime, n_steps: int, step_minutes: int) -> List[datetime]:
    return [start + timedelta(minutes=step_minutes) * i for i in range(n_steps)]


def simulate_outdoor_temp(ts: datetime, seasonal_amp: float = 9.0, daily_amp: float = 3.5) -> float:
    """
    X2 proxy generator (temperature): seasonality + daily cycle.
    """
    day_of_year = ts.timetuple().tm_yday
    hour = ts.hour + ts.minute / 60.0

    # seasonal around ~8C
    seasonal = 8.0 + seasonal_amp * math.sin(2 * math.pi * (day_of_year / 365.0))

    # daily cycle: coolest ~05:00, warmest ~15:00
    daily = daily_amp * math.sin(2 * math.pi * ((hour - 5.0) / 24.0))

    return seasonal + daily


def simulate_open_regime(ts: datetime) -> int:
    """
    X3 proxy: open/closed regime.
    Weekdays 08:00–22:00, weekends 10:00–18:00.
    """
    weekday = ts.weekday()  # 0=Mon ... 6=Sun
    hour = ts.hour + ts.minute / 60.0

    if weekday <= 4:
        return 1 if (8.0 <= hour < 22.0) else 0
    return 1 if (10.0 <= hour < 18.0) else 0


def simulate_occupancy(ts: datetime, open_regime: int, academic_intensity: float, rng: random.Random) -> float:
    """
    X1 proxy: occupancy intensity (0..~220).
    Daily peaks around midday and late afternoon, plus noise.
    """
    if open_regime == 0:
        return 0.0

    hour = ts.hour + ts.minute / 60.0
    weekday = ts.weekday()

    daily_profile = (
        0.6 * math.exp(-((hour - 13.0) ** 2) / (2 * 3.5 ** 2)) +
        0.4 * math.exp(-((hour - 18.0) ** 2) / (2 * 2.8 ** 2))
    )

    weekday_multiplier = 1.0 if weekday <= 4 else 0.65
    base_capacity = 180.0 * academic_intensity

    noise = rng.normalvariate(0.0, 8.0)
    occ = base_capacity * daily_profile * weekday_multiplier + noise

    return clamp(occ, 0.0, 220.0)


def temp_pressure(temp_out: float, comfort_low: float = 20.0, comfort_high: float = 23.0) -> float:
    """
    Convert outside temperature into a 'pressure' signal:
    distance from comfort range.
    """
    if temp_out < comfort_low:
        return comfort_low - temp_out
    if temp_out > comfort_high:
        return temp_out - comfort_high
    return 0.0


def simulate(cfg: SimConfig, start: Optional[datetime] = None) -> List[Dict[str, float]]:
    """
    Mechanism-based simulation consistent with the CLARO DAG:
      C1 -> X1, X3
      X1, X2, X3, X5 -> M1
      M1, X2, X3, X4, X6 -> Y
    """
    rng = random.Random(cfg.seed)
    if start is None:
        start = datetime(2025, 1, 1, 0, 0, 0)

    steps_per_day = int((24 * 60) / cfg.freq_minutes)
    n_steps = cfg.n_days * steps_per_day
    times = generate_time_index(start, n_steps, cfg.freq_minutes)

    rows: List[Dict[str, float]] = []
    y_prev = cfg.base_kwh_when_closed

    for ts in times:
        # X3: regime
        x3_open = simulate_open_regime(ts)

        # X2: environment
        x2_temp_out = simulate_outdoor_temp(ts)
        x2_pressure = temp_pressure(x2_temp_out)

        # X1: human use (driven by C1 proxy)
        x1_occ = simulate_occupancy(ts, x3_open, cfg.academic_intensity, rng)

        # X5 (conceptual): here represented as an "availability" factor
        # driven by X3 and shifted by X4.
        x5_availability = (0.7 + 0.3 * x3_open) * cfg.building_factor_x4

        # M1: activation (mediator)
        m1_activation = (
            cfg.regime_to_activation * x3_open +
            cfg.occ_to_activation * x1_occ +
            cfg.temp_to_activation * x2_pressure
        ) * x5_availability
        m1_activation = clamp(m1_activation, 0.0, 2.0)

        # Deterministic demand before inertia/noise
        baseline = cfg.base_kwh_when_open if x3_open == 1 else cfg.base_kwh_when_closed
        baseline *= cfg.building_factor_x4  # X4 baseline shift

        y_det = baseline + cfg.activation_to_kwh * m1_activation + cfg.direct_temp_to_kwh * x2_pressure

        # X6: inertia (memory) + noise
        noise = rng.normalvariate(0.0, cfg.noise_sigma)
        y_kwh = cfg.inertia_phi * y_prev + (1.0 - cfg.inertia_phi) * y_det + noise
        y_kwh = max(0.0, y_kwh)

        rows.append({
            "timestamp": ts.isoformat(),
            "X1_occupancy": round(x1_occ, 3),
            "X2_temp_out": round(x2_temp_out, 3),
            "X2_temp_pressure": round(x2_pressure, 3),
            "X3_open": float(x3_open),
            "X4_building_factor": round(cfg.building_factor_x4, 3),
            "X5_availability": round(x5_availability, 3),
            "M1_activation": round(m1_activation, 4),
            "Y_kwh": round(y_kwh, 4),
        })

        y_prev = y_kwh

    return rows


def write_csv(rows: List[Dict[str, float]], out_path: str) -> None:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
