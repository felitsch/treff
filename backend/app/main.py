"""TREFF Sprachreisen Post-Generator - FastAPI Backend

A comprehensive Social Media Content Tool for TREFF Sprachreisen,
providing AI-powered content generation, template management,
scheduling, analytics, and multi-platform export capabilities.
"""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

import base64

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

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
from app.core.seed_treff_standard_templates import seed_treff_standard_templates
from app.core.seed_recurring_formats import seed_recurring_formats
from app.schemas.responses import ERROR_CODES
from app.api.routes import auth, posts, templates, assets, calendar, suggestions, analytics, settings as settings_router, health, export, slides, ai, students, story_arcs, story_episodes, hashtag_sets, ctas, interactive_elements, recycling, series_reminders, video_overlays, audio_mixer, video_composer, video_templates, video_export, recurring_formats, recurring_posts, post_relations, pipeline, content_strategy, campaigns, template_favorites, video_scripts, prompt_history, smart_scheduling

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
        # Vercel file persistence: store file bytes as base64 in DB
        try:
            await conn.execute(text("ALTER TABLE assets ADD COLUMN file_data TEXT"))
            logger.info("Added file_data column to assets table")
        except Exception:
            pass
        try:
            await conn.execute(text("ALTER TABLE music_tracks ADD COLUMN file_data TEXT"))
            logger.info("Added file_data column to music_tracks table")
        except Exception:
            pass
        try:
            await conn.execute(text("ALTER TABLE video_overlays ADD COLUMN rendered_data TEXT"))
            logger.info("Added rendered_data column to video_overlays table")
        except Exception:
            pass
        try:
            await conn.execute(text("ALTER TABLE content_suggestions ADD COLUMN suggested_format VARCHAR"))
            logger.info("Added suggested_format column to content_suggestions table")
        except Exception:
            pass
        # Recurring posts columns
        try:
            await conn.execute(text("ALTER TABLE posts ADD COLUMN recurring_rule_id INTEGER REFERENCES recurring_post_rules(id) ON DELETE SET NULL"))
            logger.info("Added recurring_rule_id column to posts table")
        except Exception:
            pass
        try:
            await conn.execute(text("ALTER TABLE posts ADD COLUMN is_recurring_instance INTEGER"))
            logger.info("Added is_recurring_instance column to posts table")
        except Exception:
            pass
        # Performance tracking columns
        for col_name in ["perf_likes", "perf_comments", "perf_shares", "perf_saves", "perf_reach"]:
            try:
                await conn.execute(text(f"ALTER TABLE posts ADD COLUMN {col_name} INTEGER"))
                logger.info(f"Added {col_name} column to posts table")
            except Exception:
                pass
        try:
            await conn.execute(text("ALTER TABLE posts ADD COLUMN perf_updated_at DATETIME"))
            logger.info("Added perf_updated_at column to posts table")
        except Exception:
            pass

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

    # Seed TREFF Standard-Templates (10 production-ready templates)
    async with async_session() as session:
        try:
            count = await seed_treff_standard_templates(session)
            if count > 0:
                logger.info(f"Seeded {count} TREFF standard templates")
        except Exception as e:
            logger.error(f"Failed to seed TREFF standard templates: {e}")

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


# ─── OpenAPI Tag Descriptions ───────────────────────────────────────────────
# Organized by functional area for clear API documentation

OPENAPI_TAGS = [
    # --- Core ---
    {
        "name": "Health",
        "description": "Server health checks and database schema inspection. Use `/api/health` to verify the backend is running and the database is connected.",
    },
    {
        "name": "Authentication",
        "description": "User registration, login, token refresh, and profile management. All protected endpoints require a valid JWT Bearer token in the `Authorization` header.",
    },
    {
        "name": "Settings",
        "description": "Application settings (brand colors, API keys, posting goals). Settings are per-user and persisted in the database.",
    },
    # --- Content Creation ---
    {
        "name": "Posts",
        "description": "CRUD operations for social media posts. Supports filtering by category, platform, country, date range, and full-text search. Pagination available via `page` and `limit` query params.",
    },
    {
        "name": "Post Slides",
        "description": "Manage individual slides within a carousel post. Supports reordering, adding, updating, and removing slides.",
    },
    {
        "name": "Templates",
        "description": "HTML/CSS templates for post rendering. Includes system defaults and user-created custom templates. Supports categories, platform formats (1:1, 9:16, 4:5), and country theming.",
    },
    {
        "name": "Template Favorites",
        "description": "Bookmark templates as favorites for quick access during post creation.",
    },
    {
        "name": "Export",
        "description": "Render posts to PNG/PDF images, batch export carousels, and download previously exported files.",
    },
    # --- AI & Generation ---
    {
        "name": "AI Generation",
        "description": "AI-powered content generation using Google Gemini. Includes text generation, image generation/editing, hashtag suggestions, hook/CTA generation, humor formats, caption optimization, weekly planning, and engagement boosting.",
    },
    {
        "name": "AI Prompt History",
        "description": "Track and replay previous AI generation prompts. Supports favoriting prompts and viewing generation statistics.",
    },
    {
        "name": "Smart Scheduling",
        "description": "AI-powered optimal posting time suggestions based on platform, category, and historical engagement data.",
    },
    # --- Assets & Media ---
    {
        "name": "Assets",
        "description": "Upload, crop, trim, and manage media assets (images, videos, audio). Supports stock photo search (Unsplash/Pexels) and import.",
    },
    {
        "name": "Video Overlays",
        "description": "Create and render text/graphic overlays for video content. Supports positioning, styling, and opacity controls.",
    },
    {
        "name": "Video Templates",
        "description": "Intro/outro video branding templates. Apply templates to videos for consistent brand identity.",
    },
    {
        "name": "Video Composer",
        "description": "Compose multi-segment videos from clips, apply transitions, and export in various formats.",
    },
    {
        "name": "Video Export",
        "description": "Export videos in social media aspect ratios (9:16, 1:1, 4:5) with smart cropping, compression, and batch export.",
    },
    {
        "name": "Video Scripts",
        "description": "Generate and manage video scripts for Reels and TikTok. Includes hook formulas and timing templates.",
    },
    {
        "name": "Audio Mixer",
        "description": "Mix background music with video audio. Browse the music library, generate waveforms, and create audio mixes.",
    },
    # --- Calendar & Scheduling ---
    {
        "name": "Calendar",
        "description": "Content calendar with drag-and-drop scheduling. Supports week/month views, gap detection, platform lanes, episode ordering, CSV/iCal/PDF export and import, seasonal markers, and recurring post placeholders.",
    },
    {
        "name": "Suggestions",
        "description": "AI-generated content suggestions based on the current content mix and posting gaps.",
    },
    # --- Analytics ---
    {
        "name": "Analytics",
        "description": "Dashboard analytics: category distribution, platform breakdown, country mix, posting frequency, template usage, content mix balance, and goal tracking.",
    },
    # --- Students & Story Arcs ---
    {
        "name": "Students",
        "description": "Manage exchange students with profiles, countries, personality presets, and individual dashboards.",
    },
    {
        "name": "Story Arcs",
        "description": "Multi-episode story arcs following a student's journey. Supports arc creation wizard, chapter suggestions, and timeline tracking.",
    },
    {
        "name": "Story Episodes",
        "description": "Individual episodes within a story arc. CRUD operations for episodes with ordering and text generation.",
    },
    {
        "name": "Series Reminders",
        "description": "Notification system for story-arc deadlines and upcoming episodes. Tracks read/unread status and supports batch acknowledgment.",
    },
    # --- Content Enrichment ---
    {
        "name": "Hashtag Sets",
        "description": "Predefined and custom hashtag sets organized by theme, country, and campaign. CRUD operations for hashtag management.",
    },
    {
        "name": "CTAs",
        "description": "Call-to-action library with usage tracking. Generate AI-powered CTA suggestions and track which CTAs perform best.",
    },
    {
        "name": "Interactive Elements",
        "description": "Add polls, quizzes, sliders, and Q&A elements to posts for increased engagement.",
    },
    # --- Recurring & Recycling ---
    {
        "name": "Recurring Formats",
        "description": "Define recurring content formats (Motivation Monday, Throwback Thursday, etc.) with schedules and templates.",
    },
    {
        "name": "Recurring Posts",
        "description": "Automate recurring post creation from defined rules. Generate instances, manage schedules, and track recurring series.",
    },
    {
        "name": "Content Recycling",
        "description": "Identify evergreen content for recycling. Get recycling suggestions, calendar placements, and refresh old posts with updated content.",
    },
    # --- Strategy & Campaigns ---
    {
        "name": "Content Strategy",
        "description": "Brand content strategy: content pillars, buyer journey mapping, platform-specific strategies, seasonal planning, competitor analysis, and KPI definitions.",
    },
    {
        "name": "Campaigns",
        "description": "Multi-post marketing campaigns with AI-powered plan generation. CRUD operations for campaigns with post association.",
    },
    {
        "name": "Content Pipeline",
        "description": "Student content inbox and processing pipeline. Analyze media, process items, and multiply content across platforms.",
    },
    {
        "name": "Post Relations",
        "description": "Link related posts together (translations, variations, series). Suggest relations based on content similarity.",
    },
]

app = FastAPI(
    title="TREFF Post-Generator API",
    description="""
## TREFF Sprachreisen - Social Media Content Tool

A comprehensive API for creating, managing, and scheduling social media content
for **TREFF Sprachreisen**, a German provider of high school exchange programs
in the USA, Canada, Australia, New Zealand, and Ireland.

### Key Features

- **AI-Powered Content Generation** - Text, images, hashtags, and CTAs via Google Gemini
- **Template System** - HTML/CSS templates with live preview and country theming
- **Content Calendar** - Drag-and-drop scheduling with gap detection and platform lanes
- **Story Arcs** - Multi-episode student journey narratives
- **Video Tools** - Compose, overlay, export, and brand videos for Reels/TikTok
- **Analytics Dashboard** - Track posting frequency, category mix, and engagement
- **Campaign Management** - Plan and execute multi-post marketing campaigns
- **Content Recycling** - Identify and refresh evergreen content

### Authentication

All endpoints (except `/api/health` and `/api/auth/login|register`) require a valid
JWT Bearer token. Obtain one via `POST /api/auth/login`.

```
Authorization: Bearer <your_access_token>
```

### Standard Response Format

Successful responses return the data directly. Error responses use:

```json
{
    "detail": "Human-readable error message"
}
```

Paginated endpoints return:

```json
{
    "items": [...],
    "total": 42,
    "page": 1,
    "limit": 20,
    "total_pages": 3
}
```

### Rate Limiting

AI generation endpoints are rate-limited to prevent abuse. When rate-limited,
you'll receive a `429 Too Many Requests` response.
""",
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=OPENAPI_TAGS,
    contact={
        "name": "TREFF Sprachreisen",
        "url": "https://www.treff-sprachreisen.de",
    },
    license_info={
        "name": "Proprietary",
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
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

# ─── Custom Exception Handlers ──────────────────────────────────────────────
# All error responses follow the standard format:
# { "detail": "<message>", "error": { "code": "<CODE>", "message": "<msg>", "details": ... } }
# The "detail" field is kept for backward compatibility with the frontend.

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent error format.

    Returns both the standard FastAPI `detail` field (for frontend compatibility)
    and the structured `error` object for new consumers.
    """
    error_code = ERROR_CODES.get(exc.status_code, "ERROR")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "data": None,
            "meta": None,
            "error": {
                "code": error_code,
                "message": str(exc.detail),
                "details": None,
            },
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with meaningful messages.

    - Malformed JSON -> 400 Bad Request
    - Missing/invalid fields -> 422 Unprocessable Entity with field details
    """
    errors = exc.errors()

    # Check if this is a JSON decode error (malformed JSON body)
    for error in errors:
        if error.get("type") == "json_invalid":
            detail_msg = "Bad Request: The request body contains malformed JSON. Please send a valid JSON object."
            return JSONResponse(
                status_code=400,
                content={
                    "detail": detail_msg,
                    "data": None,
                    "meta": None,
                    "error": {
                        "code": "BAD_REQUEST",
                        "message": detail_msg,
                        "details": [
                            {
                                "type": error.get("type"),
                                "message": str(error.get("msg", "Invalid JSON")),
                            }
                        ],
                    },
                },
            )

    # For field validation errors (missing fields, wrong types, etc.) -> 422
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

    detail_msg = "Validation error: One or more fields failed validation."
    return JSONResponse(
        status_code=422,
        content={
            "detail": detail_msg,
            "data": None,
            "meta": None,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": detail_msg,
                "details": field_errors,
            },
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Catch-all for unhandled exceptions. Returns 500 with structured error.

    Logs the full traceback for debugging while returning a safe message to the client.
    """
    logger.exception(f"Unhandled exception on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "data": None,
            "meta": None,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
                "details": None,
            },
        },
    )


# Static files for uploads
if IS_VERCEL:
    # On Vercel, StaticFiles can't serve from /tmp reliably across invocations.
    # Use a catch-all route instead.
    @app.get("/api/uploads/{file_path:path}")
    async def serve_upload_api(file_path: str):
        return await serve_upload(file_path)

    @app.get("/uploads/{file_path:path}")
    async def serve_upload(file_path: str):
        full_path = UPLOADS_DIR / file_path
        if full_path.exists():
            return FileResponse(str(full_path))

        # DB-Fallback: restore file from Turso
        from app.models.asset import Asset
        from app.models.music_track import MusicTrack
        from app.models.video_overlay import VideoOverlay

        filename = file_path.split("/")[-1]
        async with async_session() as session:
            # Search in assets
            result = await session.execute(
                select(Asset.file_data, Asset.file_type).where(Asset.filename == filename)
            )
            row = result.first()
            if row and row.file_data:
                file_bytes = base64.b64decode(row.file_data)
                full_path.parent.mkdir(parents=True, exist_ok=True)
                with open(full_path, "wb") as f:
                    f.write(file_bytes)
                return Response(content=file_bytes, media_type=row.file_type,
                                headers={"Cache-Control": "public, max-age=86400"})

            # Search in music_tracks
            result2 = await session.execute(
                select(MusicTrack.file_data).where(MusicTrack.filename == filename)
            )
            row2 = result2.first()
            if row2 and row2.file_data:
                file_bytes = base64.b64decode(row2.file_data)
                full_path.parent.mkdir(parents=True, exist_ok=True)
                with open(full_path, "wb") as f:
                    f.write(file_bytes)
                return Response(content=file_bytes, media_type="audio/mpeg",
                                headers={"Cache-Control": "public, max-age=86400"})

            # Search in video_overlays (rendered PNGs)
            result3 = await session.execute(
                select(VideoOverlay.rendered_data).where(VideoOverlay.rendered_path.like(f"%{filename}"))
            )
            row3 = result3.first()
            if row3 and row3.rendered_data:
                file_bytes = base64.b64decode(row3.rendered_data)
                full_path.parent.mkdir(parents=True, exist_ok=True)
                with open(full_path, "wb") as f:
                    f.write(file_bytes)
                return Response(content=file_bytes, media_type="image/png",
                                headers={"Cache-Control": "public, max-age=86400"})

        raise HTTPException(status_code=404, detail="File not found")
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
app.include_router(recurring_posts.router, prefix="/api/recurring-posts", tags=["Recurring Posts"])
app.include_router(post_relations.router, prefix="/api/posts", tags=["Post Relations"])
app.include_router(pipeline.router, prefix="/api/pipeline", tags=["Content Pipeline"])
app.include_router(content_strategy.router, prefix="/api/content-strategy", tags=["Content Strategy"])
app.include_router(campaigns.router, prefix="/api/campaigns", tags=["Campaigns"])
app.include_router(template_favorites.router, prefix="/api/template-favorites", tags=["Template Favorites"])
app.include_router(video_scripts.router, prefix="/api/video-scripts", tags=["Video Scripts"])
app.include_router(prompt_history.router, prefix="/api/ai", tags=["AI Prompt History"])
app.include_router(smart_scheduling.router, prefix="/api/ai", tags=["Smart Scheduling"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
