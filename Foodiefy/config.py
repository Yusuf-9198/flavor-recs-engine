from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
TEMPLATE_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
GENERATED_DIR = BASE_DIR / "generated"
OUTPUT_PATH = GENERATED_DIR / "top7recommendations.geojson"

BUSINESS_DATA_PATH = DATA_DIR / "Philadelphia_businesses.csv"
REVIEWS_DATA_PATH = DATA_DIR / "Final_philadelphia_reviews.csv"

APP_NAME = "Restaurant Recommendation Service"
DEFAULT_PORT = 5000
