from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class TrainingConfig:
    sample_size: int = 3000
    random_seed: int = 42


def generate_synthetic_clinic_data(config: TrainingConfig | None = None) -> pd.DataFrame:
    cfg = config or TrainingConfig()
    rng = np.random.default_rng(cfg.random_seed)

    day_of_week = rng.integers(0, 7, cfg.sample_size)
    hour = rng.integers(8, 21, cfg.sample_size)
    doctor_count = rng.integers(1, 9, cfg.sample_size)
    scheduled_appointments = rng.integers(5, 60, cfg.sample_size)
    walk_in_patients = rng.integers(0, 35, cfg.sample_size)
    avg_consultation_minutes = rng.uniform(7, 30, cfg.sample_size)
    is_holiday = rng.binomial(1, 0.08, cfg.sample_size)
    rain_intensity = rng.uniform(0, 1, cfg.sample_size)

    peak_hour_boost = np.where((hour >= 10) & (hour <= 13), 8, 0) + np.where((hour >= 17) & (hour <= 19), 6, 0)
    weekend_boost = np.where(day_of_week >= 5, 5, 0)

    actual_load = (
        0.55 * scheduled_appointments
        + 0.95 * walk_in_patients
        + 0.35 * avg_consultation_minutes
        - 1.8 * doctor_count
        + 4.0 * is_holiday
        + 7.5 * rain_intensity
        + peak_hour_boost
        + weekend_boost
        + rng.normal(0, 3.5, cfg.sample_size)
    )

    actual_load = np.clip(actual_load, 1, None)

    return pd.DataFrame(
        {
            "day_of_week": day_of_week,
            "hour": hour,
            "doctor_count": doctor_count,
            "scheduled_appointments": scheduled_appointments,
            "walk_in_patients": walk_in_patients,
            "avg_consultation_minutes": avg_consultation_minutes,
            "is_holiday": is_holiday,
            "rain_intensity": rain_intensity,
            "actual_load": actual_load,
        }
    )
