from __future__ import annotations

from flask import Blueprint, jsonify, request

from ..services.sdg_scores import compute_sdg_scores

sdg_bp = Blueprint("sdg", __name__)


@sdg_bp.get("/sdg/health-scores")
def sdg_health_scores():
  """Return SDG-11 health scores for a given city and (optionally) scenario."""
  city = request.args.get("city")
  if not city:
    return jsonify({"error": "Missing 'city' query parameter"}), 400

  scenario = {
    "green_increase": float(request.args.get("green_increase", 0)),
    "flood_intensity": request.args.get("flood_intensity", "none"),
    "sprawl_horizon": int(request.args.get("sprawl_horizon", 2030)),
  }

  scores = compute_sdg_scores(city_id=city, scenario=scenario)
  return jsonify(scores)

