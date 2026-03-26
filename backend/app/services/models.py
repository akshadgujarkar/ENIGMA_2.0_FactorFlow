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


def _clamp(value: float, lower: float = 0.0, upper: float = 100.0) -> float:
  return max(lower, min(upper, value))


def _hotspot_count(intensity: float, thresholds: tuple[float, float, float]) -> int:
  low, medium, high = thresholds
  if intensity >= high:
    return 4
  if intensity >= medium:
    return 3
  if intensity >= low:
    return 2
  return 1


def _generate_hotspots(
  hotspot_type: str,
  label_prefix: str,
  base_lng: float,
  base_lat: float,
  intensity: float,
  offsets: list[tuple[float, float]],
  count: int,
) -> list[dict[str, Any]]:
  hotspots: list[dict[str, Any]] = []
  for idx, (lng_offset, lat_offset) in enumerate(offsets[:count], start=1):
    hotspot_intensity = _clamp(intensity - (idx - 1) * 4.5)
    hotspots.append(
      {
        "type": hotspot_type,
        "lng": round(base_lng + lng_offset, 6),
        "lat": round(base_lat + lat_offset, 6),
        "label": f"{label_prefix} {idx}",
        "intensity": round(hotspot_intensity, 1),
      }
    )
  return hotspots


CITY_HOTSPOT_LAYOUTS: dict[str, dict[str, list[tuple[float, float]]]] = {
  "delhi": {
    "heat": [(0.020, 0.010), (0.034, -0.004), (-0.016, 0.018), (0.010, -0.024)],
    "flood": [(-0.015, -0.015), (-0.028, 0.008), (0.014, -0.024), (-0.006, 0.026)],
  },
  "mumbai": {
    "heat": [(0.018, 0.012), (0.030, -0.010), (-0.014, 0.020), (0.006, -0.022)],
    "flood": [(-0.020, -0.012), (-0.030, 0.006), (0.010, -0.026), (0.018, 0.014)],
  },
  "pune": {
    "heat": [(0.016, 0.010), (0.028, -0.008), (-0.012, 0.018), (0.008, -0.018)],
    "flood": [(-0.014, -0.014), (-0.024, 0.010), (0.012, -0.020), (-0.008, 0.022)],
  },
  "bengaluru": {
    "heat": [(0.014, 0.014), (0.026, -0.006), (-0.016, 0.016), (0.010, -0.020)],
    "flood": [(-0.012, -0.016), (-0.022, 0.012), (0.016, -0.018), (-0.004, 0.024)],
  },
  "hyderabad": {
    "heat": [(0.018, 0.010), (0.030, -0.006), (-0.014, 0.016), (0.012, -0.020)],
    "flood": [(-0.016, -0.014), (-0.026, 0.008), (0.014, -0.022), (-0.006, 0.024)],
  },
}


def _city_hotspot_offsets(city_id: str, hotspot_type: str) -> list[tuple[float, float]]:
  default_layout = {
    "heat": [(0.020, 0.010), (0.032, -0.006), (-0.018, 0.015), (0.008, -0.022)],
    "flood": [(-0.015, -0.015), (-0.028, 0.008), (0.014, -0.024), (-0.006, 0.026)],
  }
  return CITY_HOTSPOT_LAYOUTS.get(city_id, default_layout).get(hotspot_type, default_layout[hotspot_type])


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
  base_green = float(metrics["greenCover"])
  base_heat = float(metrics["heatStress"])
  base_flood = float(metrics["floodRisk"])
  base_density = float(metrics["builtUp"])

  green_increase = float(config.get("green_increase", 0))
  flood_event = bool(config.get("flood_event", False))
  flood_intensity = str(config.get("flood_intensity", "none"))
  sprawl_horizon = int(config.get("sprawl_horizon", 2030))

  # A. Environmental & Ecological parameters
  tree_planting_rate = float(config.get("tree_planting_rate", 0.0))  # % canopy gain
  wetland_restoration = float(config.get("wetland_restoration", 0.0))  # hectares

  # B. Urban Heat parameters
  cool_roof_coverage = float(config.get("cool_roof_coverage", 0.0))  # % roof area

  # C. Flood & Hydrological parameters
  drainage_improvement = float(config.get("drainage_improvement", 0.0))  # % capacity gain
  permeable_surface_gain = float(config.get("permeable_surface_gain", 0.0))  # % increase

  # D. Urban Growth & Infrastructure parameters
  densification_rate = float(config.get("densification_rate", 0.0))  # % per year

  # E. Socio-Economic Vulnerability parameters
  low_income_share = float(config.get("low_income_share", 0.0))  # % population

  # F. Policy & Planning Intervention parameters
  zoning_enforcement = float(config.get("zoning_enforcement", 0.0))  # 0–100

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

  # Base predictions (no scenario). These synthetic-model outputs are used as
  # directional signals, not as direct dashboard values.
  heat_pred_base = float(lin.predict(X)[0])
  green_pred_base = float(rf_reg.predict(X)[0])
  flood_prob_base = float(rf_clf.predict_proba(X)[0, 1])

  # Scenario 1: green cover change → update NDVI feature and re-run regressors
  effective_green_increase = green_increase + 0.6 * tree_planting_rate + 0.3 * wetland_restoration
  ndvi_scenario = ndvi + effective_green_increase / 120.0
  X_green = np.array([[ndvi_scenario, ndbi, ndwi, lst_c, flood_index]], dtype=float)
  heat_after_green = float(lin.predict(X_green)[0])
  green_after_green = float(rf_reg.predict(X_green)[0])

  # Scenario 2: flood shock
  flood_shock = {"none": 0.0, "mild": 0.1, "moderate": 0.25, "extreme": 0.45}.get(
    flood_intensity, 0.0
  )
  # Flood mitigation from drainage and permeable surfaces (0–1 scale)
  flood_mitigation = 0.5 * (drainage_improvement / 100.0) + 0.5 * (permeable_surface_gain / 100.0)
  flood_index_scenario = flood_index + (flood_shock if flood_event else 0.0) * (1.0 - flood_mitigation)
  X_flood = np.array([[ndvi_scenario, ndbi, ndwi, lst_c, flood_index_scenario]])
  flood_prob_after = float(rf_clf.predict_proba(X_flood)[0, 1])

  # Scenario 3: urban sprawl projection using XGBoost
  years_ahead = max(0, sprawl_horizon - 2025)
  sprawl_signal = float(xgb.predict(X)[0] + years_ahead * (1.0 + densification_rate / 5.0))

  # Keep scenario metrics anchored to the live baseline values instead of
  # replacing them with raw synthetic-model outputs on a mismatched scale.
  green_model_delta = _clamp(green_after_green - green_pred_base, -12.0, 18.0)
  heat_model_delta = _clamp(heat_after_green - heat_pred_base, -12.0, 12.0)
  flood_model_delta = _clamp((flood_prob_after - flood_prob_base) * 100.0, -20.0, 35.0)

  green_cover = _clamp(
    base_green
    + green_increase * 0.45
    + tree_planting_rate * 0.18
    + wetland_restoration * 0.7
    - densification_rate * 1.5
    + green_model_delta
  )
  heat_stress = _clamp(
    base_heat
    - green_increase * 0.2
    - tree_planting_rate * 0.08
    - wetland_restoration * 0.2
    - cool_roof_coverage * 0.12
    - zoning_enforcement * 0.03
    + densification_rate * 3.0
    + max(0.0, base_density - 60.0) * 0.05
    + heat_model_delta
  )
  flood_severity_bump = {"none": 0.0, "mild": 8.0, "moderate": 16.0, "extreme": 28.0}.get(
    flood_intensity, 0.0
  )
  flood_risk = _clamp(
    base_flood
    + (flood_severity_bump if flood_event else 0.0)
    - drainage_improvement * 0.18
    - permeable_surface_gain * 0.28
    - wetland_restoration * 0.35
    + densification_rate * 1.5
    + flood_model_delta
  )
  density = _clamp(
    base_density
    + years_ahead * 0.6
    + densification_rate * 4.0
    - effective_green_increase * 0.15
    + _clamp(sprawl_signal / 20.0, -5.0, 18.0)
  )

  # Socio-economic vulnerability index (0–100) used for insights and map hotspots
  vulnerability_index = max(0.0, min(100.0, low_income_share * 0.7 + flood_risk * 0.3))

  scenario_metrics = {
    "density": round(density, 1),
    "greenCover": round(green_cover, 1),
    "heatStress": round(heat_stress, 1),
    "floodRisk": round(flood_risk, 1),
  }

  # Generate multiple synthetic hotspot locations per city to drive map markers.
  city_meta = next(c for c in SUPPORTED_CITIES if c["id"] == city_id)
  base_lng, base_lat = city_meta["center"]
  hotspots: list[dict[str, Any]] = []

  heat_offsets = _city_hotspot_offsets(city_id, "heat")
  flood_offsets = _city_hotspot_offsets(city_id, "flood")
  heat_trigger_intensity = max(base_heat, heat_stress)
  heat_intervention_signal = green_increase + tree_planting_rate + cool_roof_coverage / 2.0

  if heat_trigger_intensity >= 32.0 or heat_intervention_signal >= 25.0:
    heat_count = _hotspot_count(heat_trigger_intensity, (35.0, 50.0, 65.0))
    hotspots.extend(
      _generate_hotspots(
        hotspot_type="heat",
        label_prefix="Urban heat hotspot",
        base_lng=base_lng,
        base_lat=base_lat,
        intensity=heat_trigger_intensity,
        offsets=heat_offsets,
        count=heat_count,
      )
    )
  if flood_risk > 30 or flood_event:
    flood_trigger_intensity = max(flood_risk, 35.0 if flood_event else flood_risk)
    flood_count = _hotspot_count(flood_trigger_intensity, (35.0, 50.0, 70.0))
    hotspots.extend(
      _generate_hotspots(
        hotspot_type="flood",
        label_prefix="Flood-prone lowland",
        base_lng=base_lng,
        base_lat=base_lat,
        intensity=flood_risk,
        offsets=flood_offsets,
        count=flood_count,
      )
    )

  return {
    "city": city_id,
    "config": config,
    "baseline_data_source": base.get("dataSource", "unknown"),
    "baseline_metrics": metrics,
    "scenario_metrics": scenario_metrics,
    "model_insights": {
      "heat_pred_base": heat_pred_base,
      "green_pred_base": green_pred_base,
      "flood_prob_base": flood_prob_base,
      "sprawl_signal": sprawl_signal,
      "vulnerability_index": vulnerability_index,
    },
    "hotspots": hotspots,
  }

