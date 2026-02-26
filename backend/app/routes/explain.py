from __future__ import annotations

from flask import Blueprint, jsonify, request

from ..services.gemini_client import generate_impact_story

explain_bp = Blueprint("explain", __name__)


@explain_bp.post("/explain")
def explain_scenario():
  """Return a Gemini-generated natural language explanation of scenario impact.

  Body should contain:
    {
      "city": "mumbai",
      "baseline": { ...metrics... },
      "scenario": { ...metrics... },
      "config": { ...scenarioConfig... }
    }
  """
  payload = request.get_json(force=True, silent=True) or {}
  story = generate_impact_story(payload)
  return jsonify({"story": story})

