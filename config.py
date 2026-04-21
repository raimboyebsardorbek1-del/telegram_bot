import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "default_secret_for_local_dev")

SUBSCRIPTION_PRICE = 15000  # UZS, masalan
SUBSCRIPTION_DAYS = 30

# Add some basic validation to fail fast if config is missing
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in .env")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set in .env")
if not ADMIN_PASSWORD:
    raise ValueError("ADMIN_PASSWORD is not set in .env")
