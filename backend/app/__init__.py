from flask import Flask
from flask_cors import CORS

from .config import Config
from .extensions import init_extensions
from .routes.cities import cities_bp
from .routes.city_data import city_data_bp
from .routes.scenario import scenario_bp
from .routes.sdg import sdg_bp
from .routes.explain import explain_bp


def create_app(config_class: type[Config] = Config) -> Flask:
  """
  Application factory for the Resilient City Digital Twin backend.

  This sets up Flask, CORS, extensions (GEE, Firebase, Redis, Gemini),
  and registers all blueprints.
  """
  app = Flask(__name__)
  app.config.from_object(config_class)

  # Allow the React frontend (Vite dev + production origins) to call the API.
  CORS(
    app,
    resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}},
  )

  # Initialise integrations (idempotent, safe to call at startup)
  init_extensions(app)

  # Register blueprints
  app.register_blueprint(cities_bp, url_prefix="/api")
  app.register_blueprint(city_data_bp, url_prefix="/api")
  app.register_blueprint(scenario_bp, url_prefix="/api")
  app.register_blueprint(sdg_bp, url_prefix="/api")
  app.register_blueprint(explain_bp, url_prefix="/api")

  @app.get("/health")
  def health() -> dict:
    return {"status": "ok"}

  return app


app = create_app()

