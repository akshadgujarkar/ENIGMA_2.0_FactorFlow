from flask import Blueprint, request, jsonify
from app.services.geo_loader import load_city, save_latest
from app.services.simulation_engine import simulate
from app.services.sdg_calculator import calculate_sdg
from app.utils.validators import validate_scenario

simulation_bp = Blueprint("simulation", __name__)

@simulation_bp.route("/simulate", methods=["POST"])
def simulate_city():
    scenario = request.json

    validate_scenario(scenario)

    data = load_city()

    updated_data = simulate(
        data,
        scenario.get("green_increase", 0),
        scenario.get("rainfall", 0)
    )

    save_latest(updated_data)

    sdg_score = calculate_sdg(updated_data)

    return jsonify({
        "geojson": updated_data,
        "sdg_score": sdg_score
    })