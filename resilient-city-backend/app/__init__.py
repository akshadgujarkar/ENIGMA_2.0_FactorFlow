from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)

    # Import Blueprints
    from app.routes.health import health_bp
    from app.routes.city_data import city_bp
    from app.routes.simulation import simulation_bp
    from app.routes.sdg import sdg_bp

    # Register Blueprints
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(city_bp, url_prefix="/api")
    app.register_blueprint(simulation_bp, url_prefix="/api")
    app.register_blueprint(sdg_bp, url_prefix="/api")

    return app