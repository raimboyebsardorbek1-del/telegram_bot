import os
from dotenv import load_dotenv

# .env faylidan o'zgaruvchilarni yuklash
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# Safely convert ADMIN_ID to int
admin_id_env = os.getenv("ADMIN_ID", "0")
try:
    if admin_id_env and admin_id_env.isdigit():
        ADMIN_ID = int(admin_id_env)
    else:
        ADMIN_ID = 0
except ValueError:
    ADMIN_ID = 0

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "default_secret_for_local_dev")

# Click to'lov sozlamalari
CLICK_SERVICE_ID = os.getenv("CLICK_SERVICE_ID")
CLICK_MERCHANT_ID = os.getenv("CLICK_MERCHANT_ID")
CLICK_SECRET_KEY = os.getenv("CLICK_SECRET_KEY")
CLICK_MERCHANT_USER_ID = os.getenv("CLICK_MERCHANT_USER_ID")

# Pricing (UZS)
PRICES = {
    "maqola": {
        "3-10": 4000,
        "10-15": 6000,
        "15-20": 8000
    },
    "mustaqil": {
        "10-15": 3000,
        "15-20": 4000,
        "20-25": 5000
    },
    "referat": {
        "10-15": 3000,
        "15-20": 4000,
        "20-25": 5000
    },
    "taqdimot": {
        "6-19": 3000,
        "20-30": 5000,
        "premium_6_19": 6000,
        "premium_20_30": 8000
    }
}

# Muhim o'zgaruvchilarni tekshirish
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN .env faylida topilmadi")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY .env faylida topilmadi")
