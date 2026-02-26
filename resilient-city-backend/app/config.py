import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

PROCESSED_DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "base_city.geojson")
LATEST_DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "latest_city.geojson")