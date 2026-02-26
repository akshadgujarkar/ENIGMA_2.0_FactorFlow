from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import ee
import firebase_admin
from firebase_admin import credentials as fb_credentials
import google.generativeai as genai
from flask import Flask

from .config import Config

firebase_app: firebase_admin.App | None = None
gemini_model: Any | None = None

def init_earth_engine(config: Config) -> None:
    """Initialize Earth Engine for either server (service account) or local use.

    Uses only public Earth Engine API methods and avoids private internals.
    """
    if ee.data.is_initialized():
        return

    # Earth Engine now often requires an explicit Cloud project.
    # Resolve from config first, then common environment variable names.
    project = (
        config.GEE_PROJECT
        or os.getenv("GOOGLE_CLOUD_PROJECT")
        or os.getenv("GCLOUD_PROJECT")
    )

    service_account = config.GEE_SERVICE_ACCOUNT
    key_file = config.GEE_PRIVATE_KEY_PATH

    if not project:
        raise RuntimeError(
            "Earth Engine project is not configured. Set GEE_PROJECT (or "
            "GOOGLE_CLOUD_PROJECT) to a Cloud project ID with Earth Engine enabled."
        )

    try:
        if service_account and key_file:
            # Server flow: non-interactive auth with a service account JSON key.
            creds = ee.ServiceAccountCredentials(service_account, key_file)
            ee.Initialize(credentials=creds, project=project)
            return

        # Local flow: use existing OAuth credentials if already authenticated.
        ee.Initialize(project=project)
    except ee.EEException as init_error:
        if service_account and key_file:
            raise RuntimeError(
                "Failed to initialize Earth Engine with service account. "
                "Verify GEE_SERVICE_ACCOUNT, GEE_PRIVATE_KEY_PATH, and project "
                "(GEE_PROJECT / GOOGLE_CLOUD_PROJECT)."
            ) from init_error

        try:
            # Prompt user auth only for local development.
            ee.Authenticate()
            ee.Initialize(project=project)
        except Exception as auth_error:
            raise RuntimeError(
                "Earth Engine authentication/initialization failed for local use. "
                "Run `earthengine authenticate` (or set service account credentials) "
                "and ensure a Cloud project is available via GEE_PROJECT or "
                "GOOGLE_CLOUD_PROJECT."
            ) from auth_error


def init_firebase(config: Config) -> None:
  global firebase_app
  if firebase_app is not None:
    return
  if not config.FIREBASE_CREDENTIALS_PATH:
    return

  # Support absolute paths and relative paths from either CWD or backend root.
  raw_path = config.FIREBASE_CREDENTIALS_PATH
  candidate_paths = [Path(raw_path)]
  if not Path(raw_path).is_absolute():
    backend_root = Path(__file__).resolve().parents[1]
    candidate_paths.append(Path.cwd() / raw_path)
    candidate_paths.append(backend_root / raw_path)

  cred_path = next((p for p in candidate_paths if p.exists()), None)
  if cred_path is None:
    searched = ", ".join(str(p) for p in candidate_paths)
    raise RuntimeError(
      "Firebase credentials file not found. Checked: "
      f"{searched}"
    )

  cred = fb_credentials.Certificate(str(cred_path))
  firebase_app = firebase_admin.initialize_app(
    cred,
    {"databaseURL": config.FIREBASE_DB_URL} if config.FIREBASE_DB_URL else None,
  )


def init_gemini(config: Config) -> None:
  global gemini_model
  if gemini_model is not None:
    return
  if not config.GEMINI_API_KEY:
    return
  genai.configure(api_key=config.GEMINI_API_KEY)
  gemini_model = genai.GenerativeModel(config.GEMINI_MODEL_NAME)


def init_extensions(app: Flask) -> None:
  """Initialise all external integrations safely."""
  config = app.config  # type: ignore[assignment]
  cfg = Config()  # Config already reads from env; used for type hints.

  # Explicitly use env-based config for integrations
  init_earth_engine(cfg)
  init_firebase(cfg)
  init_gemini(cfg)
