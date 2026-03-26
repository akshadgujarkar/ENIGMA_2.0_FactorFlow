from __future__ import annotations

import os
from pathlib import Path
from typing import Any

# Earth Engine module is provided by the `earthengine-api` package and
# exposes itself as `ee`.  It's optional for development so we import
# lazily and provide a helpful error if the package isn't installed.

try:
    import ee
except ImportError:  # pragma: no cover - environment issue
    ee = None

# Firebase and generative AI imports are also optional; if they fail to load we
# surface a clearer error at runtime rather than crash on module import.
try:
    import firebase_admin
    from firebase_admin import credentials as fb_credentials
except ImportError:  # pragma: no cover - environment issue
    firebase_admin = None  # type: ignore[assignment]
    fb_credentials = None  # type: ignore[assignment]

try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover - environment issue
    genai = None  # type: ignore[assignment]

from flask import Flask

from .config import Config

firebase_app: firebase_admin.App | None = None
gemini_model: Any | None = None

def init_earth_engine(config: Config) -> None:
    """Initialize Earth Engine for either server (service account) or local use.

    Uses only public Earth Engine API methods and avoids private internals.

    The import of ``ee`` is attempted at module load time but may fail when
    the package isn't installed.  We formalise that check here so that the
    application surface returns a useful error instead of an ``ImportError``
    during module import.
    """
    if ee is None:  # package missing
        raise RuntimeError(
            "Earth Engine API not installed. ``pip install earthengine-api`` "
            "or run `pip install -r backend/requirements.txt` to install "
            "project dependencies."
        )

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
        msg = (
            "Earth Engine project is not configured. Set GEE_PROJECT (or "
            "GOOGLE_CLOUD_PROJECT) to a Cloud project ID with Earth Engine enabled."
        )
        if config.ENV == "development":
            print(f"⚠️  WARNING: {msg}")
            print("   Earth Engine features will be unavailable until configured.")
            return
        raise RuntimeError(msg)

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
            msg = (
                "Earth Engine authentication/initialization failed. "
                "To use Earth Engine features locally, run `earthengine authenticate` "
                "(or set GEE_PROJECT + service account credentials). "
                "Continuing without Earth Engine for now."
            )
            if config.ENV == "development":
                print(f"⚠️  WARNING: {msg}")
            else:
                raise RuntimeError(msg) from auth_error


def init_firebase(config: Config) -> None:
  global firebase_app
  if firebase_app is not None:
    return

  if firebase_admin is None or fb_credentials is None:
      raise RuntimeError(
          "Firebase admin SDK is not installed. `pip install firebase-admin` "
          "or run `pip install -r backend/requirements.txt`."
      )

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
    msg = (
      "Firebase credentials file not found. To enable Firebase, create or "
      "place your credentials JSON file and set FIREBASE_CREDENTIALS_PATH."
    )
    if config.ENV == "development":
      print(f"⚠️  WARNING: {msg}")
      print("   Firebase features will be unavailable until configured.")
      return
    searched = ", ".join(str(p) for p in candidate_paths)
    raise RuntimeError(
      f"Firebase credentials file not found. Checked: {searched}"
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

  if genai is None:
    msg = "Google Generative AI not installed. `pip install google-generativeai`."
    if config.ENV == "development":
      print(f"⚠️  WARNING: {msg}")
      return
    raise RuntimeError(msg)

  if not config.GEMINI_API_KEY:
    msg = "GEMINI_API_KEY not configured. Generative AI features will be unavailable."
    if config.ENV == "development":
      print(f"⚠️  WARNING: {msg}")
      return
    raise RuntimeError(msg)

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
