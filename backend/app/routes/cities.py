from __future__ import annotations

from flask import Blueprint, jsonify

cities_bp = Blueprint("cities", __name__)


SUPPORTED_CITIES = [
  {
    "id": "mumbai",
    "name": "Mumbai",
    "country": "India",
    "center": [72.8777, 19.0760],
    "zoom": 11.5,
  },
  {
    "id": "pune",
    "name": "Pune",
    "country": "India",
    "center": [73.8567, 18.5204],
    "zoom": 11.5,
  },
  {
    "id": "bengaluru",
    "name": "Bengaluru",
    "country": "India",
    "center": [77.5946, 12.9716],
    "zoom": 11.5,
  },
  {
    "id": "delhi",
    "name": "Delhi",
    "country": "India",
    "center": [77.2090, 28.6139],
    "zoom": 11.0,
  },
  {
    "id": "hyderabad",
    "name": "Hyderabad",
    "country": "India",
    "center": [78.4867, 17.3850],
    "zoom": 11.5,
  },
]


@cities_bp.get("/cities")
def list_cities():
  """Return a static list of supported cities.

  The spatial extents and metadata for each city are defined here and used by
  downstream GEE and ML services.
  """
  return jsonify(SUPPORTED_CITIES)

