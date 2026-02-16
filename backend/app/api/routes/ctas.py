from __future__ import annotations

"""CTA (Call-to-Action) library CRUD routes."""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.cta import CTA

router = APIRouter()
logger = logging.getLogger(__name__)

VALID_CATEGORIES = ["engagement", "conversion", "awareness", "traffic"]
VALID_PLATFORMS = ["instagram", "tiktok", "both"]
VALID_FORMATS = ["feed", "story", "reel", "all"]


def cta_to_dict(cta: CTA) -> dict:
    """Convert CTA model to dict."""
    return {
        "id": cta.id,
        "text": cta.text,
        "category": cta.category,
        "platform": cta.platform,
        "format": cta.format,
        "emoji": cta.emoji,
        "performance_score": cta.performance_score,
        "usage_count": cta.usage_count,
        "is_default": bool(cta.is_default),
        "created_at": cta.created_at.isoformat() if cta.created_at else None,
    }


@router.get("")
async def list_ctas(
    category: Optional[str] = None,
    platform: Optional[str] = None,
    format: Optional[str] = None,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List all CTAs with optional filtering by category, platform, and format.

    Query params:
    - category: engagement, conversion, awareness, traffic
    - platform: instagram, tiktok, both
    - format: feed, story, reel, all
    """
    query = select(CTA).order_by(CTA.usage_count.desc(), CTA.id)

    if category and category in VALID_CATEGORIES:
        query = query.where(CTA.category == category)

    if platform and platform in VALID_PLATFORMS:
        # "both" matches the specific platform AND "both"
        query = query.where((CTA.platform == platform) | (CTA.platform == "both"))

    if format and format in VALID_FORMATS:
        # "all" matches the specific format AND "all"
        query = query.where((CTA.format == format) | (CTA.format == "all"))

    result = await db.execute(query)
    ctas = result.scalars().all()

    return {
        "ctas": [cta_to_dict(c) for c in ctas],
        "total": len(ctas),
    }


@router.get("/{cta_id}")
async def get_cta(
    cta_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a single CTA by ID."""
    result = await db.execute(select(CTA).where(CTA.id == cta_id))
    cta = result.scalar_one_or_none()
    if not cta:
        raise HTTPException(status_code=404, detail="CTA not found")
    return cta_to_dict(cta)


@router.post("")
async def create_cta(
    request: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a new CTA.

    Expects:
    - text (str, required): CTA text
    - category (str, required): engagement, conversion, awareness, traffic
    - platform (str, optional): instagram, tiktok, both (default: both)
    - format (str, optional): feed, story, reel, all (default: all)
    - emoji (str, optional): Emoji for visual display
    """
    text = request.get("text", "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="CTA text is required")

    category = request.get("category", "").strip()
    if category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Must be one of: {', '.join(VALID_CATEGORIES)}"
        )

    platform = request.get("platform", "both").strip()
    if platform not in VALID_PLATFORMS:
        platform = "both"

    fmt = request.get("format", "all").strip()
    if fmt not in VALID_FORMATS:
        fmt = "all"

    emoji = request.get("emoji", "").strip() or None

    cta = CTA(
        text=text,
        category=category,
        platform=platform,
        format=fmt,
        emoji=emoji,
        performance_score=0.0,
        usage_count=0,
        is_default=0,
    )
    db.add(cta)
    await db.flush()
    await db.refresh(cta)

    return cta_to_dict(cta)


@router.put("/{cta_id}")
async def update_cta(
    cta_id: int,
    request: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing CTA.

    All fields are optional - only provided fields are updated.
    """
    result = await db.execute(select(CTA).where(CTA.id == cta_id))
    cta = result.scalar_one_or_none()
    if not cta:
        raise HTTPException(status_code=404, detail="CTA not found")

    if "text" in request:
        text = request["text"].strip()
        if not text:
            raise HTTPException(status_code=400, detail="CTA text cannot be empty")
        cta.text = text

    if "category" in request:
        category = request["category"].strip()
        if category not in VALID_CATEGORIES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category. Must be one of: {', '.join(VALID_CATEGORIES)}"
            )
        cta.category = category

    if "platform" in request:
        platform = request["platform"].strip()
        if platform in VALID_PLATFORMS:
            cta.platform = platform

    if "format" in request:
        fmt = request["format"].strip()
        if fmt in VALID_FORMATS:
            cta.format = fmt

    if "emoji" in request:
        cta.emoji = request["emoji"].strip() or None

    await db.flush()
    await db.refresh(cta)

    return cta_to_dict(cta)


@router.delete("/{cta_id}")
async def delete_cta(
    cta_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a CTA."""
    result = await db.execute(select(CTA).where(CTA.id == cta_id))
    cta = result.scalar_one_or_none()
    if not cta:
        raise HTTPException(status_code=404, detail="CTA not found")

    await db.delete(cta)
    return {"status": "success", "message": f"CTA '{cta.text}' deleted"}


@router.post("/{cta_id}/use")
async def record_cta_usage(
    cta_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Record that a CTA was used in a post (increments usage_count).

    Called when a user selects a CTA from the library for their post.
    """
    result = await db.execute(select(CTA).where(CTA.id == cta_id))
    cta = result.scalar_one_or_none()
    if not cta:
        raise HTTPException(status_code=404, detail="CTA not found")

    cta.usage_count = (cta.usage_count or 0) + 1
    await db.flush()
    await db.refresh(cta)

    return cta_to_dict(cta)


@router.post("/suggest")
async def suggest_ctas(
    request: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Auto-suggest CTAs based on post content and context.

    Uses category, platform, format, and optional topic to find the most
    relevant CTAs from the library. Returns top 5 suggestions sorted by
    relevance (matching filters + usage popularity).

    Expects:
    - category (str, optional): Post category (e.g. laender_spotlight, fristen_cta)
    - platform (str, optional): Target platform (instagram_feed, instagram_story, tiktok)
    - format (str, optional): Post format (feed, story, reel)
    - topic (str, optional): Post topic for context-based filtering
    """
    post_category = request.get("category", "")
    platform = request.get("platform", "")
    fmt = request.get("format", "")
    topic = request.get("topic", "")

    # Map post category to CTA categories
    # fristen_cta, conversion-oriented categories → conversion CTAs
    # erfahrungsberichte, foto_posts → engagement CTAs
    # laender_spotlight, infografiken → awareness CTAs
    # tipps_tricks → traffic CTAs
    cta_category_map = {
        "fristen_cta": "conversion",
        "erfahrungsberichte": "engagement",
        "foto_posts": "engagement",
        "laender_spotlight": "awareness",
        "infografiken": "awareness",
        "tipps_tricks": "traffic",
        "faq": "awareness",
        "reel_tiktok_thumbnails": "engagement",
        "story_posts": "traffic",
    }
    suggested_cta_category = cta_category_map.get(post_category, None)

    # Map platform to CTA platform filter
    platform_map = {
        "instagram_feed": "instagram",
        "instagram_story": "instagram",
        "instagram_stories": "instagram",
        "instagram_reels": "instagram",
        "tiktok": "tiktok",
    }
    cta_platform = platform_map.get(platform, None)

    # Map platform to CTA format filter
    format_map = {
        "instagram_feed": "feed",
        "instagram_story": "story",
        "instagram_stories": "story",
        "instagram_reels": "reel",
        "tiktok": "reel",
    }
    cta_format = format_map.get(platform, None)

    # Build query: get matching CTAs, prioritize by category match + usage_count
    query = select(CTA).order_by(CTA.usage_count.desc(), CTA.id)

    # Filter by platform compatibility
    if cta_platform:
        query = query.where((CTA.platform == cta_platform) | (CTA.platform == "both"))

    # Filter by format compatibility
    if cta_format:
        query = query.where((CTA.format == cta_format) | (CTA.format == "all"))

    result = await db.execute(query)
    all_matching = result.scalars().all()

    # Score and rank results
    scored = []
    for cta in all_matching:
        score = 0
        # Category match gives highest priority
        if suggested_cta_category and cta.category == suggested_cta_category:
            score += 100
        # Popular CTAs get a bonus
        score += min(cta.usage_count or 0, 50)
        # Performance score bonus
        score += (cta.performance_score or 0) * 10
        scored.append((score, cta))

    # Sort by score descending, take top 5
    scored.sort(key=lambda x: x[0], reverse=True)
    top_ctas = [cta_to_dict(item[1]) for _, item in zip(range(5), scored)] if scored else []

    return {
        "suggestions": top_ctas,
        "total": len(top_ctas),
        "context": {
            "post_category": post_category,
            "suggested_cta_category": suggested_cta_category,
            "platform": cta_platform,
            "format": cta_format,
        },
    }
