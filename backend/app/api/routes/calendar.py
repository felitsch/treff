"""Calendar routes."""

from typing import Optional
from datetime import datetime, date
from calendar import monthrange
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, extract, func

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.post import Post
from app.models.setting import Setting

router = APIRouter()


def post_to_calendar_dict(post: Post) -> dict:
    """Convert a Post model to a calendar-friendly dict."""
    return {
        "id": post.id,
        "title": post.title,
        "category": post.category,
        "country": post.country,
        "platform": post.platform,
        "status": post.status,
        "scheduled_date": post.scheduled_date.strftime("%Y-%m-%d") if post.scheduled_date else None,
        "scheduled_time": post.scheduled_time,
        "created_at": post.created_at.isoformat() if post.created_at else None,
    }


@router.get("")
async def get_calendar(
    month: Optional[int] = None,
    year: Optional[int] = None,
    platform: Optional[str] = None,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get posts scheduled for a given month, grouped by date.
    Optionally filter by platform (instagram_feed, instagram_story, tiktok)."""
    now = datetime.now()
    if not month:
        month = now.month
    if not year:
        year = now.year

    # Get first and last day of the month
    first_day = date(year, month, 1)
    last_day_num = monthrange(year, month)[1]
    last_day = date(year, month, last_day_num)

    # Query posts that have a scheduled_date within this month
    first_dt = datetime(year, month, 1, 0, 0, 0)
    last_dt = datetime(year, month, last_day_num, 23, 59, 59)

    conditions = [
        Post.user_id == user_id,
        Post.scheduled_date.isnot(None),
        Post.scheduled_date >= first_dt,
        Post.scheduled_date <= last_dt,
    ]

    # Apply platform filter if specified
    if platform:
        conditions.append(Post.platform == platform)

    query = select(Post).where(and_(*conditions)).order_by(Post.scheduled_date)

    result = await db.execute(query)
    posts = result.scalars().all()

    # Group posts by date
    posts_by_date = {}
    for post in posts:
        date_key = post.scheduled_date.strftime("%Y-%m-%d")
        if date_key not in posts_by_date:
            posts_by_date[date_key] = []
        posts_by_date[date_key].append(post_to_calendar_dict(post))

    return {
        "month": month,
        "year": year,
        "posts_by_date": posts_by_date,
        "total_posts": len(posts),
    }


@router.get("/week")
async def get_calendar_week(
    date_str: Optional[str] = Query(None, alias="date"),
    platform: Optional[str] = None,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get posts scheduled for a week around the given date.
    Optionally filter by platform (instagram_feed, instagram_story, tiktok)."""
    from datetime import timedelta

    if date_str:
        try:
            center_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        center_date = date.today()

    # Get the Monday of the week
    start_of_week = center_date - timedelta(days=center_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    start_dt = datetime(start_of_week.year, start_of_week.month, start_of_week.day, 0, 0, 0)
    end_dt = datetime(end_of_week.year, end_of_week.month, end_of_week.day, 23, 59, 59)

    conditions = [
        Post.user_id == user_id,
        Post.scheduled_date.isnot(None),
        Post.scheduled_date >= start_dt,
        Post.scheduled_date <= end_dt,
    ]

    # Apply platform filter if specified
    if platform:
        conditions.append(Post.platform == platform)

    query = select(Post).where(and_(*conditions)).order_by(Post.scheduled_date)

    result = await db.execute(query)
    posts = result.scalars().all()

    posts_by_date = {}
    for post in posts:
        date_key = post.scheduled_date.strftime("%Y-%m-%d")
        if date_key not in posts_by_date:
            posts_by_date[date_key] = []
        posts_by_date[date_key].append(post_to_calendar_dict(post))

    return {
        "start_date": start_of_week.isoformat(),
        "end_date": end_of_week.isoformat(),
        "posts_by_date": posts_by_date,
    }


@router.get("/unscheduled")
async def get_unscheduled_drafts(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get posts that are not yet scheduled (no scheduled_date set)."""
    query = select(Post).where(
        and_(
            Post.user_id == user_id,
            Post.scheduled_date.is_(None),
            Post.status.in_(["draft", "exported"]),
        )
    ).order_by(Post.created_at.desc())

    result = await db.execute(query)
    posts = result.scalars().all()

    return {
        "posts": [post_to_calendar_dict(post) for post in posts],
        "count": len(posts),
    }


@router.get("/gaps")
async def get_calendar_gaps(
    month: Optional[int] = None,
    year: Optional[int] = None,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get days without scheduled content for a month."""
    now = datetime.now()
    if not month:
        month = now.month
    if not year:
        year = now.year

    last_day_num = monthrange(year, month)[1]
    first_dt = datetime(year, month, 1, 0, 0, 0)
    last_dt = datetime(year, month, last_day_num, 23, 59, 59)

    query = select(Post.scheduled_date).where(
        and_(
            Post.user_id == user_id,
            Post.scheduled_date.isnot(None),
            Post.scheduled_date >= first_dt,
            Post.scheduled_date <= last_dt,
        )
    )
    result = await db.execute(query)
    scheduled_dates = set()
    for row in result.scalars().all():
        if row:
            scheduled_dates.add(row.strftime("%Y-%m-%d"))

    gaps = []
    for day in range(1, last_day_num + 1):
        d = date(year, month, day)
        if d.isoformat() not in scheduled_dates:
            gaps.append(d.isoformat())

    return {"gaps": gaps, "month": month, "year": year}


@router.get("/stats")
async def get_calendar_stats(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get posting frequency and goal progress."""
    from datetime import timedelta

    now = datetime.now()
    # This week (Monday to Sunday)
    start_of_week = now.date() - timedelta(days=now.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    start_week_dt = datetime(start_of_week.year, start_of_week.month, start_of_week.day, 0, 0, 0)
    end_week_dt = datetime(end_of_week.year, end_of_week.month, end_of_week.day, 23, 59, 59)

    # Posts this week
    week_query = select(func.count(Post.id)).where(
        and_(
            Post.user_id == user_id,
            Post.scheduled_date.isnot(None),
            Post.scheduled_date >= start_week_dt,
            Post.scheduled_date <= end_week_dt,
        )
    )
    week_result = await db.execute(week_query)
    posts_this_week = week_result.scalar() or 0

    # Posts this month
    first_of_month = datetime(now.year, now.month, 1, 0, 0, 0)
    last_day_num = monthrange(now.year, now.month)[1]
    last_of_month = datetime(now.year, now.month, last_day_num, 23, 59, 59)

    month_query = select(func.count(Post.id)).where(
        and_(
            Post.user_id == user_id,
            Post.scheduled_date.isnot(None),
            Post.scheduled_date >= first_of_month,
            Post.scheduled_date <= last_of_month,
        )
    )
    month_result = await db.execute(month_query)
    posts_this_month = month_result.scalar() or 0

    # Fetch user's posting goals from settings
    settings_result = await db.execute(
        select(Setting).where(
            and_(
                Setting.user_id == user_id,
                Setting.key.in_(["posts_per_week", "posts_per_month"]),
            )
        )
    )
    user_settings = {s.key: s.value for s in settings_result.scalars().all()}

    # Use user settings or defaults (3 per week, 12 per month)
    try:
        weekly_goal = int(user_settings.get("posts_per_week", "3"))
    except (ValueError, TypeError):
        weekly_goal = 3

    try:
        monthly_goal = int(user_settings.get("posts_per_month", "12"))
    except (ValueError, TypeError):
        monthly_goal = 12

    return {
        "posts_this_week": posts_this_week,
        "weekly_goal": weekly_goal,
        "posts_this_month": posts_this_month,
        "monthly_goal": monthly_goal,
    }
