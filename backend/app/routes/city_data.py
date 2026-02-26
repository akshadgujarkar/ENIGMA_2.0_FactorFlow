from __future__ import annotations

from flask import Blueprint, jsonify, request

from ..services.gee_client import (
  get_city_realtime_indices,
  get_city_timeseries,
  UnknownCityError,
)

city_data_bp = Blueprint("city_data", __name__)


@city_data_bp.get("/city/<city_id>/data")
def city_realtime_data(city_id: str):
  """Return current real-time indices for a city.

  This aggregates NDVI, LST, flood risk, and built-up percentage into a
  compact payload that the frontend dashboard consumes.
  """
  try:
    indices = get_city_realtime_indices(city_id)
  except UnknownCityError:
    return jsonify({"error": "Unknown city"}), 404
  return jsonify(indices)


@city_data_bp.get("/city/<city_id>/timeseries")
def city_timeseries(city_id: str):
  """Return historical indices for 2018–2025 for the given city."""
  start = request.args.get("start", "2018-01-01")
  end = request.args.get("end", "2025-12-31")
  try:
    series = get_city_timeseries(city_id, start=start, end=end)
  except UnknownCityError:
    return jsonify({"error": "Unknown city"}), 404
  return jsonify(series)

