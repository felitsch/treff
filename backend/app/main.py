"""TREFF Sprachreisen Post-Generator - FastAPI Backend"""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import engine, Base, async_session
from app.core.seed_templates import seed_default_templates
from app.api.routes import auth, posts, templates, assets, calendar, suggestions, analytics, settings as settings_router, health, export, slides, ai

logger = logging.getLogger(__name__)

# Resolve paths relative to this file's location
BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = BASE_DIR / "static" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Startup
    logger.info("Starting TREFF Post-Generator backend...")

    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified")

    # Seed default templates if not already present
    async with async_session() as session:
        try:
            count = await seed_default_templates(session)
            if count > 0:
                logger.info(f"Seeded {count} default templates")
        except Exception as e:
            logger.error(f"Failed to seed templates: {e}")

    yield

    # Shutdown
    logger.info("Shutting down TREFF Post-Generator backend...")
    await engine.dispose()


app = FastAPI(
    title="TREFF Post-Generator API",
    description="Social Media Content Tool for TREFF Sprachreisen",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for uploads
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# API Routes
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(templates.router, prefix="/api/templates", tags=["Templates"])
app.include_router(posts.router, prefix="/api/posts", tags=["Posts"])
app.include_router(slides.router, prefix="/api/posts", tags=["Post Slides"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI Generation"])
app.include_router(export.router, prefix="/api/export", tags=["Export"])
app.include_router(assets.router, prefix="/api/assets", tags=["Assets"])
app.include_router(calendar.router, prefix="/api/calendar", tags=["Calendar"])
app.include_router(suggestions.router, prefix="/api/suggestions", tags=["Suggestions"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(settings_router.router, prefix="/api/settings", tags=["Settings"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
