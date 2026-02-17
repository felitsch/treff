"""Config API routes — Posting Strategy, Hook Formulas, Hashtag Sets.

Serves the frontend config files as structured JSON via authenticated API endpoints.
These are the centralized configs that Smart-Scheduler, AI Text Generator,
and Hashtag Manager access.

Endpoints:
    GET /api/config/posting-strategy      — Platform-specific posting rules
    GET /api/config/hook-formulas         — Hook formula templates for AI text gen
    GET /api/config/hashtag-sets          — Predefined hashtag groups (brand, country, niche)

All data originates from the frontend/src/config/ JS modules but is also
available via these API endpoints for backend consumers and potential
future mobile clients.
"""

import json
import logging
from pathlib import Path

from fastapi import APIRouter, Depends
from app.core.security import get_current_user_id

router = APIRouter()
logger = logging.getLogger(__name__)

# Locate config files (frontend/src/config/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
_SOCIAL_CONTENT_PATH = _PROJECT_ROOT / "frontend" / "src" / "config" / "social-content.json"

# Cache
_social_content_cache = None


def _load_social_content() -> dict:
    """Load and cache social-content.json."""
    global _social_content_cache
    if _social_content_cache is None:
        try:
            with open(_SOCIAL_CONTENT_PATH, "r", encoding="utf-8") as f:
                _social_content_cache = json.load(f)
            logger.info("Config: Loaded social-content.json")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error("Config: Failed to load social-content.json: %s", e)
            _social_content_cache = {}
    return _social_content_cache


# ═══════════════════════════════════════════════════════════════════
# GET /api/config/posting-strategy
# ═══════════════════════════════════════════════════════════════════

@router.get("/posting-strategy")
async def get_posting_strategy(user_id: int = Depends(get_current_user_id)):
    """Get platform-specific posting strategy configuration.

    Returns posting frequency, optimal times, content formats, caption rules,
    and best practices for each platform (Instagram Feed, Stories, Reels, TikTok).

    Used by:
    - SmartScheduler (recommended times)
    - Weekly Planner (posting frequency limits)
    - Post Creation Wizard (content format suggestions)
    """
    social = _load_social_content()
    platforms = social.get("platforms", {})

    # Transform to structured posting strategy format
    strategy = {}
    for platform_id, platform_data in platforms.items():
        posting_freq = platform_data.get("posting_frequency", {})
        posting_times = platform_data.get("optimal_posting_times", {})

        strategy[platform_id] = {
            "name": platform_data.get("name", platform_id),
            "postingFrequency": {
                "minPerWeek": posting_freq.get("min_per_week", 1),
                "maxPerWeek": posting_freq.get("max_per_week", 7),
                "idealPerWeek": posting_freq.get("ideal_per_week", 3),
                "description": posting_freq.get("description", ""),
            },
            "bestTimes": {
                "weekday": posting_times.get("weekday", []),
                "weekend": posting_times.get("weekend", []),
                "bestDays": posting_times.get("best_days", []),
                "description": posting_times.get("description", ""),
            },
            "maxPostsPerDay": _get_max_per_day(platform_id),
            "contentFormats": platform_data.get("content_types", []),
            "captionRules": platform_data.get("caption_rules", {}),
            "bestPractices": platform_data.get("best_practices", []),
        }

        # Add duration info for video platforms
        if "duration" in platform_data:
            strategy[platform_id]["duration"] = platform_data["duration"]

    return {
        "platforms": strategy,
        "rules": [
            "Immer mindestens 1 Brand-Hashtag verwenden (#TREFFSprachreisen)",
            "Mix aus grossen und kleinen Hashtags",
            "Hashtags rotieren — nicht immer die gleichen verwenden",
        ],
    }


def _get_max_per_day(platform_id: str) -> int:
    """Get max posts per day for a platform."""
    limits = {
        "instagram_feed": 1,
        "instagram_stories": 3,
        "instagram_reels": 2,
        "tiktok": 2,
    }
    return limits.get(platform_id, 1)


# ═══════════════════════════════════════════════════════════════════
# GET /api/config/hook-formulas
# ═══════════════════════════════════════════════════════════════════

@router.get("/hook-formulas")
async def get_hook_formulas(
    platform: str | None = None,
    user_id: int = Depends(get_current_user_id),
):
    """Get hook formula templates for AI text generation.

    Returns proven hook formulas with templates, examples, platform suitability,
    and effectiveness ratings.

    Args:
        platform: Optional filter by platform (instagram_feed, instagram_reels, tiktok, etc.)

    Used by:
    - AI Text Generator (hook suggestions in generated text)
    - Post Creation Wizard (hook selection in Step 4)
    - Strategy Loader (AI prompt enrichment)
    """
    social = _load_social_content()
    hook_data = social.get("hook_formulas", {})
    formulas = hook_data.get("formulas", [])

    # Enrich with category info
    categories = {
        "knowledge_gap": "curiosity",
        "comparison": "comparison",
        "myth_buster": "curiosity",
        "pov": "emotion",
        "list": "list",
        "question": "curiosity",
        "expectation_reality": "comparison",
        "emotional_opener": "emotion",
        "countdown_urgency": "urgency",
        "behind_scenes": "curiosity",
    }

    enriched = []
    for formula in formulas:
        f = {**formula}
        f["category"] = categories.get(formula.get("id", ""), "curiosity")
        enriched.append(f)

    # Apply platform filter
    if platform:
        enriched = [f for f in enriched if platform in f.get("platforms", [])]

    # Sort by effectiveness (highest first)
    enriched.sort(key=lambda f: f.get("effectiveness", 0), reverse=True)

    return {
        "description": hook_data.get("description", ""),
        "formulas": enriched,
        "total": len(enriched),
        "categories": ["curiosity", "emotion", "urgency", "comparison", "list"],
    }


# ═══════════════════════════════════════════════════════════════════
# GET /api/config/hashtag-sets
# ═══════════════════════════════════════════════════════════════════

@router.get("/hashtag-sets")
async def get_hashtag_sets(
    country: str | None = None,
    user_id: int = Depends(get_current_user_id),
):
    """Get predefined hashtag groups (brand, country, niche, trending).

    Returns structured hashtag sets organized by brand, niche topics,
    and country. Also includes usage rules and platform limits.

    Args:
        country: Optional filter to include country-specific hashtags (usa, kanada, australien, neuseeland, irland)

    Used by:
    - Hashtag Manager (load predefined sets)
    - AI Hashtag Suggestion (combine with AI-generated tags)
    - Post Creation Wizard (quick hashtag selection)
    """
    social = _load_social_content()
    hashtag_data = social.get("hashtag_strategy", {})

    brand = hashtag_data.get("brand_hashtags", {})
    niche = hashtag_data.get("niche_hashtags", {})
    country_tags = hashtag_data.get("country_hashtags", {})
    rules = hashtag_data.get("rules", [])

    result = {
        "brand": brand,
        "niche": niche,
        "country": country_tags,
        "rules": rules,
        "platformLimits": {
            "instagram_feed": {"min": 5, "max": 30, "ideal": 10},
            "instagram_stories": {"min": 0, "max": 10, "ideal": 3},
            "instagram_reels": {"min": 3, "max": 30, "ideal": 7},
            "tiktok": {"min": 3, "max": 10, "ideal": 5},
        },
    }

    # If country filter, also include a ready-to-use set
    if country and country in country_tags:
        primary_brand = brand.get("primary", ["#TREFFSprachreisen"])
        country_set = country_tags[country]
        result["recommended"] = {
            "hashtags": primary_brand[:2] + country_set[:5],
            "country": country,
            "description": f"Empfohlenes Set fuer {country.title()}-Content",
        }

    return result
