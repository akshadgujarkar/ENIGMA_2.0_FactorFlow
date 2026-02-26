from __future__ import annotations

from flask import Blueprint, jsonify, request

from ..services.models import (
  run_scenario_simulation,
  retrain_models_for_city,
  UnknownCityError as ModelUnknownCityError,
)

scenario_bp = Blueprint("scenario", __name__)


@scenario_bp.post("/scenario/simulate")
def simulate_scenario():
  """Run a what-if simulation for a given city and configuration.

  Expected JSON body:
  {
    "city": "mumbai",
    "green_increase": 10,
    "flood_event": true,
    "flood_intensity": "moderate",
    "sprawl_horizon": 2030
  }
  """
  data = request.get_json(force=True, silent=True) or {}
  city = data.get("city")
  if not city:
    return jsonify({"error": "Missing 'city' in request body"}), 400
  try:
    result = run_scenario_simulation(city_id=city, config=data)
  except ModelUnknownCityError:
    return jsonify({"error": "Unknown city"}), 404
  return jsonify(result)


@scenario_bp.post("/scenario/retrain")
def retrain_scenario_models():
  """Trigger a background retraining of city models (simple synchronous version).

  Body:
    { "city": "mumbai" }
  """
  data = request.get_json(force=True, silent=True) or {}
  city = data.get("city")
  if not city:
    return jsonify({"error": "Missing 'city' in request body"}), 400
  try:
    summary = retrain_models_for_city(city_id=city)
  except ModelUnknownCityError:
    return jsonify({"error": "Unknown city"}), 404
  return jsonify(summary)

