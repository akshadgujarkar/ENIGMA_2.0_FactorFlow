from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.neighbors import KNeighborsRegressor
from xgboost import XGBRegressor

from ..config import Config
from ..routes.cities import SUPPORTED_CITIES
from .gee_client import get_city_realtime_indices


class UnknownCityError(ValueError):
  pass


def _models_dir() -> Path:
  cfg = Config()
  path = Path(cfg.MODELS_DIR)
  path.mkdir(parents=True, exist_ok=True)
  return path


def _model_paths(city_id: str) -> dict[str, Path]:
  base = _models_dir() / city_id
  base.mkdir(parents=True, exist_ok=True)
  return {
    "xgboost": base / "xgboost.pkl",
    "rf_classifier": base / "rf_classifier.pkl",
    "rf_regressor": base / "rf_regressor.pkl",
    "cnn": base / "cnn_placeholder.pkl",
    "knn": base / "knn.pkl",
    "linear": base / "linear.pkl",
  }


def _ensure_city(city_id: str) -> None:
  if not any(c["id"] == city_id for c in SUPPORTED_CITIES):
    raise UnknownCityError(city_id)


def retrain_models_for_city(city_id: str) -> dict[str, Any]:
  """Train or retrain all models for a city.

  In this scaffold implementation we simulate a small synthetic dataset that
  mimics features derived from GEE time-series, so the pipeline is end-to-end
  testable. In production you would replace the synthetic generation with
  proper feature extraction from GEE and/or Firebase.
  """
  _ensure_city(city_id)

  rng = np.random.default_rng(seed=42)
  n_samples = 500

  # Synthetic feature matrix: [ndvi, ndbi, ndwi, lst_c, flood_index]
  X = rng.normal(size=(n_samples, 5))

  # Continuous targets
  y_heat = 50 + 20 * X[:, 3] - 10 * X[:, 0]  # heat stress
  y_green = 50 + 25 * X[:, 0] - 10 * X[:, 1]  # green cover %

  # Classification target for flood risk (0/1)
  flood_prob = 1 / (1 + np.exp(-3 * (X[:, 4] - 0.2)))
  y_flood_class = (rng.random(n_samples) < flood_prob).astype(int)

  paths = _model_paths(city_id)

  # 1. XGBoost (for urban sprawl / projections)
  xgb = XGBRegressor(
    n_estimators=150,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.8,
    objective="reg:squarederror",
  )
  xgb.fit(X, y_heat)
  joblib.dump(xgb, paths["xgboost"])

  # 2. Random Forest Classifier (flood risk classification)
  rf_clf = RandomForestClassifier(n_estimators=200, max_depth=6)
  rf_clf.fit(X, y_flood_class)
  joblib.dump(rf_clf, paths["rf_classifier"])

  # 3. Random Forest Regressor (LST / green cover prediction)
  rf_reg = RandomForestRegressor(n_estimators=200, max_depth=8)
  rf_reg.fit(X, y_green)
  joblib.dump(rf_reg, paths["rf_regressor"])

  # 4. CNN placeholder (image-based model). For now, store a stub.
  joblib.dump({"info": "cnn-placeholder"}, paths["cnn"])

  # 5. KNN baseline
  knn = KNeighborsRegressor(n_neighbors=5)
  knn.fit(X, y_heat)
  joblib.dump(knn, paths["knn"])

  # 6. Linear Regression baseline (interpretability)
  lin = LinearRegression()
  lin.fit(X, y_heat)
  joblib.dump(lin, paths["linear"])

  return {
    "city": city_id,
    "status": "retrained",
    "models": {name: str(path) for name, path in paths.items()},
  }


def _load_models(city_id: str) -> dict[str, Any]:
  _ensure_city(city_id)
  paths = _model_paths(city_id)

  # If models do not exist yet, train them quickly
  if not paths["xgboost"].exists():
    retrain_models_for_city(city_id)

  return {name: joblib.load(path) for name, path in paths.items()}


def run_scenario_simulation(city_id: str, config: dict[str, Any]) -> dict[str, Any]:
  """Run all core what-if scenarios and return updated metrics.

  This focuses on:
    - Scenario 1: green cover increase
    - Scenario 2: flash flood event
    - Scenario 3: urban sprawl projection
    - Scenario 4: combined
  """
  _ensure_city(city_id)
  models = _load_models(city_id)

  base = get_city_realtime_indices(city_id)
  metrics = base["metrics"]

  green_increase = float(config.get("green_increase", 0))
  flood_event = bool(config.get("flood_event", False))
  flood_intensity = str(config.get("flood_intensity", "none"))
  sprawl_horizon = int(config.get("sprawl_horizon", 2030))

  # Build feature vector from baseline metrics (scaled roughly to 0–1)
  ndvi = base["ndvi_mean"]
  ndbi = base["ndbi_mean"]
  lst_c = base["lst_mean_c"]
  flood_index = base["flood_index_mean"]
  ndwi = max(-1.0, min(1.0, 1.0 - ndbi))  # rough proxy

  X = np.array([[ndvi, ndbi, ndwi, lst_c, flood_index]], dtype=float)

  xgb: XGBRegressor = models["xgboost"]
  rf_clf: RandomForestClassifier = models["rf_classifier"]
  rf_reg: RandomForestRegressor = models["rf_regressor"]
  lin: LinearRegression = models["linear"]

  # Base predictions (no scenario)
  heat_pred_base = float(lin.predict(X)[0])
  green_pred_base = float(rf_reg.predict(X)[0])
  flood_prob_base = float(rf_clf.predict_proba(X)[0, 1])

  # Scenario 1: green cover change → update NDVI feature and re-run regressors
  ndvi_scenario = ndvi + green_increase / 100.0
  X_green = np.array([[ndvi_scenario, ndbi, ndwi, lst_c, flood_index]], dtype=float)
  heat_after_green = float(lin.predict(X_green)[0])
  green_after_green = float(rf_reg.predict(X_green)[0])

  # Scenario 2: flood shock
  flood_shock = {"none": 0.0, "mild": 0.1, "moderate": 0.25, "extreme": 0.45}.get(
    flood_intensity, 0.0
  )
  flood_index_scenario = flood_index + (flood_shock if flood_event else 0.0)
  X_flood = np.array([[ndvi_scenario, ndbi, ndwi, lst_c, flood_index_scenario]])
  flood_prob_after = float(rf_clf.predict_proba(X_flood)[0, 1])

  # Scenario 3: urban sprawl projection using XGBoost
  years_ahead = max(0, sprawl_horizon - 2025)
  sprawl_signal = float(xgb.predict(X)[0] + years_ahead * 1.5)

  # Combine into dashboard-style metrics (0–100)
  green_cover = max(0.0, min(100.0, green_after_green))
  heat_stress = max(0.0, min(100.0, heat_after_green))
  flood_risk = max(0.0, min(100.0, 100.0 * flood_prob_after))
  density = max(
    0.0,
    min(
      100.0,
      metrics["builtUp"] + 0.2 * sprawl_signal - green_increase * 0.1,
    ),
  )

  scenario_metrics = {
    "density": round(density, 1),
    "greenCover": round(green_cover, 1),
    "heatStress": round(heat_stress, 1),
    "floodRisk": round(flood_risk, 1),
  }

  return {
    "city": city_id,
    "config": config,
    "baseline_metrics": metrics,
    "scenario_metrics": scenario_metrics,
    "model_insights": {
      "heat_pred_base": heat_pred_base,
      "green_pred_base": green_pred_base,
      "flood_prob_base": flood_prob_base,
      "sprawl_signal": sprawl_signal,
    },
  }

