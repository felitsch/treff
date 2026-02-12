"""Application configuration."""

from pathlib import Path
from pydantic_settings import BaseSettings

# Resolve backend directory for absolute paths
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database - use absolute path so it works regardless of CWD
    DATABASE_URL: str = f"sqlite+aiosqlite:///{_BACKEND_DIR / 'treff.db'}"

    # JWT Authentication
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

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
        env_file = str(_BACKEND_DIR / ".env")
        env_file_encoding = "utf-8"


settings = Settings()
