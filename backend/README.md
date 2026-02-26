## Resilient City Digital Twin – Backend

This is the Flask backend for the SDG 11 "Resilient City" Digital Twin. It connects
to Google Earth Engine, Firebase, and Gemini, and serves ML-powered
scenario simulations to the React frontend.

### Tech stack

- **Flask** with blueprints
- **Google Earth Engine** (Sentinel‑1/2, Landsat 8/9)
- **Firebase Admin SDK** (for storing pre‑processed indices and model artefacts)
- **Google Generative AI (Gemini 2.5 Flash)** for narrative explanations
- **scikit‑learn + XGBoost + PyTorch (stub CNN)** for ML models

### Project layout

- `app/__init__.py` – Flask app factory and blueprint registration
- `app/config.py` – configuration and environment variables
- `app/extensions.py` – initialises GEE, Firebase, Gemini
- `app/routes/` – REST endpoints:
  - `cities.py` – `/api/cities`
  - `city_data.py` – `/api/city/<city>/data`, `/api/city/<city>/timeseries`
  - `scenario.py` – `/api/scenario/simulate`, `/api/scenario/retrain`
  - `sdg.py` – `/api/sdg/health-scores`
  - `explain.py` – `/api/explain`
- `app/services/` – GEE, ML, scoring, and Gemini helpers
- `models/` – trained model files saved via `joblib`
- `data/` – (optional) pre‑processed feature datasets

### Setup

1. **Install dependencies**

   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment**

   ```bash
   cp .env.example .env
   # Edit .env with your own keys and paths
   ```

   Required pieces:

   - Google Earth Engine credentials:
     - Either run `earthengine authenticate` locally (free OAuth flow), **or**
     - Provide a service account + JSON key if you prefer.
   - Firebase service account JSON + database URL (free tier)
   - Gemini API key from Google AI Studio

3. **Authenticate Earth Engine locally (if needed)**

   If you are not using a service account, run:

   ```bash
   earthengine authenticate
   ```

4. **Run the API**

   ```bash
   export FLASK_APP=app
   flask run --host=0.0.0.0 --port=8000
   ```

   Or with gunicorn in production:

   ```bash
   gunicorn -b 0.0.0.0:8000 'app:app'
   ```

### Core endpoints

- `GET /api/cities`
- `GET /api/city/<city>/data`
- `GET /api/city/<city>/timeseries?start=2018-01-01&end=2025-12-31`
- `POST /api/scenario/simulate`
- `POST /api/scenario/retrain`
- `GET /api/sdg/health-scores?city=mumbai&green_increase=10&flood_intensity=moderate`
- `POST /api/explain`

### Adding new cities

1. Add a new entry to `SUPPORTED_CITIES` in `app/routes/cities.py` with:
   - `id`, `name`, `country`, `center` `[lon, lat]`, `zoom`
2. Retrain models for the new city:

   ```bash
   curl -X POST http://localhost:8000/api/scenario/retrain -H "Content-Type: application/json" -d '{"city":"new-city-id"}'
   ```

3. Update the frontend city selector to include the new city.

