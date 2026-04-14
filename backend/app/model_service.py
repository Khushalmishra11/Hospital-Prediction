from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

from .training import generate_synthetic_clinic_data


BASE_DIR = Path(__file__).resolve().parents[1]
MODEL_DIR = BASE_DIR / "model"
MODEL_PATH = MODEL_DIR / "load_predictor.joblib"


class ModelNotTrainedError(Exception):
    pass


class LoadPredictorService:
    feature_columns = [
        "day_of_week",
        "hour",
        "doctor_count",
        "scheduled_appointments",
        "walk_in_patients",
        "avg_consultation_minutes",
        "is_holiday",
        "rain_intensity",
    ]

    def __init__(self) -> None:
        self._model_bundle: dict[str, Any] | None = None

    def train_and_save(self, training_data: pd.DataFrame | None = None) -> dict[str, float | int | str]:
        data = training_data if training_data is not None else generate_synthetic_clinic_data()

        x = data[self.feature_columns]
        y = data["actual_load"]

        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)

        model = RandomForestRegressor(
            n_estimators=300,
            max_depth=12,
            min_samples_split=6,
            random_state=42,
            n_jobs=-1,
        )
        model.fit(x_train, y_train)

        y_pred = model.predict(x_test)
        metrics = {
            "r2_score": float(r2_score(y_test, y_pred)),
            "mae": float(mean_absolute_error(y_test, y_pred)),
            "samples": int(len(data)),
        }

        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        bundle = {
            "model": model,
            "feature_columns": self.feature_columns,
            "metrics": metrics,
        }
        joblib.dump(bundle, MODEL_PATH)
        self._model_bundle = bundle

        return {
            "status": "trained",
            **metrics,
        }

    def _ensure_model_loaded(self) -> None:
        if self._model_bundle is not None:
            return
        if not MODEL_PATH.exists():
            raise ModelNotTrainedError("No model artifact found. Train the model first.")
        self._model_bundle = joblib.load(MODEL_PATH)

    def predict_load(self, features: dict[str, Any]) -> float:
        self._ensure_model_loaded()
        if self._model_bundle is None:
            raise ModelNotTrainedError("Model could not be loaded.")

        model = self._model_bundle["model"]
        row = pd.DataFrame([{col: features[col] for col in self.feature_columns}])
        prediction = float(model.predict(row)[0])
        return max(prediction, 0.0)

    @staticmethod
    def estimate_wait_minutes(predicted_load: float, doctor_count: int, avg_consultation_minutes: float) -> float:
        service_capacity = max(doctor_count, 1) * (60.0 / max(avg_consultation_minutes, 1.0))
        utilization = predicted_load / max(service_capacity, 0.1)

        if utilization <= 1.0:
            wait = utilization * 12.0
        else:
            wait = 12.0 + ((utilization - 1.0) * 35.0)

        return round(float(max(wait, 1.0)), 2)

    @staticmethod
    def risk_level(predicted_load: float) -> str:
        if predicted_load < 20:
            return "LOW"
        if predicted_load < 40:
            return "MEDIUM"
        return "HIGH"
