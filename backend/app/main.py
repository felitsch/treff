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
from app.core.seed_content_pillars import seed_content_pillars
from app.core.seed_audio_suggestions import seed_audio_suggestions
from app.schemas.responses import ERROR_CODES
from app.api.routes import auth, posts, templates, assets, calendar, suggestions, analytics, settings as settings_router, health, export, slides, ai, students, story_arcs, story_episodes, hashtag_sets, ctas, interactive_elements, recycling, series_reminders, video_overlays, audio_mixer, video_composer, video_templates, video_export, recurring_formats, recurring_posts, post_relations, pipeline, content_strategy, campaigns, template_favorites, video_scripts, prompt_history, smart_scheduling, tasks, reports, content_pillars, video_thumbnails, config_endpoints, audio_suggestions, shot_lists

logger = logging.getLogger(__name__)

# Resolve uploads directory (Vercel-aware)
UPLOADS_DIR = get_upload_dir()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Startup
    logger.info("Starting TREFF Post-Generator backend...")

    from sqlalchemy import text

    # ── Schema check: skip all DDL if DB is already up to date ──
    # Probe the newest column (assets.marked_unused) — if it exists, the schema
    # is fully migrated and we can skip create_all + all ALTER TABLEs.
    # IMPORTANT: Update this probe whenever a new ALTER TABLE migration is added.
    # It must reference the LAST column in the alter_stmts list below.
    schema_ready = False
    async with engine.begin() as conn:
        try:
            await conn.execute(text("SELECT marked_unused FROM assets LIMIT 0"))
            schema_ready = True
            logger.info("Database schema already up to date — skipping DDL")
        except Exception as exc:
            err_msg = str(exc).lower()
            if "no such column" in err_msg or "no such table" in err_msg:
                schema_ready = False
            else:
                logger.error("Schema probe failed unexpectedly: %s", exc)
                raise

    if not schema_ready:
        # Full schema bootstrap (first deploy or after schema change)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created/verified")

        # ── ALTER TABLE migrations ──
        alter_stmts = [
            "ALTER TABLE assets ADD COLUMN duration_seconds FLOAT",
            "ALTER TABLE assets ADD COLUMN thumbnail_path VARCHAR",
            "ALTER TABLE students ADD COLUMN personality_preset TEXT",
            "ALTER TABLE posts ADD COLUMN story_arc_id INTEGER REFERENCES story_arcs(id)",
            "ALTER TABLE posts ADD COLUMN episode_number INTEGER",
            "ALTER TABLE posts ADD COLUMN linked_post_group_id VARCHAR",
            "ALTER TABLE posts ADD COLUMN student_id INTEGER REFERENCES students(id) ON DELETE SET NULL",
            "ALTER TABLE assets ADD COLUMN file_data TEXT",
            "ALTER TABLE music_tracks ADD COLUMN file_data TEXT",
            "ALTER TABLE video_overlays ADD COLUMN rendered_data TEXT",
            "ALTER TABLE content_suggestions ADD COLUMN suggested_format VARCHAR",
            "ALTER TABLE posts ADD COLUMN recurring_rule_id INTEGER REFERENCES recurring_post_rules(id) ON DELETE SET NULL",
            "ALTER TABLE posts ADD COLUMN is_recurring_instance INTEGER",
            "ALTER TABLE posts ADD COLUMN perf_likes INTEGER",
            "ALTER TABLE posts ADD COLUMN perf_comments INTEGER",
            "ALTER TABLE posts ADD COLUMN perf_shares INTEGER",
            "ALTER TABLE posts ADD COLUMN perf_saves INTEGER",
            "ALTER TABLE posts ADD COLUMN perf_reach INTEGER",
            "ALTER TABLE posts ADD COLUMN perf_updated_at DATETIME",
            "ALTER TABLE posts ADD COLUMN pillar_id VARCHAR",
            "ALTER TABLE posts ADD COLUMN hook_formula VARCHAR(100)",
            "ALTER TABLE assets ADD COLUMN thumbnail_small VARCHAR",
            "ALTER TABLE assets ADD COLUMN thumbnail_medium VARCHAR",
            "ALTER TABLE assets ADD COLUMN thumbnail_large VARCHAR",
            "ALTER TABLE assets ADD COLUMN exif_data TEXT",
            "ALTER TABLE assets ADD COLUMN last_used_at DATETIME",
            "ALTER TABLE assets ADD COLUMN marked_unused INTEGER",
        ]

        if IS_VERCEL:
            # Batch all ALTER TABLEs in a single Turso pipeline request
            from app.core.database import turso_batch_execute
            results = await turso_batch_execute(alter_stmts)
            for stmt, result in zip(alter_stmts, results):
                if result.get("type") == "ok":
                    col_name = stmt.split("ADD COLUMN ")[1].split(" ")[0]
                    logger.info(f"Migration: added {col_name}")
        else:
            # Local: individual execution for clearer error handling
            async with engine.begin() as conn:
                for stmt in alter_stmts:
                    try:
                        await conn.execute(text(stmt))
                        col_name = stmt.split("ADD COLUMN ")[1].split(" ")[0]
                        logger.info(f"Migration: added {col_name}")
                    except Exception:
                        pass  # Column already exists

    # ── Alembic check (local only — useless on Vercel with Turso) ──
    if not IS_VERCEL:
        try:
            from pathlib import Path as _Path
            from alembic.config import Config as _AlembicConfig
            from alembic.script import ScriptDirectory as _ScriptDir
            from alembic.runtime.migration import MigrationContext as _MigCtx
            from sqlalchemy import create_engine as _create_engine
            from sqlalchemy.pool import NullPool as _NullPool

            _backend_dir = _Path(__file__).resolve().parent.parent
            _ini = _backend_dir / "alembic.ini"
            if _ini.exists():
                _cfg = _AlembicConfig(str(_ini))
                _cfg.set_main_option("script_location", str(_backend_dir / "migrations"))
                _script = _ScriptDir.from_config(_cfg)
                _head = _script.get_current_head()
                _db_path = str(_backend_dir / "treff.db")
                _eng = _create_engine(f"sqlite:///{_db_path}", poolclass=_NullPool)
                with _eng.connect() as _conn:
                    _ctx = _MigCtx.configure(_conn)
                    _current = _ctx.get_current_revision()
                _eng.dispose()
                if _current == _head:
                    logger.info("Alembic migrations: up to date (revision %s)", _current)
                elif _current is None:
                    logger.warning("Alembic migrations: no revision stamped yet. Run 'python migrate.py stamp head'")
                else:
                    logger.warning("Alembic migrations: PENDING! Current=%s, Head=%s. Run 'python migrate.py upgrade'", _current, _head)
        except ImportError:
            pass  # Alembic not installed, skip check
        except Exception as e:
            logger.debug("Alembic migration check skipped: %s", e)

    # ── Seed data (single session for all seeds) ──
    SEED_FUNCTIONS = [
        (seed_default_users, "default user(s)"),
        (seed_default_templates, "default templates"),
        (seed_story_teaser_templates, "story-teaser templates"),
        (seed_story_series_templates, "story-series templates"),
        (seed_treff_standard_templates, "TREFF standard templates"),
        (seed_default_suggestions, "content suggestions"),
        (seed_humor_formats, "humor formats"),
        (seed_hashtag_sets, "hashtag sets"),
        (seed_default_ctas, "CTAs"),
        (seed_music_tracks, "music tracks"),
        (seed_video_templates, "video templates"),
        (seed_recurring_formats, "recurring formats"),
        (seed_content_pillars, "content pillars"),
        (seed_audio_suggestions, "audio suggestions"),
    ]

    async with async_session() as session:
        for seed_fn, label in SEED_FUNCTIONS:
            try:
                count = await seed_fn(session)
                if count > 0:
                    logger.info(f"Seeded {count} {label}")
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to seed {label}: {e}")

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
        "name": "Content Pillars",
        "description": "Content pillar management: CRUD for thematic content categories (e.g., Erfahrungsberichte, Laender-Spotlights), distribution tracking against target percentages, and seed endpoint.",
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
    {
        "name": "Background Tasks",
        "description": "Monitor and manage long-running background operations. Query task status, view history, cancel running tasks, and receive progress updates.",
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
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset", "Retry-After"],
)

# Rate-limiting middleware (applied after CORS so preflight OPTIONS are not limited)
from app.core.rate_limiter import RateLimitMiddleware  # noqa: E402
app.add_middleware(RateLimitMiddleware)

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
app.include_router(video_thumbnails.router, prefix="/api/video/thumbnails", tags=["Video Thumbnails"])
app.include_router(recurring_formats.router, prefix="/api/recurring-formats", tags=["Recurring Formats"])
app.include_router(recurring_posts.router, prefix="/api/recurring-posts", tags=["Recurring Posts"])
app.include_router(post_relations.router, prefix="/api/posts", tags=["Post Relations"])
app.include_router(pipeline.router, prefix="/api/pipeline", tags=["Content Pipeline"])
app.include_router(content_strategy.router, prefix="/api/content-strategy", tags=["Content Strategy"])
app.include_router(campaigns.router, prefix="/api/campaigns", tags=["Campaigns"])
app.include_router(template_favorites.router, prefix="/api/template-favorites", tags=["Template Favorites"])
app.include_router(video_scripts.router, prefix="/api/video-scripts", tags=["Video Scripts"])
app.include_router(audio_suggestions.router, prefix="/api/audio-suggestions", tags=["Audio Suggestions"])
app.include_router(prompt_history.router, prefix="/api/ai", tags=["AI Prompt History"])
app.include_router(smart_scheduling.router, prefix="/api/ai", tags=["Smart Scheduling"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["Background Tasks"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(content_pillars.router, prefix="/api/content-pillars", tags=["Content Pillars"])
app.include_router(config_endpoints.router, prefix="/api/config", tags=["Config"])
app.include_router(shot_lists.router, prefix="/api/shot-lists", tags=["Shot Lists"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
