import os
from datetime import timedelta
from dotenv import load_dotenv

# Project root directory
BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

load_dotenv(os.path.join(BASE_DIR, "secrets.env"))

class Config:
    # Application security
    SECRET_KEY = os.environ.get("SECRET_KEY")

    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY is missing. Check your secrets.env file.")

    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Enable source cookies only when HTTPS is configured
    SESSION_COOKIE_SECURE = (
        os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"
    )
    
    # Database configuration
    DATABASE = os.path.join(BASE_DIR, "instance", "attendance.db")

    # PostgreSQL connection URL(provided by Render in production)
    DATABASE_URL = os.environ.get("DATABASE_URL")

    # Application settings
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"

    # Attendance analytics
    THRESHOLD = 75
    SEMESTER_SESSIONS = 14
    MIN_SESSIONS_FOR_AI = 3