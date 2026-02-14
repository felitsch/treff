"""Application configuration."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Resolve backend directory for absolute paths
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent

IS_VERCEL = os.environ.get("VERCEL") == "1"

# On Vercel, use /tmp for SQLite (ephemeral but functional)
if IS_VERCEL:
    _DB_PATH = "/tmp/treff.db"
else:
    _DB_PATH = str(_BACKEND_DIR / "treff.db")


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database - use absolute path so it works regardless of CWD
    DATABASE_URL: str = f"sqlite+aiosqlite:///{_DB_PATH}"

    # JWT Authentication
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Default User (seeded on startup for Vercel ephemeral DB)
    DEFAULT_USER_EMAIL: str = "admin@treff.de"
    DEFAULT_USER_PASSWORD: str = "treff2024"

    # Google Gemini API
    GEMINI_API_KEY: str = ""

    # OpenAI API (Optional fallback)
    OPENAI_API_KEY: str = ""

    # Stock Photo APIs
    UNSPLASH_ACCESS_KEY: str = ""
    PEXELS_API_KEY: str = ""

    # Server
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:5173"

    # Logging
    LOG_LEVEL: str = "INFO"
    SQL_ECHO: bool = False

    class Config:
        # On Vercel, env vars come from the dashboard — no .env file
        env_file = None if IS_VERCEL else str(_BACKEND_DIR / ".env")
        env_file_encoding = "utf-8"


settings = Settings()
