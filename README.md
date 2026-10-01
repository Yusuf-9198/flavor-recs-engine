# Restaurant Recommendation Engine

A custom-built restaurant recommendation system engineered for personalized dining discovery using geospatial clustering and NLP-based review matching.

## Overview

This project delivers nearby restaurant recommendations by combining:
- geospatial clustering for local relevance
- review text processing and filtering
- TF-IDF vector similarity for user preference matching
- GeoJSON output for map-friendly rendering

The solution is designed to be modular, maintainable, and deployment-safe while preserving the original business logic and recommendation flow.

## Architecture

The application is organized around a small but scalable backend service.

- `Foodiefy/app.py` — Flask app factory and bootstrap
- `Foodiefy/routes.py` — API route registration and request validation
- `Foodiefy/recommendation_service.py` — ML inference, clustering, and GeoJSON serialization
- `Foodiefy/config.py` — safe path and configuration settings
- `Foodiefy/templates/` — frontend UI layer
- `Foodiefy/static/` — UI assets and frontend scripts
- `Foodiefy/data/` — business and review datasets

## Core Recommendation Flow

1. The user submits latitude, longitude, and a preference phrase such as "pizza pasta".
2. Nearby restaurants are grouped using KMeans clustering around the user’s coordinates.
3. Review text is cleaned and normalized to remove stop words and punctuation.
4. TF-IDF vectors model the restaurant review corpus and match user preference language.
5. The ranked recommendations are returned as GeoJSON for the map display.

## API Endpoints

### `GET /`
Renders the restaurant map UI.

### `GET /health`
Returns application health status.

### `POST /test`
Accepts JSON payloads in the format:

```json
{
  "latitude": 39.951732,
  "longitude": -75.142140,
  "words": "pizza pasta"
}
```

Returns a GeoJSON `FeatureCollection` with ranked restaurant predictions.

## Local Setup

### 1. Create an environment

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the application

```bash
python run.py
```

The app starts on `http://localhost:5000` by default.

## Deployment Notes

- This project is compatible with a Flask WSGI deployment pattern.
- Use `wsgi.py` for production-style deployment entrypoints.
- Gunicorn is configured with `gunicorn.conf.py` and a `Procfile` for host deployment.
- Docker Compose includes a dedicated Nginx reverse proxy in front of the app container.
- The ML pipeline expects the local CSV data files in the `Foodiefy/data` directory.

### Production run commands

```bash
gunicorn --config gunicorn.conf.py wsgi:app
```

```bash
docker-compose up --build
```

## Data Sources

The recommendation engine uses restaurant and review data derived from the Philadelphia business and review datasets included in the project.

## Testing

```bash
python -m pytest tests/test_recommendation_service.py -q
```

## Ownership

This implementation has been refactored into a cleaner, modular backend architecture with a modern, personal engineering structure while preserving the original recommendation behavior and data flow.

