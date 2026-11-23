import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"

# Ensure directories exist
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Simple crawler settings
START_URL = os.getenv("START_URL", "https://davietjal.org/")
ALLOWED_DOMAIN = os.getenv("ALLOWED_DOMAIN", "davietjal.org")
MAX_PAGES_DEFAULT = int(os.getenv("MAX_PAGES", "50"))
