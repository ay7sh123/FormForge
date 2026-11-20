import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()

DEFAULT_SECRET = "dev-only-change-me"


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", DEFAULT_SECRET)
    MONGO_URI = os.getenv("MONGO_URI")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "formforge")

    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "0") == "1"

    MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # 1 MB per request
