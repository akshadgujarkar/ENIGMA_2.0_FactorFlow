from __future__ import annotations

from typing import Any

from .gee_client import get_city_realtime_indices


def compute_sdg_scores(city_id: str, scenario: dict[str, Any]) -> dict[str, Any]:
  """Compute SDG-11 component scores and composite score.

  This uses the current real-time indices as a baseline, then applies simple
  scenario modifiers. The heavy-lift modelling is handled in the ML services,
  but this function presents a consistent, explainable scoring layer.
  """
  base = get_city_realtime_indices(city_id)
  metrics = base["metrics"]

  green = float(metrics["greenCover"])
  heat = float(metrics["heatStress"])
  flood = float(metrics["floodRisk"])
  built_up = float(metrics["builtUp"])

  green_increase = float(scenario.get("green_increase", 0))
  flood_intensity = str(scenario.get("flood_intensity", "none"))

  # Apply simple scenario adjustments on top of base metrics
  green_adj = min(100.0, green + green_increase * 0.8)
  heat_adj = max(0.0, heat - green_increase * 0.6)

  flood_shock = {"none": 0, "mild": 10, "moderate": 20, "extreme": 35}.get(
    flood_intensity, 0
  )
  flood_adj = max(0.0, min(100.0, flood + flood_shock - green_increase * 0.3))

  # Urban sprawl proxy: high built-up + high heat increases sprawl stress
  sprawl = max(0.0, min(100.0, 0.6 * built_up + 0.4 * heat))

  # Convert indicators to "health" scores where 100 is best
  green_score = green_adj
  heat_resilience_score = 100.0 - heat_adj
  flood_risk_score = 100.0 - flood_adj
  sprawl_score = 100.0 - sprawl

  composite = (
    0.3 * green_score
    + 0.25 * heat_resilience_score
    + 0.25 * flood_risk_score
    + 0.2 * sprawl_score
  )

  return {
    "city": city_id,
    "scenario": scenario,
    "scores": {
      "greenScore": round(green_score, 1),
      "heatResilienceScore": round(heat_resilience_score, 1),
      "floodRiskScore": round(flood_risk_score, 1),
      "urbanSprawlScore": round(sprawl_score, 1),
      "sdg11CompositeScore": round(composite, 1),
    },
    "baseline_metrics": metrics,
  }

