import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "scraper_db")
    CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY")
    CLERK_PUBLISHABLE_KEY = os.getenv("CLERK_PUBLISHABLE_KEY")
    CLERK_JWKS_URL = os.getenv("CLERK_JWKS_URL")
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    STATIC_DIR = os.getenv("STATIC_DIR", "app/static")

settings = Settings()
