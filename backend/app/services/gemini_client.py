from __future__ import annotations

from typing import Any

from ..extensions import gemini_model


def generate_impact_story(payload: dict[str, Any]) -> str:
  """Generate a human-readable impact story for a scenario.

  If Gemini is not configured, returns a deterministic fallback string.
  """
  if gemini_model is None:
    city = payload.get("city", "the city")
    return (
      f"Scenario impact summary for {city}: Green cover, heat stress, and flood "
      "risk have been updated based on the configured scenario. Configure "
      "GEMINI_API_KEY to enable richer narrative explanations."
    )

  city = payload.get("city", "the city")
  baseline = payload.get("baseline", {})
  scenario = payload.get("scenario", {})
  config = payload.get("config", {})

  prompt = f"""
You are an urban resilience and climate adaptation expert.

City: {city}

Baseline metrics (approximate indices 0–100):
{baseline}

Scenario metrics (after applying interventions or shocks):
{scenario}

Scenario configuration (what the planner changed):
{config}

Write a concise, decision-focused impact story for a city-planning dashboard:
- Explain how green cover, urban heat, flood risk, and built-up intensity changed.
- Highlight trade-offs and co-benefits for SDG 11 (Sustainable Cities and Communities).
- End with 3–5 concrete, actionable recommendations for planners.
Keep it under 350 words, in clear language suitable for city officials.
  """

  response = gemini_model.generate_content(prompt)  # type: ignore[union-attr]
  text = getattr(response, "text", None)
  if callable(text):
    return text()
  return str(text or "")

