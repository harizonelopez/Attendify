import os
from datetime import timedelta

# Project root directory
BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

class Config:
    # Application security
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "development-secret-key-change-later"
    )
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    
    # Database configuration
    DATABASE = os.path.join(
        BASE_DIR,
        "instance",
        "attendance.db"
    )

    # Application settings
    DEBUG = os.environ.get(
        "FLASK_DEBUG",
        "1"
    ) == "1"

    # Attendance analytics
    THRESHOLD = 75
    SEMESTER_SESSIONS = 14
    MIN_SESSIONS_FOR_AI = 3