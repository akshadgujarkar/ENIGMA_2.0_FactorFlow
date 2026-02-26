import json
from app.config import PROCESSED_DATA_PATH, LATEST_DATA_PATH

def load_city():
    with open(PROCESSED_DATA_PATH) as f:
        return json.load(f)

def load_latest():
    try:
        with open(LATEST_DATA_PATH) as f:
            return json.load(f)
    except:
        return load_city()

def save_latest(data):
    with open(LATEST_DATA_PATH, "w") as f:
        json.dump(data, f)