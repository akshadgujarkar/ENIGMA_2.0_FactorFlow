from flask import Blueprint, jsonify
from app.services.geo_loader import load_city

city_bp = Blueprint("city", __name__)

@city_bp.route("/city", methods=["GET"])
def get_city():
    data = load_city()
    return jsonify(data)