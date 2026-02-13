"""Content recycling routes - detect evergreen/recyclable posts and suggest refreshed versions."""

from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.post import Post

router = APIRouter()

# Categories considered "evergreen" (timeless content that can be reused)
EVERGREEN_CATEGORIES = {
    "faq",
    "tipps_tricks",
    "laender_spotlight",
    "infografiken",
}

# All categories (non-evergreen can still be recycled, but with lower score)
ALL_CATEGORIES = {
    "laender_spotlight",
    "erfahrungsberichte",
    "infografiken",
    "fristen_cta",
    "tipps_tricks",
    "faq",
    "foto_posts",
    "reel_tiktok_thumbnails",
    "story_posts",
}

# Category display names (German)
CATEGORY_LABELS = {
    "laender_spotlight": "Laender-Spotlight",
    "erfahrungsberichte": "Erfahrungsbericht",
    "infografiken": "Infografik",
    "fristen_cta": "Fristen/CTA",
    "tipps_tricks": "Tipps & Tricks",
    "faq": "FAQ",
    "foto_posts": "Foto-Post",
    "reel_tiktok_thumbnails": "Reel/TikTok",
    "story_posts": "Story",
}


def _calculate_recycle_score(post: Post, days_old: int) -> int:
    """Calculate a recycling score (0-100) based on post attributes.

    Factors:
    - Evergreen category: +40 points
    - Age (older = more suitable): +20 max
    - Has been posted/exported (proven content): +20 points
    - Has country content (reusable for different audience): +10 points
    - Has caption content (richer content): +10 points
    """
    score = 0

    # Evergreen category bonus
    if post.category in EVERGREEN_CATEGORIES:
        score += 40

    # Age bonus (max 20 points for 180+ days old)
    age_score = min(20, int((days_old - 90) / 4.5))
    score += max(0, age_score)

    # Proven content bonus (was actually posted/exported)
    if post.status in ("posted", "exported"):
        score += 20

    # Country content bonus
    if post.country:
        score += 10

    # Rich content bonus (has caption)
    if post.caption_instagram or post.caption_tiktok:
        score += 10

    return min(100, score)


def _post_to_recycling_dict(post: Post, days_old: int, score: int) -> dict:
    """Convert a Post to a recycling suggestion dict."""
    return {
        "id": post.id,
        "title": post.title,
        "category": post.category,
        "category_label": CATEGORY_LABELS.get(post.category, post.category),
        "country": post.country,
        "platform": post.platform,
        "status": post.status,
        "tone": post.tone,
        "cta_text": post.cta_text,
        "slide_data": post.slide_data,
        "caption_instagram": post.caption_instagram,
        "caption_tiktok": post.caption_tiktok,
        "hashtags_instagram": post.hashtags_instagram,
        "hashtags_tiktok": post.hashtags_tiktok,
        "is_evergreen": post.category in EVERGREEN_CATEGORIES,
        "days_old": days_old,
        "recycle_score": score,
        "created_at": post.created_at.isoformat() if post.created_at else None,
        "posted_at": post.posted_at.isoformat() if post.posted_at else None,
        "reason": _build_reason(post, days_old),
    }


def _build_reason(post: Post, days_old: int) -> str:
    """Build a German-language reason for why this post is recyclable."""
    parts = []

    if post.category in EVERGREEN_CATEGORIES:
        parts.append("Evergreen-Content (zeitloses Thema)")
    else:
        parts.append("Aelterer Post mit Wiederverwendungspotenzial")

    months = days_old // 30
    if months >= 6:
        parts.append(f"Vor {months} Monaten erstellt")
    else:
        parts.append(f"Vor {days_old} Tagen erstellt")

    if post.status in ("posted", "exported"):
        parts.append("Bereits erfolgreich veroeffentlicht")

    return " - ".join(parts)


def _get_now_naive():
    """Get current UTC datetime without timezone info (for SQLite compatibility)."""
    return datetime.utcnow()


@router.get("")
async def get_recyclable_posts(
    min_age_days: int = Query(default=90, ge=1, le=730, description="Minimum age in days"),
    category: Optional[str] = None,
    evergreen_only: bool = Query(default=False, description="Only return evergreen categories"),
    limit: int = Query(default=10, ge=1, le=50),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get posts eligible for content recycling.

    Scans posts older than min_age_days and ranks them by recycling potential.
    Evergreen content (FAQs, Tipps, Laender-Spotlights) gets higher scores.
    """
    now = _get_now_naive()
    cutoff = now - timedelta(days=min_age_days)

    filters = [
        Post.user_id == user_id,
        Post.created_at <= cutoff,
    ]

    if category:
        filters.append(Post.category == category)

    if evergreen_only:
        filters.append(Post.category.in_(EVERGREEN_CATEGORIES))

    result = await db.execute(
        select(Post).where(*filters).order_by(Post.created_at.asc())
    )
    posts = result.scalars().all()

    # Score and sort by recycling potential
    scored_posts = []
    for post in posts:
        if post.created_at:
            # Ensure naive datetime for comparison
            post_created = post.created_at.replace(tzinfo=None) if post.created_at.tzinfo else post.created_at
            days_old = (now - post_created).days
        else:
            days_old = min_age_days
        score = _calculate_recycle_score(post, days_old)
        scored_posts.append((post, days_old, score))

    # Sort by score descending
    scored_posts.sort(key=lambda x: x[2], reverse=True)

    # Limit results
    scored_posts = scored_posts[:limit]

    suggestions = [
        _post_to_recycling_dict(p, days_old, score)
        for p, days_old, score in scored_posts
    ]

    return {
        "suggestions": suggestions,
        "total_recyclable": len(posts),
        "evergreen_count": sum(1 for p in posts if p.category in EVERGREEN_CATEGORIES),
    }


@router.get("/stats")
async def get_recycling_stats(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get recycling statistics for the dashboard."""
    now = _get_now_naive()
    cutoff_90 = now - timedelta(days=90)

    # Total posts older than 90 days
    total_result = await db.execute(
        select(func.count(Post.id)).where(
            Post.user_id == user_id,
            Post.created_at <= cutoff_90,
        )
    )
    total_recyclable = total_result.scalar() or 0

    # Evergreen posts older than 90 days
    evergreen_result = await db.execute(
        select(func.count(Post.id)).where(
            Post.user_id == user_id,
            Post.created_at <= cutoff_90,
            Post.category.in_(EVERGREEN_CATEGORIES),
        )
    )
    evergreen_count = evergreen_result.scalar() or 0

    # Category breakdown of recyclable posts
    category_result = await db.execute(
        select(Post.category, func.count(Post.id))
        .where(
            Post.user_id == user_id,
            Post.created_at <= cutoff_90,
        )
        .group_by(Post.category)
    )
    categories = [
        {
            "category": row[0],
            "label": CATEGORY_LABELS.get(row[0], row[0]),
            "count": row[1],
            "is_evergreen": row[0] in EVERGREEN_CATEGORIES,
        }
        for row in category_result.all()
    ]

    return {
        "total_recyclable": total_recyclable,
        "evergreen_count": evergreen_count,
        "categories": categories,
        "evergreen_categories": list(EVERGREEN_CATEGORIES),
    }


@router.post("/{post_id}/refresh")
async def refresh_post(
    post_id: int,
    refresh_data: dict = None,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a refreshed copy of an old post for recycling.

    Creates a new draft post based on the original, with:
    - Status reset to 'draft'
    - Title updated with '(Refresh)' suffix
    - All content copied for editing
    - Optional overrides via refresh_data
    """
    if refresh_data is None:
        refresh_data = {}

    result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user_id)
    )
    original = result.scalar_one_or_none()
    if not original:
        raise HTTPException(status_code=404, detail="Post not found")

    # Create new post based on original
    new_title = refresh_data.get("title", f"{original.title} (Refresh)" if original.title else "Refresh")

    new_post = Post(
        user_id=user_id,
        template_id=original.template_id,
        category=refresh_data.get("category", original.category),
        country=refresh_data.get("country", original.country),
        platform=refresh_data.get("platform", original.platform),
        status="draft",
        title=new_title,
        slide_data=original.slide_data,
        caption_instagram=original.caption_instagram,
        caption_tiktok=original.caption_tiktok,
        hashtags_instagram=original.hashtags_instagram,
        hashtags_tiktok=original.hashtags_tiktok,
        cta_text=original.cta_text,
        tone=refresh_data.get("tone", original.tone),
    )
    db.add(new_post)
    await db.flush()
    await db.refresh(new_post)

    response = {
        "id": new_post.id,
        "title": new_post.title,
        "category": new_post.category,
        "country": new_post.country,
        "platform": new_post.platform,
        "status": new_post.status,
        "tone": new_post.tone,
        "created_at": new_post.created_at.isoformat() if new_post.created_at else None,
        "original_post_id": post_id,
        "message": "Post wurde als Entwurf recycelt. Du kannst ihn jetzt bearbeiten.",
    }

    await db.commit()
    return response


@router.get("/calendar-suggestions")
async def get_calendar_recycling_suggestions(
    month: int = Query(ge=1, le=12),
    year: int = Query(ge=2020, le=2030),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Suggest recyclable posts for empty calendar days.

    Finds days without scheduled posts in the given month and suggests
    recyclable content from the user's post history for those gaps.
    """
    from calendar import monthrange

    now = _get_now_naive()
    _, days_in_month = monthrange(year, month)

    # Get all dates with scheduled posts in the requested month
    month_start = datetime(year, month, 1)
    month_end = datetime(year, month, days_in_month, 23, 59, 59)

    scheduled_result = await db.execute(
        select(Post.scheduled_date).where(
            Post.user_id == user_id,
            Post.scheduled_date >= month_start,
            Post.scheduled_date <= month_end,
            Post.status.in_(["scheduled", "reminded", "exported", "posted"]),
        )
    )
    scheduled_dates = set()
    for row in scheduled_result.all():
        if row[0]:
            scheduled_dates.add(row[0].date() if hasattr(row[0], 'date') else row[0])

    # Find gap days (no scheduled posts, future dates only)
    today = now.date()
    gap_days = []
    for day_num in range(1, days_in_month + 1):
        from datetime import date as date_type
        d = date_type(year, month, day_num)
        if d >= today and d not in scheduled_dates:
            gap_days.append(d)

    # Get recyclable posts (older than 90 days)
    cutoff = now - timedelta(days=90)
    recycle_result = await db.execute(
        select(Post).where(
            Post.user_id == user_id,
            Post.created_at <= cutoff,
        ).order_by(Post.created_at.asc())
    )
    recyclable_posts = recycle_result.scalars().all()

    # Score posts
    scored = []
    for post in recyclable_posts:
        if post.created_at:
            post_created = post.created_at.replace(tzinfo=None) if post.created_at.tzinfo else post.created_at
            days_old = (now - post_created).days
        else:
            days_old = 90
        score = _calculate_recycle_score(post, days_old)
        scored.append((post, days_old, score))
    scored.sort(key=lambda x: x[2], reverse=True)

    # Build suggestions: match top recyclable posts to gap days
    suggestions = []
    for i, gap_day in enumerate(gap_days[:10]):  # Limit to 10 gap days
        if i < len(scored):
            post, days_old, score = scored[i % len(scored)]
            suggestions.append({
                "gap_date": gap_day.isoformat(),
                "gap_day_name": gap_day.strftime("%A"),
                "suggested_post": _post_to_recycling_dict(post, days_old, score),
            })
        else:
            suggestions.append({
                "gap_date": gap_day.isoformat(),
                "gap_day_name": gap_day.strftime("%A"),
                "suggested_post": None,
            })

    return {
        "month": month,
        "year": year,
        "total_gaps": len(gap_days),
        "suggestions": suggestions,
        "total_recyclable": len(recyclable_posts),
    }
