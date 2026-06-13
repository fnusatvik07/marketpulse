"""Central configuration. Everything comes from .env at the project root."""
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# LLM
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Oxylabs
OXYLABS_USERNAME = os.getenv("OXYLABS_USERNAME", "")
OXYLABS_PASSWORD = os.getenv("OXYLABS_PASSWORD", "")
OXYLABS_URL = "https://realtime.oxylabs.io/v1/queries"

# Mock mode: forced via env, or automatic when credentials are missing
OXYLABS_MOCK = (
    os.getenv("OXYLABS_MOCK", "").lower() == "true"
    or not (OXYLABS_USERNAME and OXYLABS_PASSWORD)
)

# Marketplaces the user can choose at runtime (in the CLI or the UI).
# code  -> the Oxylabs `domain` value + a human label + currency, for display.
# This is the single source of truth; CLI and UI both read it.
MARKETPLACES = {
    "in": {"label": "India · amazon.in", "currency": "INR", "flag": "IN"},
    "com": {"label": "United States · amazon.com", "currency": "USD", "flag": "US"},
    "co.uk": {"label": "United Kingdom · amazon.co.uk", "currency": "GBP", "flag": "UK"},
    "de": {"label": "Germany · amazon.de", "currency": "EUR", "flag": "DE"},
    "ca": {"label": "Canada · amazon.ca", "currency": "CAD", "flag": "CA"},
    "com.au": {"label": "Australia · amazon.com.au", "currency": "AUD", "flag": "AU"},
    "ae": {"label": "UAE · amazon.ae", "currency": "AED", "flag": "AE"},
    "co.jp": {"label": "Japan · amazon.co.jp", "currency": "JPY", "flag": "JP"},
}

# The default marketplace if the user does not pick one.
AMAZON_DOMAIN = os.getenv("AMAZON_DOMAIN", "in")
if AMAZON_DOMAIN not in MARKETPLACES:
    AMAZON_DOMAIN = "in"

# Memory
POSTGRES_URI = os.getenv(
    "POSTGRES_URI",
    "postgresql://postgres:postgres@localhost:5442/marketpulse?sslmode=disable",
)

# Summarization knobs
MAX_MESSAGES = int(os.getenv("MAX_MESSAGES", "12"))
KEEP_LAST = int(os.getenv("KEEP_LAST", "6"))

# Image downloads
DOWNLOADS_DIR = PROJECT_ROOT / "downloads"
DOWNLOADS_DIR.mkdir(exist_ok=True)
