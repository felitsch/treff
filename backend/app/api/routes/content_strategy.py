"""Content Strategy API routes.

Serves the TREFF Sprachreisen content strategy as structured JSON.
This is the foundation for all AI-powered content features — the strategy
defines content pillars, buyer journey mapping, seasonal calendar, and
platform-specific guidelines.

Also serves the social-content strategy (hook formulas, posting times,
engagement strategies, content repurposing, viral patterns).
"""

import json
import logging
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends
from app.core.security import get_current_user_id

router = APIRouter()
logger = logging.getLogger(__name__)

# Load the content strategy JSON at module level
_STRATEGY_PATH = Path(__file__).resolve().parent.parent.parent.parent.parent / "frontend" / "src" / "config" / "content-strategy.json"
_strategy_data = None

# Load the social content strategy JSON at module level
_SOCIAL_STRATEGY_PATH = Path(__file__).resolve().parent.parent.parent.parent.parent / "frontend" / "src" / "config" / "social-content.json"
_social_strategy_data = None


def _load_strategy() -> dict:
    """Load and cache the content strategy JSON."""
    global _strategy_data
    if _strategy_data is None:
        try:
            with open(_STRATEGY_PATH, "r", encoding="utf-8") as f:
                _strategy_data = json.load(f)
            logger.info("Content strategy loaded from %s", _STRATEGY_PATH)
        except FileNotFoundError:
            logger.error("Content strategy file not found at %s", _STRATEGY_PATH)
            _strategy_data = {"error": "Content strategy file not found"}
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in content strategy: %s", e)
            _strategy_data = {"error": "Invalid content strategy JSON"}
    return _strategy_data


def _load_social_strategy() -> dict:
    """Load and cache the social content strategy JSON."""
    global _social_strategy_data
    if _social_strategy_data is None:
        try:
            with open(_SOCIAL_STRATEGY_PATH, "r", encoding="utf-8") as f:
                _social_strategy_data = json.load(f)
            logger.info("Social content strategy loaded from %s", _SOCIAL_STRATEGY_PATH)
        except FileNotFoundError:
            logger.error("Social content strategy file not found at %s", _SOCIAL_STRATEGY_PATH)
            _social_strategy_data = {"error": "Social content strategy file not found"}
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in social content strategy: %s", e)
            _social_strategy_data = {"error": "Invalid social content strategy JSON"}
    return _social_strategy_data


@router.get("")
async def get_content_strategy(user_id: int = Depends(get_current_user_id)):
    """Get the full content strategy.

    Returns the complete content strategy document as JSON, including:
    - Brand identity and tone of voice
    - Target audience profiles
    - Content pillars with distribution percentages
    - Buyer journey mapping
    - Content calendar framework
    - Hub-and-Spoke structure
    - Competitor analysis
    - Platform strategies
    - KPI targets
    """
    return _load_strategy()


@router.get("/pillars")
async def get_content_pillars(user_id: int = Depends(get_current_user_id)):
    """Get content pillars with distribution percentages.

    Returns just the content pillars section — useful for the AI text generator
    and weekly planner to determine content mix.
    """
    strategy = _load_strategy()
    return {
        "pillars": strategy.get("content_pillars", []),
        "total_percent": sum(p.get("distribution_percent", 0) for p in strategy.get("content_pillars", [])),
    }


@router.get("/buyer-journey")
async def get_buyer_journey(user_id: int = Depends(get_current_user_id)):
    """Get buyer journey stages.

    Returns the buyer journey mapping — awareness, consideration, decision —
    with associated content types and metrics.
    """
    strategy = _load_strategy()
    return strategy.get("buyer_journey", {})


@router.get("/seasonal")
async def get_seasonal_strategy(user_id: int = Depends(get_current_user_id)):
    """Get current seasonal strategy.

    Returns the seasonal strategy phase for the current month,
    including priority pillars, key events, and content mix ratios.
    """
    strategy = _load_strategy()
    calendar = strategy.get("content_calendar", {})
    seasonal = calendar.get("seasonal_strategy", {})
    phases = seasonal.get("phases", [])

    # Determine current phase based on current month
    current_month = date.today().month
    current_phase = None
    for phase in phases:
        if current_month in phase.get("months", []):
            current_phase = phase
            break

    return {
        "current_month": current_month,
        "current_phase": current_phase,
        "all_phases": phases,
        "weekly_rhythm": calendar.get("weekly_rhythm", []),
        "posting_frequency": calendar.get("posting_frequency", {}),
        "best_posting_times": calendar.get("best_posting_times", {}),
        "country_rotation": calendar.get("country_rotation", {}),
    }


@router.get("/competitors")
async def get_competitor_analysis(user_id: int = Depends(get_current_user_id)):
    """Get competitor analysis.

    Returns analysis of competing organizations and TREFF's positioning.
    """
    strategy = _load_strategy()
    return strategy.get("competitor_analysis", {})


@router.get("/hub-and-spoke")
async def get_hub_and_spoke(user_id: int = Depends(get_current_user_id)):
    """Get hub-and-spoke content structure.

    Returns the evergreen hub content pieces and spoke content types
    for the content calendar and AI planner.
    """
    strategy = _load_strategy()
    return strategy.get("hub_and_spoke", {})


@router.get("/platform/{platform}")
async def get_platform_strategy(
    platform: str,
    user_id: int = Depends(get_current_user_id),
):
    """Get platform-specific strategy.

    Args:
        platform: 'instagram' or 'tiktok'

    Returns format distribution, best practices, and hashtag strategy
    for the specified platform.
    """
    strategy = _load_strategy()
    platform_strategies = strategy.get("platform_strategy", {})

    if platform not in platform_strategies:
        return {"error": f"Unknown platform: {platform}. Use 'instagram' or 'tiktok'."}

    return platform_strategies[platform]


@router.get("/kpis")
async def get_kpi_targets(user_id: int = Depends(get_current_user_id)):
    """Get KPI targets.

    Returns follower growth targets, engagement rate goals,
    and other performance metrics for tracking progress.
    """
    strategy = _load_strategy()
    return strategy.get("kpi_targets", {})


@router.get("/tone-of-voice")
async def get_tone_of_voice(user_id: int = Depends(get_current_user_id)):
    """Get tone of voice guidelines.

    Returns the brand's tone of voice rules — do's and don'ts
    for content creation. Used by the AI text generator.
    """
    strategy = _load_strategy()
    brand = strategy.get("brand", {})
    return brand.get("tone_of_voice", {})


# ═══════════════════════════════════════════════════════════════════════
# Social Content Strategy Endpoints (social-content.json)
# ═══════════════════════════════════════════════════════════════════════


@router.get("/social-strategy")
async def get_social_strategy(user_id: int = Depends(get_current_user_id)):
    """Get the full social content strategy.

    Returns the complete social content strategy including:
    - Platform-specific posting frequencies and optimal times
    - Hook formulas for attention-grabbing openers
    - Content repurposing workflows
    - Engagement strategies and CTAs
    - Viral content patterns
    - Hashtag strategy
    - Content calendar rules
    """
    return _load_social_strategy()


@router.get("/social-strategy/platforms")
async def get_social_platforms(user_id: int = Depends(get_current_user_id)):
    """Get platform-specific strategies (frequencies, times, best practices).

    Returns posting frequency, optimal times, content types, and best practices
    for Instagram Feed, Stories, Reels, and TikTok.
    """
    social = _load_social_strategy()
    return social.get("platforms", {})


@router.get("/social-strategy/platforms/{platform}")
async def get_social_platform_detail(
    platform: str,
    user_id: int = Depends(get_current_user_id),
):
    """Get strategy for a specific social platform.

    Args:
        platform: 'instagram_feed', 'instagram_stories', 'instagram_reels', or 'tiktok'
    """
    social = _load_social_strategy()
    platforms = social.get("platforms", {})
    if platform not in platforms:
        valid = list(platforms.keys())
        return {"error": f"Unknown platform: {platform}. Valid: {valid}"}
    return platforms[platform]


@router.get("/social-strategy/hooks")
async def get_hook_formulas(user_id: int = Depends(get_current_user_id)):
    """Get hook formulas for attention-grabbing post openers.

    Returns proven hook templates with examples, platform suitability,
    and effectiveness ratings. Used by the AI text generator to create
    compelling first lines and video intros.
    """
    social = _load_social_strategy()
    return social.get("hook_formulas", {})


@router.get("/social-strategy/repurposing")
async def get_content_repurposing(user_id: int = Depends(get_current_user_id)):
    """Get content repurposing workflows.

    Returns transformation rules for adapting content between platforms:
    - Instagram Feed -> Stories, TikTok
    - Reels -> TikTok
    - Experience reports -> Carousel, TikTok
    Each workflow includes effort level (niedrig/mittel/hoch).
    """
    social = _load_social_strategy()
    return social.get("content_repurposing", {})


@router.get("/social-strategy/engagement")
async def get_engagement_strategies(user_id: int = Depends(get_current_user_id)):
    """Get engagement strategies and CTA types.

    Returns CTA strategy types (question, poll, save, share, ugc, dm, link_in_bio)
    with examples and platform suitability, plus community building tips.
    """
    social = _load_social_strategy()
    return social.get("engagement_strategies", {})


@router.get("/social-strategy/viral-patterns")
async def get_viral_patterns(user_id: int = Depends(get_current_user_id)):
    """Get viral content patterns adapted for TREFF.

    Returns proven viral content formats from the education/travel space,
    adapted for TREFF's target audience and brand.
    """
    social = _load_social_strategy()
    return social.get("viral_patterns", {})


@router.get("/social-strategy/hashtags")
async def get_hashtag_strategy(user_id: int = Depends(get_current_user_id)):
    """Get the hashtag strategy document.

    Returns brand hashtags, niche hashtags, country-specific hashtags,
    and usage rules for Instagram and TikTok.
    """
    social = _load_social_strategy()
    return social.get("hashtag_strategy", {})


@router.get("/social-strategy/posting-times")
async def get_optimal_posting_times(user_id: int = Depends(get_current_user_id)):
    """Get optimal posting times for all platforms.

    Returns the best posting times for the German teenager target audience,
    organized by platform and day type (weekday vs weekend).
    Used by the Smart-Scheduler and Weekly Planner.
    """
    social = _load_social_strategy()
    platforms = social.get("platforms", {})
    times = {}
    for key, platform_data in platforms.items():
        times[key] = {
            "name": platform_data.get("name", key),
            "optimal_posting_times": platform_data.get("optimal_posting_times", {}),
            "posting_frequency": platform_data.get("posting_frequency", {}),
        }
    return times


@router.get("/social-strategy/calendar-rules")
async def get_calendar_rules(user_id: int = Depends(get_current_user_id)):
    """Get content calendar rules for the weekly planner.

    Returns weekly mix rules, seasonal priorities, and recurring content slots
    used by the Wochenplan-Generator to create balanced content plans.
    """
    social = _load_social_strategy()
    return social.get("content_calendar_rules", {})
