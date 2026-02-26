import os
from dataclasses import dataclass


@dataclass
class Config:
  """Base configuration loaded from environment variables.

  All secrets should be provided via a .env file or the deployment environment.
  """

  # Flask
  DEBUG: bool = os.getenv("FLASK_DEBUG", "false").lower() == "true"
  ENV: str = os.getenv("FLASK_ENV", "production")

  # CORS
  CORS_ORIGINS: str | None = os.getenv("CORS_ORIGINS")

  # Google Earth Engine
  GEE_SERVICE_ACCOUNT: str | None = os.getenv("GEE_SERVICE_ACCOUNT")
  GEE_PRIVATE_KEY_PATH: str | None = os.getenv("GEE_PRIVATE_KEY_PATH")

  # Firebase
  FIREBASE_CREDENTIALS_PATH: str | None = os.getenv("FIREBASE_CREDENTIALS_PATH")
  FIREBASE_DB_URL: str | None = os.getenv("FIREBASE_DB_URL")

  # Redis
  REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
  REDIS_CACHE_TTL_SECONDS: int = int(os.getenv("REDIS_CACHE_TTL_SECONDS", "3600"))

  # Gemini (Google Generative AI)
  GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
  GEMINI_MODEL_NAME: str = os.getenv("GEMINI_MODEL_NAME", "models/gemini-2.5-flash")

  # Model storage
  MODELS_DIR: str = os.getenv("MODELS_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models")))

