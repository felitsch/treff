"""TREFF Sprachreisen Post-Generator - FastAPI Backend"""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.paths import IS_VERCEL, get_upload_dir
from app.core.database import engine, Base, async_session
from app.core.seed_users import seed_default_users
from app.core.seed_templates import seed_default_templates, seed_story_teaser_templates, seed_story_series_templates
from app.core.seed_suggestions import seed_default_suggestions
from app.core.seed_humor_formats import seed_humor_formats
from app.core.seed_hashtag_sets import seed_hashtag_sets
from app.core.seed_ctas import seed_default_ctas
from app.core.seed_music_tracks import seed_music_tracks
from app.core.seed_video_templates import seed_video_templates
from app.core.seed_recurring_formats import seed_recurring_formats
from app.api.routes import auth, posts, templates, assets, calendar, suggestions, analytics, settings as settings_router, health, export, slides, ai, students, story_arcs, story_episodes, hashtag_sets, ctas, interactive_elements, recycling, series_reminders, video_overlays, audio_mixer, video_composer, video_templates, video_export, recurring_formats, post_relations

logger = logging.getLogger(__name__)

# Resolve uploads directory (Vercel-aware)
UPLOADS_DIR = get_upload_dir()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Startup
    logger.info("Starting TREFF Post-Generator backend...")

    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified")

    # Migrate: add video-specific columns to assets table if missing
    async with engine.begin() as conn:
        from sqlalchemy import text
        try:
            await conn.execute(text("ALTER TABLE assets ADD COLUMN duration_seconds FLOAT"))
            logger.info("Added duration_seconds column to assets table")
        except Exception:
            pass  # Column already exists
        try:
            await conn.execute(text("ALTER TABLE assets ADD COLUMN thumbnail_path VARCHAR"))
            logger.info("Added thumbnail_path column to assets table")
        except Exception:
            pass  # Column already exists
        try:
            await conn.execute(text("ALTER TABLE students ADD COLUMN personality_preset TEXT"))
            logger.info("Added personality_preset column to students table")
        except Exception:
            pass  # Column already exists
        try:
            await conn.execute(text("ALTER TABLE posts ADD COLUMN story_arc_id INTEGER REFERENCES story_arcs(id)"))
            logger.info("Added story_arc_id column to posts table")
        except Exception:
            pass  # Column already exists
        try:
            await conn.execute(text("ALTER TABLE posts ADD COLUMN episode_number INTEGER"))
            logger.info("Added episode_number column to posts table")
        except Exception:
            pass  # Column already exists
        try:
            await conn.execute(text("ALTER TABLE posts ADD COLUMN linked_post_group_id VARCHAR"))
            logger.info("Added linked_post_group_id column to posts table")
        except Exception:
            pass  # Column already exists
        try:
            await conn.execute(text("ALTER TABLE posts ADD COLUMN student_id INTEGER REFERENCES students(id) ON DELETE SET NULL"))
            logger.info("Added student_id column to posts table")
        except Exception:
            pass  # Column already exists

    # Seed default user (critical for Vercel where DB is ephemeral)
    async with async_session() as session:
        try:
            count = await seed_default_users(session)
            if count > 0:
                logger.info(f"Seeded {count} default user(s)")
        except Exception as e:
            logger.error(f"Failed to seed default user: {e}")

    # Seed default templates if not already present
    async with async_session() as session:
        try:
            count = await seed_default_templates(session)
            if count > 0:
                logger.info(f"Seeded {count} default templates")
        except Exception as e:
            logger.error(f"Failed to seed templates: {e}")

    # Seed story-teaser templates if not already present
    async with async_session() as session:
        try:
            count = await seed_story_teaser_templates(session)
            if count > 0:
                logger.info(f"Seeded {count} story-teaser templates")
        except Exception as e:
            logger.error(f"Failed to seed story-teaser templates: {e}")

    # Seed story-series templates if not already present
    async with async_session() as session:
        try:
            count = await seed_story_series_templates(session)
            if count > 0:
                logger.info(f"Seeded {count} story-series templates")
        except Exception as e:
            logger.error(f"Failed to seed story-series templates: {e}")

    # Seed default content suggestions if not already present
    async with async_session() as session:
        try:
            count = await seed_default_suggestions(session)
            if count > 0:
                logger.info(f"Seeded {count} default content suggestions")
        except Exception as e:
            logger.error(f"Failed to seed suggestions: {e}")

    # Seed default humor formats if not already present
    async with async_session() as session:
        try:
            count = await seed_humor_formats(session)
            if count > 0:
                logger.info(f"Seeded {count} default humor formats")
        except Exception as e:
            logger.error(f"Failed to seed humor formats: {e}")

    # Seed default hashtag sets if not already present
    async with async_session() as session:
        try:
            count = await seed_hashtag_sets(session)
            if count > 0:
                logger.info(f"Seeded {count} default hashtag sets")
        except Exception as e:
            logger.error(f"Failed to seed hashtag sets: {e}")

    # Seed default CTAs if not already present
    async with async_session() as session:
        try:
            count = await seed_default_ctas(session)
            if count > 0:
                logger.info(f"Seeded {count} default CTAs")
        except Exception as e:
            logger.error(f"Failed to seed CTAs: {e}")

    # Seed default music tracks for audio library
    async with async_session() as session:
        try:
            count = await seed_music_tracks(session)
            if count > 0:
                logger.info(f"Seeded {count} default music tracks")
        except Exception as e:
            logger.error(f"Failed to seed music tracks: {e}")

    # Seed default video branding templates (intro/outro)
    async with async_session() as session:
        try:
            count = await seed_video_templates(session)
            if count > 0:
                logger.info(f"Seeded {count} default video branding templates")
        except Exception as e:
            logger.error(f"Failed to seed video templates: {e}")

    # Seed default recurring formats (Running Gags)
    async with async_session() as session:
        try:
            count = await seed_recurring_formats(session)
            if count > 0:
                logger.info(f"Seeded {count} default recurring formats")
        except Exception as e:
            logger.error(f"Failed to seed recurring formats: {e}")

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

# CORS — include Vercel preview/production URLs
_allowed_origins = [settings.FRONTEND_URL, "http://localhost:5173"]
_vercel_url = os.environ.get("VERCEL_URL")
if _vercel_url:
    _allowed_origins.append(f"https://{_vercel_url}")
_vercel_project_url = os.environ.get("VERCEL_PROJECT_PRODUCTION_URL")
if _vercel_project_url:
    _allowed_origins.append(f"https://{_vercel_project_url}")
# Deduplicate
_allowed_origins = list(set(_allowed_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom exception handlers for graceful error responses

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with meaningful messages.

    - Malformed JSON → 400 Bad Request
    - Missing/invalid fields → 422 Unprocessable Entity with field details
    """
    errors = exc.errors()

    # Check if this is a JSON decode error (malformed JSON body)
    for error in errors:
        if error.get("type") == "json_invalid":
            return JSONResponse(
                status_code=400,
                content={
                    "detail": "Bad Request: The request body contains malformed JSON. Please send a valid JSON object.",
                    "errors": [
                        {
                            "type": error.get("type"),
                            "message": str(error.get("msg", "Invalid JSON")),
                        }
                    ],
                },
            )

    # For field validation errors (missing fields, wrong types, etc.) → 422
    field_errors = []
    for error in errors:
        loc = error.get("loc", [])
        # Build a human-readable field path (skip 'body' prefix)
        field_path = ".".join(str(part) for part in loc if part != "body")
        field_errors.append(
            {
                "field": field_path,
                "message": error.get("msg", "Validation error"),
                "type": error.get("type", "unknown"),
            }
        )

    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error: One or more fields failed validation.",
            "errors": field_errors,
        },
    )


# Static files for uploads
if IS_VERCEL:
    # On Vercel, StaticFiles can't serve from /tmp reliably across invocations.
    # Use a catch-all route instead.
    @app.get("/uploads/{file_path:path}")
    async def serve_upload(file_path: str):
        full_path = UPLOADS_DIR / file_path
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        return FileResponse(str(full_path))
else:
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
app.include_router(students.router, prefix="/api/students", tags=["Students"])
app.include_router(story_arcs.router, prefix="/api/story-arcs", tags=["Story Arcs"])
app.include_router(story_episodes.router, prefix="/api/story-arcs", tags=["Story Episodes"])
app.include_router(hashtag_sets.router, prefix="/api/hashtag-sets", tags=["Hashtag Sets"])
app.include_router(ctas.router, prefix="/api/ctas", tags=["CTAs"])
app.include_router(interactive_elements.router, prefix="/api/posts", tags=["Interactive Elements"])
app.include_router(recycling.router, prefix="/api/recycling", tags=["Content Recycling"])
app.include_router(series_reminders.router, prefix="/api/series-reminders", tags=["Series Reminders"])
app.include_router(video_overlays.router, prefix="/api/video-overlays", tags=["Video Overlays"])
app.include_router(audio_mixer.router, prefix="/api/audio", tags=["Audio Mixer"])
app.include_router(video_composer.router, prefix="/api/video-composer", tags=["Video Composer"])
app.include_router(video_templates.router, prefix="/api/video-templates", tags=["Video Templates"])
app.include_router(video_export.router, prefix="/api/video-export", tags=["Video Export"])
app.include_router(recurring_formats.router, prefix="/api/recurring-formats", tags=["Recurring Formats"])
app.include_router(post_relations.router, prefix="/api/posts", tags=["Post Relations"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
