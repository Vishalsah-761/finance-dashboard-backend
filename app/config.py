import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/finance_db")
    # Hardcoded fallback so it never changes between restarts
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "finance-super-secret-key-hardcoded-2024")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JSON_SORT_KEYS = False


class TestingConfig(Config):
    TESTING = True
    MONGO_URI = "mongomock://localhost/finance_test_db"
