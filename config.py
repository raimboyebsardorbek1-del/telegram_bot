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
CLICK_CARD_NUMBER = os.getenv("CLICK_CARD_NUMBER", "8600 0000 0000 0000")
SUBSCRIPTION_PRICE = 25000  # UZS
SUBSCRIPTION_DAYS = 30

# Muhim o'zgaruvchilarni tekshirish
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN .env faylida topilmadi")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY .env faylida topilmadi")
if not ADMIN_PASSWORD:
    raise ValueError("ADMIN_PASSWORD .env faylida topilmadi")
