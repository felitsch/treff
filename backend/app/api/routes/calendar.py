"""Calendar routes."""

import csv
import io
from typing import Optional
from datetime import datetime, date
from calendar import monthrange
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
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


@router.get("/reminders")
async def get_due_reminders(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get posts that are due for publishing (scheduled time has arrived or passed).
    Returns posts with status 'scheduled' where the scheduled date/time is now or in the past,
    that haven't been marked as 'reminded' yet.
    Also includes posts scheduled for today whose time has passed but are still 'scheduled'."""
    from datetime import timedelta

    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    current_time_str = now.strftime("%H:%M")

    # Start of today
    today_start = datetime(now.year, now.month, now.day, 0, 0, 0)

    # Find posts that are scheduled and due:
    # 1. Posts scheduled for a date BEFORE today (overdue)
    # 2. Posts scheduled for today where the time has passed
    # Status must be 'scheduled' (not yet reminded/posted/exported)
    query = select(Post).where(
        and_(
            Post.user_id == user_id,
            Post.scheduled_date.isnot(None),
            Post.status == "scheduled",
        )
    ).order_by(Post.scheduled_date.asc())

    result = await db.execute(query)
    posts = result.scalars().all()

    due_posts = []
    for post in posts:
        post_date_str = post.scheduled_date.strftime("%Y-%m-%d")
        post_time = post.scheduled_time or "00:00"

        if post_date_str < today_str:
            # Overdue - scheduled date is in the past
            due_posts.append(post)
        elif post_date_str == today_str and post_time <= current_time_str:
            # Due today - scheduled time has passed
            due_posts.append(post)

    return {
        "reminders": [post_to_calendar_dict(post) for post in due_posts],
        "count": len(due_posts),
    }


@router.put("/reminders/{post_id}/acknowledge")
async def acknowledge_reminder(
    post_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Acknowledge a reminder by changing post status from 'scheduled' to 'reminded'.
    This prevents the reminder from showing again."""
    query = select(Post).where(
        and_(
            Post.id == post_id,
            Post.user_id == user_id,
        )
    )
    result = await db.execute(query)
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.status != "scheduled":
        raise HTTPException(status_code=400, detail="Post is not in scheduled status")

    post.status = "reminded"
    await db.commit()

    return {
        "success": True,
        "post_id": post.id,
        "status": "reminded",
        "message": f"Reminder acknowledged for post '{post.title}'",
    }


@router.get("/queue")
async def get_calendar_queue(
    platform: Optional[str] = None,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get upcoming scheduled posts in chronological order (queue view).
    Returns all posts with a scheduled_date >= today, sorted by date and time ascending.
    Optionally filter by platform (instagram_feed, instagram_story, tiktok)."""
    from datetime import timedelta

    now = datetime.now()
    today_start = datetime(now.year, now.month, now.day, 0, 0, 0)

    conditions = [
        Post.user_id == user_id,
        Post.scheduled_date.isnot(None),
        Post.scheduled_date >= today_start,
    ]

    # Apply platform filter if specified
    if platform:
        conditions.append(Post.platform == platform)

    query = (
        select(Post)
        .where(and_(*conditions))
        .order_by(Post.scheduled_date.asc(), Post.scheduled_time.asc())
    )

    result = await db.execute(query)
    posts = result.scalars().all()

    return {
        "posts": [post_to_calendar_dict(post) for post in posts],
        "count": len(posts),
    }


@router.get("/export-csv")
async def export_calendar_csv(
    month: Optional[int] = None,
    year: Optional[int] = None,
    platform: Optional[str] = None,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Export all scheduled posts for a given month as a CSV file.
    Columns: date, time, title, category, platform, status, country.
    Returns a downloadable CSV file."""
    now = datetime.now()
    if not month:
        month = now.month
    if not year:
        year = now.year

    last_day_num = monthrange(year, month)[1]
    first_dt = datetime(year, month, 1, 0, 0, 0)
    last_dt = datetime(year, month, last_day_num, 23, 59, 59)

    conditions = [
        Post.user_id == user_id,
        Post.scheduled_date.isnot(None),
        Post.scheduled_date >= first_dt,
        Post.scheduled_date <= last_dt,
    ]

    if platform:
        conditions.append(Post.platform == platform)

    query = (
        select(Post)
        .where(and_(*conditions))
        .order_by(Post.scheduled_date.asc(), Post.scheduled_time.asc())
    )

    result = await db.execute(query)
    posts = result.scalars().all()

    # Build CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow(["date", "time", "title", "category", "platform", "status", "country"])

    # Data rows
    for post in posts:
        writer.writerow([
            post.scheduled_date.strftime("%Y-%m-%d") if post.scheduled_date else "",
            post.scheduled_time or "",
            post.title or "",
            post.category or "",
            post.platform or "",
            post.status or "",
            post.country or "",
        ])

    output.seek(0)

    # Month names for filename
    month_names_en = [
        "january", "february", "march", "april", "may", "june",
        "july", "august", "september", "october", "november", "december",
    ]
    filename = f"TREFF_calendar_{month_names_en[month - 1]}_{year}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


# ========== SEASONAL MARKERS ==========
# Fixed annual markers for TREFF Sprachreisen business cycle.
# These are predefined dates that appear on the calendar every year
# to help the social media team plan deadline-related posts.

SEASONAL_MARKERS = [
    # Bewerbungsfristen (Application Deadlines)
    {
        "type": "bewerbungsfrist",
        "label": "Bewerbungsfrist USA Classic",
        "icon": "📋",
        "color": "red",
        "month": 3,
        "day": 31,
        "description": "Bewerbungsschluss fuer USA Classic Programm (Herbstabreise)",
    },
    {
        "type": "bewerbungsfrist",
        "label": "Bewerbungsfrist Kanada",
        "icon": "📋",
        "color": "red",
        "month": 4,
        "day": 30,
        "description": "Bewerbungsschluss fuer Kanada-Programme (Herbstabreise)",
    },
    {
        "type": "bewerbungsfrist",
        "label": "Bewerbungsfrist Australien/Neuseeland",
        "icon": "📋",
        "color": "red",
        "month": 5,
        "day": 31,
        "description": "Bewerbungsschluss fuer Australien & Neuseeland (Januar-Abreise)",
    },
    {
        "type": "bewerbungsfrist",
        "label": "Bewerbungsfrist Irland",
        "icon": "📋",
        "color": "red",
        "month": 5,
        "day": 15,
        "description": "Bewerbungsschluss fuer Irland-Programme (Herbstabreise)",
    },
    {
        "type": "bewerbungsfrist",
        "label": "Bewerbungsfrist USA Select",
        "icon": "📋",
        "color": "red",
        "month": 4,
        "day": 15,
        "description": "Bewerbungsschluss fuer USA Select Programm (Herbstabreise)",
    },
    # Abflugzeiten (Departure Periods)
    {
        "type": "abflugzeit",
        "label": "Abflug USA/Kanada/Irland",
        "icon": "✈️",
        "color": "blue",
        "month": 8,
        "day": 15,
        "description": "Abreisezeitraum fuer USA, Kanada und Irland (Mitte August)",
    },
    {
        "type": "abflugzeit",
        "label": "Abflug Australien/Neuseeland",
        "icon": "✈️",
        "color": "blue",
        "month": 1,
        "day": 20,
        "description": "Abreisezeitraum fuer Australien & Neuseeland (Ende Januar)",
    },
    # Schuljahresbeginn (School Year Start)
    {
        "type": "schuljahresbeginn",
        "label": "Schulstart USA/Kanada",
        "icon": "🏫",
        "color": "green",
        "month": 9,
        "day": 1,
        "description": "Schuljahresbeginn in den USA und Kanada",
    },
    {
        "type": "schuljahresbeginn",
        "label": "Schulstart Irland",
        "icon": "🏫",
        "color": "green",
        "month": 9,
        "day": 1,
        "description": "Schuljahresbeginn in Irland",
    },
    {
        "type": "schuljahresbeginn",
        "label": "Schulstart Australien/Neuseeland",
        "icon": "🏫",
        "color": "green",
        "month": 2,
        "day": 1,
        "description": "Schuljahresbeginn in Australien & Neuseeland (Term 1)",
    },
    # Rueckkehr-Saison (Return Season)
    {
        "type": "rueckkehr",
        "label": "Rueckkehr USA/Kanada/Irland",
        "icon": "🏠",
        "color": "purple",
        "month": 6,
        "day": 15,
        "description": "Rueckkehrzeitraum fuer USA, Kanada und Irland Austauschschueler",
    },
    {
        "type": "rueckkehr",
        "label": "Rueckkehr Australien/Neuseeland",
        "icon": "🏠",
        "color": "purple",
        "month": 12,
        "day": 10,
        "description": "Rueckkehrzeitraum fuer Australien & Neuseeland Austauschschueler",
    },
    # Stipendien-Deadlines (Scholarship Deadlines)
    {
        "type": "stipendium",
        "label": "Stipendien-Bewerbungsfrist",
        "icon": "🎓",
        "color": "amber",
        "month": 10,
        "day": 15,
        "description": "Bewerbungsschluss fuer TREFF-Stipendien und Teilstipendien",
    },
    # Messen & Events (Fairs & Events)
    {
        "type": "messe",
        "label": "JuBi Messe Herbst",
        "icon": "🎪",
        "color": "teal",
        "month": 11,
        "day": 1,
        "description": "Jugendbildungsmesse (JuBi) - Herbsttermine fuer Highschool-Interessenten",
    },
    {
        "type": "messe",
        "label": "JuBi Messe Fruehling",
        "icon": "🎪",
        "color": "teal",
        "month": 3,
        "day": 1,
        "description": "Jugendbildungsmesse (JuBi) - Fruehlingsstermine fuer Highschool-Interessenten",
    },
]


@router.get("/seasonal-markers")
async def get_seasonal_markers(
    month: Optional[int] = None,
    year: Optional[int] = None,
    user_id: int = Depends(get_current_user_id),
):
    """Get seasonal markers (Bewerbungsfristen, Abflugzeiten, etc.) for a given month.

    Returns a list of markers with date, label, type, icon, color, and description.
    These are fixed annual dates relevant to TREFF's Highschool program business cycle.
    """
    now = datetime.now()
    if not month:
        month = now.month
    if not year:
        year = now.year

    markers = []
    for marker in SEASONAL_MARKERS:
        if marker["month"] == month:
            # Validate the day is valid for this month/year
            last_day = monthrange(year, month)[1]
            day = min(marker["day"], last_day)

            marker_date = date(year, month, day)
            markers.append({
                "date": marker_date.isoformat(),
                "type": marker["type"],
                "label": marker["label"],
                "icon": marker["icon"],
                "color": marker["color"],
                "description": marker["description"],
            })

    return {
        "markers": markers,
        "month": month,
        "year": year,
        "count": len(markers),
    }
