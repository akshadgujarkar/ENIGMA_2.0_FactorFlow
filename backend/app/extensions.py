from __future__ import annotations

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
  """Initialise Google Earth Engine once per process.

  Uses service account credentials if provided, otherwise falls back to
  default credentials (e.g. `earthengine authenticate` flow).
  """
  if ee.data._credentials is not None:  # type: ignore[attr-defined]
    return

  if config.GEE_SERVICE_ACCOUNT and config.GEE_PRIVATE_KEY_PATH:
    service_account = config.GEE_SERVICE_ACCOUNT
    key_file = config.GEE_PRIVATE_KEY_PATH
    creds = ee.ServiceAccountCredentials(service_account, key_file)
    ee.Initialize(creds)
  else:
    ee.Initialize()


def init_firebase(config: Config) -> None:
  global firebase_app
  if firebase_app is not None:
    return
  if not config.FIREBASE_CREDENTIALS_PATH:
    return
  cred = fb_credentials.Certificate(config.FIREBASE_CREDENTIALS_PATH)
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

