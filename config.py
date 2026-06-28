import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
PORT = int(os.getenv("PORT", "8080"))
MAX_HISTORY = int(os.getenv("MAX_HISTORY", "20"))
MAX_RPM = int(os.getenv("MAX_RPM", "10"))

def validate():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не задан!")
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY не задан!")
