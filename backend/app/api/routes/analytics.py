"""Analytics routes."""

from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.post import Post
from app.models.asset import Asset
from app.models.calendar_entry import CalendarEntry
from app.models.content_suggestion import ContentSuggestion

router = APIRouter()


@router.get("/overview")
async def get_overview(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get analytics overview: total posts, this week, this month."""
    now = datetime.now(timezone.utc)
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    total_result = await db.execute(
        select(func.count(Post.id)).where(Post.user_id == user_id)
    )
    total = total_result.scalar() or 0

    week_result = await db.execute(
        select(func.count(Post.id)).where(
            Post.user_id == user_id,
            Post.created_at >= week_start,
        )
    )
    posts_this_week = week_result.scalar() or 0

    month_result = await db.execute(
        select(func.count(Post.id)).where(
            Post.user_id == user_id,
            Post.created_at >= month_start,
        )
    )
    posts_this_month = month_result.scalar() or 0

    return {
        "total_posts": total,
        "posts_this_week": posts_this_week,
        "posts_this_month": posts_this_month,
    }


@router.get("/dashboard")
async def get_dashboard_data(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get all dashboard data in a single API call."""
    now = datetime.now(timezone.utc)
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

    # Quick stats
    total_result = await db.execute(
        select(func.count(Post.id)).where(Post.user_id == user_id)
    )
    total_posts = total_result.scalar() or 0

    week_result = await db.execute(
        select(func.count(Post.id)).where(
            Post.user_id == user_id,
            Post.created_at >= week_start,
        )
    )
    posts_this_week = week_result.scalar() or 0

    scheduled_result = await db.execute(
        select(func.count(Post.id)).where(
            Post.user_id == user_id,
            Post.status == "scheduled",
        )
    )
    scheduled_posts = scheduled_result.scalar() or 0

    asset_result = await db.execute(
        select(func.count(Asset.id)).where(Asset.user_id == user_id)
    )
    total_assets = asset_result.scalar() or 0

    # Recent posts (last 5)
    recent_result = await db.execute(
        select(Post)
        .where(Post.user_id == user_id)
        .order_by(Post.created_at.desc())
        .limit(5)
    )
    recent_posts_raw = recent_result.scalars().all()
    recent_posts = [
        {
            "id": p.id,
            "title": p.title,
            "category": p.category,
            "platform": p.platform,
            "status": p.status,
            "country": p.country,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in recent_posts_raw
    ]

    # Mini calendar: scheduled posts for the next 7 days
    today = now.date()
    next_week = today + timedelta(days=7)
    calendar_result = await db.execute(
        select(CalendarEntry).where(
            CalendarEntry.scheduled_date >= today,
            CalendarEntry.scheduled_date <= next_week,
        )
    )
    calendar_entries_raw = calendar_result.scalars().all()
    calendar_entries = [
        {
            "id": e.id,
            "post_id": e.post_id,
            "scheduled_date": e.scheduled_date.isoformat() if e.scheduled_date else None,
            "scheduled_time": e.scheduled_time,
            "notes": e.notes,
        }
        for e in calendar_entries_raw
    ]

    # Content suggestions (pending, latest 5)
    suggestions_result = await db.execute(
        select(ContentSuggestion)
        .where(ContentSuggestion.status == "pending")
        .order_by(ContentSuggestion.created_at.desc())
        .limit(5)
    )
    suggestions_raw = suggestions_result.scalars().all()
    suggestions = [
        {
            "id": s.id,
            "suggestion_type": s.suggestion_type,
            "title": s.title,
            "description": s.description,
            "suggested_category": s.suggested_category,
            "suggested_country": s.suggested_country,
            "suggested_date": s.suggested_date.isoformat() if s.suggested_date else None,
            "reason": s.reason,
            "status": s.status,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in suggestions_raw
    ]

    return {
        "stats": {
            "posts_this_week": posts_this_week,
            "scheduled_posts": scheduled_posts,
            "total_assets": total_assets,
            "total_posts": total_posts,
        },
        "recent_posts": recent_posts,
        "calendar_entries": calendar_entries,
        "suggestions": suggestions,
    }


@router.get("/frequency")
async def get_frequency(
    period: str = "week",
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get posting frequency over time."""
    # TODO: Implement time-based aggregation
    return {"period": period, "data": []}


@router.get("/categories")
async def get_categories(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get category distribution."""
    result = await db.execute(
        select(Post.category, func.count(Post.id))
        .where(Post.user_id == user_id)
        .group_by(Post.category)
    )
    return [{"category": row[0], "count": row[1]} for row in result.all()]


@router.get("/platforms")
async def get_platforms(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get platform distribution."""
    result = await db.execute(
        select(Post.platform, func.count(Post.id))
        .where(Post.user_id == user_id)
        .group_by(Post.platform)
    )
    return [{"platform": row[0], "count": row[1]} for row in result.all()]


@router.get("/countries")
async def get_countries(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get country distribution."""
    result = await db.execute(
        select(Post.country, func.count(Post.id))
        .where(Post.user_id == user_id, Post.country.isnot(None))
        .group_by(Post.country)
    )
    return [{"country": row[0], "count": row[1]} for row in result.all()]


@router.get("/templates")
async def get_template_usage(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get most used templates."""
    result = await db.execute(
        select(Post.template_id, func.count(Post.id))
        .where(Post.user_id == user_id, Post.template_id.isnot(None))
        .group_by(Post.template_id)
        .order_by(func.count(Post.id).desc())
    )
    return [{"template_id": row[0], "count": row[1]} for row in result.all()]


@router.get("/goals")
async def get_goals(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get weekly/monthly targets vs actual."""
    now = datetime.now(timezone.utc)
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    week_result = await db.execute(
        select(func.count(Post.id)).where(
            Post.user_id == user_id,
            Post.created_at >= week_start,
        )
    )
    weekly_actual = week_result.scalar() or 0

    month_result = await db.execute(
        select(func.count(Post.id)).where(
            Post.user_id == user_id,
            Post.created_at >= month_start,
        )
    )
    monthly_actual = month_result.scalar() or 0

    return {
        "weekly_target": 4,
        "weekly_actual": weekly_actual,
        "monthly_target": 16,
        "monthly_actual": monthly_actual,
    }
