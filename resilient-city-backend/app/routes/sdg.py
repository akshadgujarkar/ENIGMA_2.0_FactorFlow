from flask import Blueprint, jsonify
from app.services.geo_loader import load_latest
from app.services.sdg_calculator import calculate_sdg

sdg_bp = Blueprint("sdg", __name__)

@sdg_bp.route("/sdg", methods=["GET"])
def get_sdg():
    data = load_latest()
    score = calculate_sdg(data)
    return jsonify({"sdg_score": score})