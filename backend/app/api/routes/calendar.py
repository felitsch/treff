"""Calendar routes."""

import csv
import io
import json
import uuid
from typing import Optional, List
from datetime import datetime, date, timedelta
from calendar import monthrange
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, extract, func

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.post import Post
from app.models.setting import Setting
from app.models.story_arc import StoryArc
from app.models.recurring_format import RecurringFormat

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
        "story_arc_id": post.story_arc_id,
        "episode_number": post.episode_number,
        "linked_post_group_id": post.linked_post_group_id,
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


# ========== STORY ARC TIMELINE ==========

# Colors assigned to arcs automatically (cycle through)
ARC_COLORS = [
    {"bg": "#3B82F6", "light": "#DBEAFE", "text": "#1E40AF"},   # blue
    {"bg": "#8B5CF6", "light": "#EDE9FE", "text": "#5B21B6"},   # violet
    {"bg": "#EC4899", "light": "#FCE7F3", "text": "#9D174D"},   # pink
    {"bg": "#10B981", "light": "#D1FAE5", "text": "#065F46"},   # emerald
    {"bg": "#F59E0B", "light": "#FEF3C7", "text": "#92400E"},   # amber
    {"bg": "#EF4444", "light": "#FEE2E2", "text": "#991B1B"},   # red
    {"bg": "#06B6D4", "light": "#CFFAFE", "text": "#155E75"},   # cyan
    {"bg": "#F97316", "light": "#FFEDD5", "text": "#9A3412"},   # orange
]


@router.get("/arc-timeline")
async def get_arc_timeline(
    month: Optional[int] = None,
    year: Optional[int] = None,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get story arcs with their episode posts for calendar timeline display.

    Returns arcs that have at least one episode (post with story_arc_id) scheduled
    within the visible calendar range (prev month trailing days through next month leading days),
    or arcs whose date range overlaps with the visible month.

    Each arc includes:
    - Arc metadata (title, status, planned_episodes, etc.)
    - Episodes (posts linked to the arc) with scheduled dates
    - Computed start_date and end_date based on episode scheduled dates
    - Auto-assigned color for timeline display
    """
    from datetime import timedelta

    now = datetime.now()
    if not month:
        month = now.month
    if not year:
        year = now.year

    # Calculate the visible date range for the calendar month view
    # This includes trailing days from prev month and leading days from next month
    first_of_month = date(year, month, 1)
    last_day_num = monthrange(year, month)[1]
    last_of_month = date(year, month, last_day_num)

    # Extend range to cover the full 6-week calendar grid
    # Go back to the Monday of the week containing the 1st
    start_dow = first_of_month.weekday()  # 0=Mon, 6=Sun
    visible_start = first_of_month - timedelta(days=start_dow)
    # Go forward to fill 42 cells (6 weeks)
    visible_end = visible_start + timedelta(days=41)

    visible_start_dt = datetime(visible_start.year, visible_start.month, visible_start.day, 0, 0, 0)
    visible_end_dt = datetime(visible_end.year, visible_end.month, visible_end.day, 23, 59, 59)

    # Get all active/draft/paused story arcs for this user
    arc_query = select(StoryArc).where(
        StoryArc.user_id == user_id,
        StoryArc.status.in_(["draft", "active", "paused", "completed"]),
    ).order_by(StoryArc.created_at.asc())

    arc_result = await db.execute(arc_query)
    arcs = arc_result.scalars().all()

    if not arcs:
        return {"arcs": [], "month": month, "year": year}

    arc_ids = [a.id for a in arcs]

    # Get all posts (episodes) linked to these arcs that have a scheduled date
    episode_query = select(Post).where(
        Post.user_id == user_id,
        Post.story_arc_id.in_(arc_ids),
        Post.scheduled_date.isnot(None),
    ).order_by(Post.scheduled_date.asc())

    episode_result = await db.execute(episode_query)
    episodes = episode_result.scalars().all()

    # Group episodes by arc_id
    episodes_by_arc = {}
    for ep in episodes:
        if ep.story_arc_id not in episodes_by_arc:
            episodes_by_arc[ep.story_arc_id] = []
        episodes_by_arc[ep.story_arc_id].append(ep)

    # Build timeline data
    timeline_arcs = []
    for idx, arc in enumerate(arcs):
        arc_episodes = episodes_by_arc.get(arc.id, [])

        # Skip arcs with no scheduled episodes
        if not arc_episodes:
            continue

        # Compute date range from episodes
        ep_dates = [ep.scheduled_date for ep in arc_episodes if ep.scheduled_date]
        if not ep_dates:
            continue

        arc_start = min(ep_dates)
        arc_end = max(ep_dates)

        arc_start_date = arc_start.date() if hasattr(arc_start, 'date') else arc_start
        arc_end_date = arc_end.date() if hasattr(arc_end, 'date') else arc_end

        # Check if arc date range overlaps with visible calendar range
        if arc_end_date < visible_start or arc_start_date > visible_end:
            continue

        # Assign color (cycle through palette)
        color = ARC_COLORS[idx % len(ARC_COLORS)]

        # Build episode list
        ep_list = []
        for ep_idx, ep in enumerate(arc_episodes):
            ep_date = ep.scheduled_date
            ep_date_str = ep_date.strftime("%Y-%m-%d") if ep_date else None
            ep_list.append({
                "id": ep.id,
                "title": ep.title or f"Episode {ep.episode_number or (ep_idx + 1)}",
                "episode_number": ep.episode_number or (ep_idx + 1),
                "scheduled_date": ep_date_str,
                "scheduled_time": ep.scheduled_time,
                "status": ep.status,
                "platform": ep.platform,
                "category": ep.category,
            })

        timeline_arcs.append({
            "id": arc.id,
            "title": arc.title,
            "subtitle": arc.subtitle,
            "status": arc.status,
            "country": arc.country,
            "planned_episodes": arc.planned_episodes,
            "current_episode": arc.current_episode,
            "start_date": arc_start_date.isoformat(),
            "end_date": arc_end_date.isoformat(),
            "color": color,
            "episodes": ep_list,
            "total_episodes": len(ep_list),
        })

    return {
        "arcs": timeline_arcs,
        "month": month,
        "year": year,
        "count": len(timeline_arcs),
    }


# ========== SERIES ORDER VALIDATION ==========

async def _get_arc_episodes(db: AsyncSession, user_id: int, arc_id: int) -> list:
    """Get all episodes for a story arc, ordered by episode_number then scheduled_date."""
    query = select(Post).where(
        Post.user_id == user_id,
        Post.story_arc_id == arc_id,
    ).order_by(Post.episode_number.asc().nullslast(), Post.scheduled_date.asc().nullslast())
    result = await db.execute(query)
    return list(result.scalars().all())


async def _get_min_episode_gap(db: AsyncSession, user_id: int) -> int:
    """Get min_episode_gap_days from user settings (default: 1)."""
    result = await db.execute(
        select(Setting).where(
            Setting.user_id == user_id,
            Setting.key == "min_episode_gap_days",
        )
    )
    setting = result.scalar_one_or_none()
    if setting:
        try:
            return max(0, int(setting.value))
        except (ValueError, TypeError):
            pass
    return 1  # Default: 1 day minimum gap


def _validate_episode_order(
    episodes: list,
    target_post_id: int,
    target_date: date,
    min_gap_days: int = 1,
) -> dict:
    """Validate that scheduling an episode at target_date respects ordering.

    Returns dict with:
    - valid: bool
    - conflicts: list of conflict descriptions
    - warnings: list of warning messages
    """
    conflicts = []
    warnings = []

    # Find the target post's episode_number
    target_ep_num = None
    for ep in episodes:
        if ep.id == target_post_id:
            target_ep_num = ep.episode_number
            break

    if target_ep_num is None:
        return {"valid": True, "conflicts": [], "warnings": []}

    for ep in episodes:
        if ep.id == target_post_id:
            continue
        if ep.episode_number is None or ep.scheduled_date is None:
            continue

        ep_date = ep.scheduled_date.date() if hasattr(ep.scheduled_date, 'date') else ep.scheduled_date

        # Earlier episode must be scheduled before the target date
        if ep.episode_number < target_ep_num:
            if ep_date >= target_date:
                conflicts.append({
                    "type": "predecessor_conflict",
                    "episode_id": ep.id,
                    "episode_number": ep.episode_number,
                    "episode_title": ep.title or f"Episode {ep.episode_number}",
                    "episode_date": ep_date.isoformat(),
                    "message": f"Episode {ep.episode_number} ('{ep.title or 'Unbenannt'}') ist fuer {ep_date.strftime('%d.%m.%Y')} geplant und muss VOR Episode {target_ep_num} liegen."
                })
            elif min_gap_days > 0:
                gap = (target_date - ep_date).days
                if gap < min_gap_days:
                    warnings.append({
                        "type": "min_gap_violation",
                        "episode_id": ep.id,
                        "episode_number": ep.episode_number,
                        "episode_title": ep.title or f"Episode {ep.episode_number}",
                        "episode_date": ep_date.isoformat(),
                        "gap_days": gap,
                        "min_gap_days": min_gap_days,
                        "message": f"Nur {gap} Tag(e) Abstand zu Episode {ep.episode_number} (Minimum: {min_gap_days} Tag(e))."
                    })

        # Later episode must be scheduled after the target date
        if ep.episode_number > target_ep_num:
            if ep_date <= target_date:
                conflicts.append({
                    "type": "successor_conflict",
                    "episode_id": ep.id,
                    "episode_number": ep.episode_number,
                    "episode_title": ep.title or f"Episode {ep.episode_number}",
                    "episode_date": ep_date.isoformat(),
                    "message": f"Episode {ep.episode_number} ('{ep.title or 'Unbenannt'}') ist fuer {ep_date.strftime('%d.%m.%Y')} geplant und muss NACH Episode {target_ep_num} liegen."
                })
            elif min_gap_days > 0:
                gap = (ep_date - target_date).days
                if gap < min_gap_days:
                    warnings.append({
                        "type": "min_gap_violation",
                        "episode_id": ep.id,
                        "episode_number": ep.episode_number,
                        "episode_title": ep.title or f"Episode {ep.episode_number}",
                        "episode_date": ep_date.isoformat(),
                        "gap_days": gap,
                        "min_gap_days": min_gap_days,
                        "message": f"Nur {gap} Tag(e) Abstand zu Episode {ep.episode_number} (Minimum: {min_gap_days} Tag(e))."
                    })

    return {
        "valid": len(conflicts) == 0,
        "conflicts": conflicts,
        "warnings": warnings,
    }


@router.post("/validate-episode-order")
async def validate_episode_order(
    data: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Validate that scheduling an episode at a target date respects series ordering.

    Body:
    - post_id: int - The post/episode being scheduled
    - target_date: str (YYYY-MM-DD) - The proposed scheduled date
    - story_arc_id: int (optional) - Override arc ID if post isn't linked yet

    Returns:
    - valid: bool - True if no ordering conflicts
    - conflicts: list - Hard conflicts (wrong order)
    - warnings: list - Soft warnings (min gap violations)
    - episode_info: dict - Info about the target episode and arc
    """
    post_id = data.get("post_id")
    target_date_str = data.get("target_date")
    arc_id_override = data.get("story_arc_id")

    if not post_id or not target_date_str:
        raise HTTPException(status_code=400, detail="post_id and target_date are required")

    try:
        target_date_parsed = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    # Get the post
    result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    arc_id = arc_id_override or post.story_arc_id
    if not arc_id:
        # Not part of a story arc - no ordering to validate
        return {
            "valid": True,
            "conflicts": [],
            "warnings": [],
            "episode_info": None,
        }

    # Get all episodes in the arc
    episodes = await _get_arc_episodes(db, user_id, arc_id)
    min_gap = await _get_min_episode_gap(db, user_id)

    validation = _validate_episode_order(episodes, post_id, target_date_parsed, min_gap)

    # Build episode info
    episode_info = {
        "post_id": post.id,
        "episode_number": post.episode_number,
        "story_arc_id": arc_id,
        "min_gap_days": min_gap,
        "total_episodes": len(episodes),
    }

    return {
        **validation,
        "episode_info": episode_info,
    }


@router.post("/schedule-episode")
async def schedule_episode(
    data: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Schedule an episode post with order validation and optional cascade shift.

    Body:
    - post_id: int - The post/episode to schedule
    - scheduled_date: str (YYYY-MM-DD)
    - scheduled_time: str (HH:MM)
    - force: bool (default false) - Skip validation and schedule anyway
    - shift_following: bool (default false) - Shift all following episodes by the same delta

    Returns: The scheduled post, plus info about any shifted episodes.
    """
    post_id = data.get("post_id")
    scheduled_date_str = data.get("scheduled_date")
    scheduled_time_str = data.get("scheduled_time", "10:00")
    force = data.get("force", False)
    shift_following = data.get("shift_following", False)

    if not post_id or not scheduled_date_str:
        raise HTTPException(status_code=400, detail="post_id and scheduled_date are required")

    try:
        target_date = datetime.strptime(scheduled_date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    target_date_only = target_date.date()

    # Reject past dates
    today = date.today()
    if target_date_only < today:
        raise HTTPException(
            status_code=400,
            detail="Vergangene Daten koennen nicht ausgewaehlt werden."
        )

    # Validate time format
    if scheduled_time_str:
        try:
            parts = scheduled_time_str.split(":")
            hour, minute = int(parts[0]), int(parts[1])
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError
        except (ValueError, IndexError):
            raise HTTPException(status_code=400, detail="Invalid time format. Use HH:MM (24-hour)")

    # Get the post
    result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    shifted_episodes = []
    arc_id = post.story_arc_id

    if arc_id and not force:
        # Validate episode order
        episodes = await _get_arc_episodes(db, user_id, arc_id)
        min_gap = await _get_min_episode_gap(db, user_id)
        validation = _validate_episode_order(episodes, post_id, target_date_only, min_gap)

        if not validation["valid"]:
            if not shift_following:
                # Return conflict info so frontend can offer shift option
                return {
                    "success": False,
                    "conflicts": validation["conflicts"],
                    "warnings": validation["warnings"],
                    "message": "Reihenfolge-Konflikt: " + "; ".join(
                        c["message"] for c in validation["conflicts"]
                    ),
                }

    # Calculate delta for shift_following
    if shift_following and arc_id and post.episode_number and post.scheduled_date:
        old_date = post.scheduled_date.date() if hasattr(post.scheduled_date, 'date') else post.scheduled_date
        day_delta = (target_date_only - old_date).days

        if day_delta != 0:
            # Get following episodes (higher episode_number)
            episodes = await _get_arc_episodes(db, user_id, arc_id)
            for ep in episodes:
                if ep.id == post_id:
                    continue
                if ep.episode_number and ep.episode_number > post.episode_number and ep.scheduled_date:
                    ep_old_date = ep.scheduled_date.date() if hasattr(ep.scheduled_date, 'date') else ep.scheduled_date
                    new_ep_date = ep_old_date + timedelta(days=day_delta)

                    # Don't shift to past dates
                    if new_ep_date >= today:
                        ep.scheduled_date = datetime(new_ep_date.year, new_ep_date.month, new_ep_date.day)
                        shifted_episodes.append({
                            "id": ep.id,
                            "title": ep.title,
                            "episode_number": ep.episode_number,
                            "old_date": ep_old_date.isoformat(),
                            "new_date": new_ep_date.isoformat(),
                        })

    # Schedule the target post
    post.scheduled_date = target_date
    post.scheduled_time = scheduled_time_str
    post.status = "scheduled"

    await db.flush()
    await db.refresh(post)

    post_dict = post_to_calendar_dict(post)
    await db.commit()

    return {
        "success": True,
        "post": post_dict,
        "shifted_episodes": shifted_episodes,
        "message": "Episode erfolgreich geplant."
        + (f" {len(shifted_episodes)} nachfolgende Episode(n) verschoben." if shifted_episodes else ""),
    }


@router.get("/episode-gap-setting")
async def get_episode_gap_setting(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get the min_episode_gap_days setting for the user."""
    min_gap = await _get_min_episode_gap(db, user_id)
    return {"min_episode_gap_days": min_gap}


@router.put("/episode-gap-setting")
async def set_episode_gap_setting(
    data: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Set the min_episode_gap_days setting for the user.

    Body:
    - min_episode_gap_days: int (0-30)
    """
    gap_days = data.get("min_episode_gap_days")
    if gap_days is None:
        raise HTTPException(status_code=400, detail="min_episode_gap_days is required")
    try:
        gap_days = int(gap_days)
        if gap_days < 0 or gap_days > 30:
            raise ValueError
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="min_episode_gap_days must be 0-30")

    # Upsert setting
    result = await db.execute(
        select(Setting).where(
            Setting.user_id == user_id,
            Setting.key == "min_episode_gap_days",
        )
    )
    setting = result.scalar_one_or_none()
    if setting:
        setting.value = str(gap_days)
    else:
        new_setting = Setting(user_id=user_id, key="min_episode_gap_days", value=str(gap_days))
        db.add(new_setting)

    await db.commit()
    return {"min_episode_gap_days": gap_days, "message": "Einstellung gespeichert."}


# ========== PLATFORM LANES ==========

PLATFORM_LANE_ORDER = ["instagram_feed", "instagram_story", "tiktok"]
PLATFORM_LANE_LABELS = {
    "instagram_feed": "IG Feed",
    "instagram_story": "IG Story",
    "tiktok": "TikTok",
}
PLATFORM_LANE_ICONS = {
    "instagram_feed": "\U0001f4f7",   # camera
    "instagram_story": "\U0001f4f1",   # mobile phone
    "tiktok": "\U0001f3b5",            # musical note
}


@router.get("/platform-lanes")
async def get_platform_lanes(
    month: Optional[int] = None,
    year: Optional[int] = None,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get posts for a month grouped by platform lane AND date.

    Returns posts organized as:
    {
        "lanes": [
            {
                "platform": "instagram_feed",
                "label": "IG Feed",
                "icon": "📷",
                "posts_by_date": {"2026-02-13": [...], ...},
                "total": 5
            },
            ...
        ],
        "cross_platform_stats": {
            "instagram_feed": 5,
            "instagram_story": 3,
            "tiktok": 2,
            "total": 10,
            "linked_groups": 2
        }
    }
    """
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

    query = select(Post).where(and_(*conditions)).order_by(Post.scheduled_date)
    result = await db.execute(query)
    posts = result.scalars().all()

    # Group by platform then by date
    lanes = []
    platform_counts = {}
    linked_groups = set()

    for platform in PLATFORM_LANE_ORDER:
        platform_posts = [p for p in posts if p.platform == platform]
        posts_by_date = {}
        for post in platform_posts:
            date_key = post.scheduled_date.strftime("%Y-%m-%d")
            if date_key not in posts_by_date:
                posts_by_date[date_key] = []
            posts_by_date[date_key].append(post_to_calendar_dict(post))
            if post.linked_post_group_id:
                linked_groups.add(post.linked_post_group_id)

        platform_counts[platform] = len(platform_posts)
        lanes.append({
            "platform": platform,
            "label": PLATFORM_LANE_LABELS.get(platform, platform),
            "icon": PLATFORM_LANE_ICONS.get(platform, ""),
            "posts_by_date": posts_by_date,
            "total": len(platform_posts),
        })

    return {
        "lanes": lanes,
        "month": month,
        "year": year,
        "cross_platform_stats": {
            **platform_counts,
            "total": len(posts),
            "linked_groups": len(linked_groups),
        },
    }


@router.get("/cross-platform-stats")
async def get_cross_platform_stats(
    month: Optional[int] = None,
    year: Optional[int] = None,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get cross-platform performance statistics.

    Compares content distribution across platforms for the given month.
    """
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

    # Count per platform
    for platform in PLATFORM_LANE_ORDER:
        pass

    query = select(Post).where(and_(*conditions)).order_by(Post.scheduled_date)
    result = await db.execute(query)
    posts = result.scalars().all()

    platform_data = {}
    category_per_platform = {}
    linked_groups = {}

    for post in posts:
        plat = post.platform
        if plat not in platform_data:
            platform_data[plat] = {"count": 0, "statuses": {}, "categories": {}}
        platform_data[plat]["count"] += 1

        # Status breakdown
        st = post.status or "draft"
        platform_data[plat]["statuses"][st] = platform_data[plat]["statuses"].get(st, 0) + 1

        # Category breakdown
        cat = post.category or "unknown"
        platform_data[plat]["categories"][cat] = platform_data[plat]["categories"].get(cat, 0) + 1

        # Track linked groups
        if post.linked_post_group_id:
            if post.linked_post_group_id not in linked_groups:
                linked_groups[post.linked_post_group_id] = set()
            linked_groups[post.linked_post_group_id].add(plat)

    # Determine platforms with low coverage
    total = len(posts)
    recommendations = []
    for plat in PLATFORM_LANE_ORDER:
        count = platform_data.get(plat, {}).get("count", 0)
        pct = round(count / total * 100, 1) if total > 0 else 0
        if pct < 20:
            recommendations.append({
                "platform": plat,
                "label": PLATFORM_LANE_LABELS.get(plat, plat),
                "count": count,
                "percentage": pct,
                "message": f"Nur {count} Posts ({pct}%) auf {PLATFORM_LANE_LABELS.get(plat, plat)} - mehr Content empfohlen!",
            })

    # Multi-platform coverage
    multi_platform_groups = sum(1 for g in linked_groups.values() if len(g) >= 2)
    all_three_platforms = sum(1 for g in linked_groups.values() if len(g) >= 3)

    return {
        "month": month,
        "year": year,
        "total_posts": total,
        "platforms": {
            plat: {
                "count": platform_data.get(plat, {}).get("count", 0),
                "percentage": round(platform_data.get(plat, {}).get("count", 0) / total * 100, 1) if total > 0 else 0,
                "statuses": platform_data.get(plat, {}).get("statuses", {}),
                "categories": platform_data.get(plat, {}).get("categories", {}),
                "label": PLATFORM_LANE_LABELS.get(plat, plat),
                "icon": PLATFORM_LANE_ICONS.get(plat, ""),
            }
            for plat in PLATFORM_LANE_ORDER
        },
        "multi_platform": {
            "linked_groups": len(linked_groups),
            "multi_platform_groups": multi_platform_groups,
            "all_three_platforms": all_three_platforms,
        },
        "recommendations": recommendations,
    }


# ═══════════════════════════════════════════════════════════════════════
# Recurring Format Placeholders for Calendar (Feature #191)
# ═══════════════════════════════════════════════════════════════════════

DAY_NAME_TO_WEEKDAY = {
    "Montag": 0,
    "Dienstag": 1,
    "Mittwoch": 2,
    "Donnerstag": 3,
    "Freitag": 4,
    "Samstag": 5,
    "Sonntag": 6,
}


@router.get("/recurring-placeholders")
async def get_recurring_placeholders(
    month: Optional[int] = None,
    year: Optional[int] = None,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get recurring format placeholder dates for a given month.

    Returns a list of placeholder objects with date, format info, and whether
    a post already exists on that date (to avoid double-showing).
    """
    import json as json_module

    now = datetime.now()
    target_month = month or now.month
    target_year = year or now.year

    # Get all active recurring formats (system defaults + user's own)
    result = await db.execute(
        select(RecurringFormat).where(
            RecurringFormat.is_active == True,
            or_(
                RecurringFormat.user_id == None,
                RecurringFormat.user_id == user_id,
            ),
        )
    )
    formats = result.scalars().all()

    if not formats:
        return {"placeholders": [], "format_count": 0}

    # Get existing scheduled posts for this month (to mark covered days)
    _, last_day = monthrange(target_year, target_month)
    month_start = datetime(target_year, target_month, 1)
    month_end = datetime(target_year, target_month, last_day, 23, 59, 59)

    posts_result = await db.execute(
        select(Post.scheduled_date, Post.category).where(
            Post.user_id == user_id,
            Post.scheduled_date.isnot(None),
            Post.scheduled_date >= month_start,
            Post.scheduled_date <= month_end,
        )
    )
    existing_posts = posts_result.all()
    posts_by_date = {}
    for p_date, p_cat in existing_posts:
        if p_date:
            date_str = p_date.strftime("%Y-%m-%d")
            if date_str not in posts_by_date:
                posts_by_date[date_str] = []
            posts_by_date[date_str].append(p_cat)

    # Generate placeholders
    placeholders = []

    for fmt in formats:
        if fmt.frequency == "weekly" and fmt.preferred_day:
            weekday = DAY_NAME_TO_WEEKDAY.get(fmt.preferred_day)
            if weekday is None:
                continue

            # Find all dates in this month that match the preferred day
            current = date(target_year, target_month, 1)
            while current.month == target_month:
                if current.weekday() == weekday:
                    date_str = current.isoformat()
                    has_post = date_str in posts_by_date
                    # Check if the existing post matches this format's category
                    category_match = False
                    if has_post and fmt.category:
                        category_match = fmt.category in posts_by_date[date_str]

                    hashtags = []
                    if fmt.hashtags:
                        try:
                            hashtags = json_module.loads(fmt.hashtags)
                        except (json_module.JSONDecodeError, TypeError):
                            hashtags = []

                    placeholders.append({
                        "date": date_str,
                        "format_id": fmt.id,
                        "format_name": fmt.name,
                        "format_icon": fmt.icon,
                        "format_tone": fmt.tone,
                        "format_category": fmt.category,
                        "preferred_time": fmt.preferred_time,
                        "hashtags": hashtags,
                        "has_existing_post": has_post,
                        "category_match": category_match,
                        "is_default": fmt.is_default,
                    })
                current += timedelta(days=1)

        elif fmt.frequency == "biweekly" and fmt.preferred_day:
            weekday = DAY_NAME_TO_WEEKDAY.get(fmt.preferred_day)
            if weekday is None:
                continue

            # Find every other occurrence of the preferred day
            current = date(target_year, target_month, 1)
            occurrence = 0
            while current.month == target_month:
                if current.weekday() == weekday:
                    occurrence += 1
                    if occurrence % 2 == 1:  # 1st, 3rd occurrence
                        date_str = current.isoformat()
                        has_post = date_str in posts_by_date

                        hashtags = []
                        if fmt.hashtags:
                            try:
                                hashtags = json_module.loads(fmt.hashtags)
                            except (json_module.JSONDecodeError, TypeError):
                                hashtags = []

                        placeholders.append({
                            "date": date_str,
                            "format_id": fmt.id,
                            "format_name": fmt.name,
                            "format_icon": fmt.icon,
                            "format_tone": fmt.tone,
                            "format_category": fmt.category,
                            "preferred_time": fmt.preferred_time,
                            "hashtags": hashtags,
                            "has_existing_post": has_post in posts_by_date,
                            "category_match": False,
                            "is_default": fmt.is_default,
                        })
                current += timedelta(days=1)

        elif fmt.frequency == "monthly":
            # Monthly: first occurrence of preferred_day, or 1st of month
            if fmt.preferred_day:
                weekday = DAY_NAME_TO_WEEKDAY.get(fmt.preferred_day)
                if weekday is None:
                    continue
                current = date(target_year, target_month, 1)
                while current.month == target_month:
                    if current.weekday() == weekday:
                        date_str = current.isoformat()
                        has_post = date_str in posts_by_date

                        hashtags = []
                        if fmt.hashtags:
                            try:
                                hashtags = json_module.loads(fmt.hashtags)
                            except (json_module.JSONDecodeError, TypeError):
                                hashtags = []

                        placeholders.append({
                            "date": date_str,
                            "format_id": fmt.id,
                            "format_name": fmt.name,
                            "format_icon": fmt.icon,
                            "format_tone": fmt.tone,
                            "format_category": fmt.category,
                            "preferred_time": fmt.preferred_time,
                            "hashtags": hashtags,
                            "has_existing_post": has_post,
                            "category_match": False,
                            "is_default": fmt.is_default,
                        })
                        break  # Only first occurrence for monthly
                    current += timedelta(days=1)

    # Sort by date
    placeholders.sort(key=lambda p: p["date"])

    return {
        "placeholders": placeholders,
        "format_count": len(formats),
    }


# ========== CALENDAR EXPORT: iCal ==========

@router.get("/export/ical")
async def export_calendar_ical(
    month: Optional[int] = None,
    year: Optional[int] = None,
    platform: Optional[str] = None,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Export scheduled posts as iCalendar (.ics) file.

    Each scheduled post becomes a calendar event with:
    - Summary: Post title
    - Description: Category, platform, country, status, hashtags
    - DTSTART/DTEND: Scheduled date/time (30min duration)
    """
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

    # Build iCal content (RFC 5545)
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//TREFF Sprachreisen//Content Calendar//DE",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:TREFF Content-Kalender {month:02d}/{year}",
    ]

    platform_labels = {
        "instagram_feed": "Instagram Feed",
        "instagram_story": "Instagram Story",
        "tiktok": "TikTok",
    }

    for post in posts:
        dt_date = post.scheduled_date.strftime("%Y%m%d")
        # Parse time or default to 10:00
        hour, minute = 10, 0
        if post.scheduled_time:
            try:
                parts = post.scheduled_time.split(":")
                hour, minute = int(parts[0]), int(parts[1])
            except (ValueError, IndexError):
                pass

        dt_start = f"{dt_date}T{hour:02d}{minute:02d}00"
        # 30 minute event duration
        end_hour = hour
        end_minute = minute + 30
        if end_minute >= 60:
            end_hour += 1
            end_minute -= 60
        if end_hour >= 24:
            end_hour = 23
            end_minute = 59
        dt_end = f"{dt_date}T{end_hour:02d}{end_minute:02d}00"

        uid = f"treff-post-{post.id}@treff-sprachreisen.de"

        plat_label = platform_labels.get(post.platform, post.platform or "")
        description_parts = []
        if post.category:
            description_parts.append(f"Kategorie: {post.category}")
        if plat_label:
            description_parts.append(f"Plattform: {plat_label}")
        if post.country:
            description_parts.append(f"Land: {post.country}")
        if post.status:
            description_parts.append(f"Status: {post.status}")
        if post.hashtags_instagram:
            description_parts.append(f"Hashtags: {post.hashtags_instagram}")

        description = "\\n".join(description_parts)

        summary = (post.title or "Unbenannter Post").replace(",", "\\,")
        description = description.replace(",", "\\,")

        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTART:{dt_start}",
            f"DTEND:{dt_end}",
            f"SUMMARY:{summary}",
            f"DESCRIPTION:{description}",
            f"CATEGORIES:{post.category or ''}",
            f"STATUS:{'CONFIRMED' if post.status == 'scheduled' else 'TENTATIVE'}",
            "END:VEVENT",
        ])

    lines.append("END:VCALENDAR")

    ical_content = "\r\n".join(lines) + "\r\n"

    month_names_en = [
        "january", "february", "march", "april", "may", "june",
        "july", "august", "september", "october", "november", "december",
    ]
    filename = f"TREFF_calendar_{month_names_en[month - 1]}_{year}.ics"

    return Response(
        content=ical_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


# ========== CALENDAR EXPORT: PDF ==========

@router.get("/export/pdf")
async def export_calendar_pdf(
    month: Optional[int] = None,
    year: Optional[int] = None,
    platform: Optional[str] = None,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Export calendar as a printable PDF overview.

    Generates an HTML-based visual weekly overview, then returns it
    as a downloadable HTML file that can be printed to PDF from browser.
    For server-side PDF, a headless browser (Puppeteer) would be needed.
    """
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

    # Group posts by date
    posts_by_date = {}
    for post in posts:
        date_str = post.scheduled_date.strftime("%Y-%m-%d")
        if date_str not in posts_by_date:
            posts_by_date[date_str] = []
        posts_by_date[date_str].append(post)

    # German month names
    month_names_de = [
        "Januar", "Februar", "Maerz", "April", "Mai", "Juni",
        "Juli", "August", "September", "Oktober", "November", "Dezember",
    ]
    month_name = month_names_de[month - 1]

    platform_labels = {
        "instagram_feed": "IG Feed",
        "instagram_story": "IG Story",
        "tiktok": "TikTok",
    }

    category_colors = {
        "laender-spotlight": "#3B82F6",
        "erfahrungsberichte": "#8B5CF6",
        "tipps-checklisten": "#F59E0B",
        "infografiken": "#06B6D4",
        "behind-the-scenes": "#EC4899",
        "countdown-events": "#EF4444",
        "interaktiv": "#10B981",
        "motivation": "#F97316",
        "eltern-content": "#6366F1",
        "partner-schulen": "#14B8A6",
    }

    # Build calendar grid (Monday-based)
    first_day = date(year, month, 1)
    # Monday = 0
    start_weekday = first_day.weekday()
    # Start from Monday of the first week
    grid_start = first_day - timedelta(days=start_weekday)

    weeks_html = ""
    current = grid_start
    for week_num in range(6):
        cells = ""
        for day_num in range(7):
            day_date = current + timedelta(days=week_num * 7 + day_num)
            date_str = day_date.strftime("%Y-%m-%d")
            is_current_month = day_date.month == month

            day_posts = posts_by_date.get(date_str, [])
            posts_html = ""
            for p in day_posts[:3]:  # Max 3 posts per cell
                color = category_colors.get(p.category, "#6B7280")
                plat = platform_labels.get(p.platform, p.platform or "")
                title = (p.title or "Unbenannt")[:25]
                time_str = p.scheduled_time or ""
                posts_html += f'''<div style="background:{color}15;border-left:3px solid {color};padding:2px 4px;margin:1px 0;font-size:9px;border-radius:2px;">
                    <span style="color:{color};font-weight:600;">{time_str}</span>
                    <span style="color:#374151;">{title}</span>
                    <span style="color:#9CA3AF;font-size:8px;">{plat}</span>
                </div>'''
            if len(day_posts) > 3:
                posts_html += f'<div style="font-size:8px;color:#9CA3AF;text-align:center;">+{len(day_posts)-3} mehr</div>'

            opacity = "1" if is_current_month else "0.35"
            bg = "#FFFFFF" if is_current_month else "#F9FAFB"
            cells += f'''<td style="border:1px solid #E5E7EB;padding:3px;vertical-align:top;width:14.28%;height:90px;opacity:{opacity};background:{bg};">
                <div style="font-size:11px;font-weight:600;color:#6B7280;margin-bottom:2px;">{day_date.day}</div>
                {posts_html}
            </td>'''

        weeks_html += f"<tr>{cells}</tr>"

    # Stats summary
    total_posts = len(posts)
    platform_counts = {}
    category_counts = {}
    for p in posts:
        pl = platform_labels.get(p.platform, p.platform or "Sonstige")
        platform_counts[pl] = platform_counts.get(pl, 0) + 1
        category_counts[p.category or "Sonstige"] = category_counts.get(p.category or "Sonstige", 0) + 1

    stats_html = f"<strong>{total_posts} Posts</strong> geplant"
    if platform_counts:
        parts = [f"{v}x {k}" for k, v in sorted(platform_counts.items(), key=lambda x: -x[1])]
        stats_html += " &mdash; " + ", ".join(parts)

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="utf-8">
    <title>TREFF Content-Kalender {month_name} {year}</title>
    <style>
        @page {{ size: A4 landscape; margin: 10mm; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 15px; color: #1F2937; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 2px solid #4C8BC2; }}
        .header h1 {{ margin: 0; font-size: 20px; color: #4C8BC2; }}
        .header .brand {{ font-size: 12px; color: #6B7280; }}
        .stats {{ font-size: 11px; color: #6B7280; margin-bottom: 8px; }}
        table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
        th {{ background: #4C8BC2; color: white; padding: 5px; font-size: 11px; text-align: center; }}
        @media print {{ body {{ padding: 0; }} }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Content-Kalender: {month_name} {year}</h1>
        <div class="brand">TREFF Sprachreisen &bull; Erstellt am {now.strftime('%d.%m.%Y')}</div>
    </div>
    <div class="stats">{stats_html}</div>
    <table>
        <thead>
            <tr>
                <th>Mo</th><th>Di</th><th>Mi</th><th>Do</th><th>Fr</th><th>Sa</th><th>So</th>
            </tr>
        </thead>
        <tbody>
            {weeks_html}
        </tbody>
    </table>
</body>
</html>"""

    month_names_en = [
        "january", "february", "march", "april", "may", "june",
        "july", "august", "september", "october", "november", "december",
    ]
    filename = f"TREFF_calendar_{month_names_en[month - 1]}_{year}.html"

    return Response(
        content=html,
        media_type="text/html",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


# ========== CALENDAR IMPORT: CSV ==========

VALID_PLATFORMS = {"instagram_feed", "instagram_story", "tiktok"}
VALID_CATEGORIES = {
    "laender-spotlight", "erfahrungsberichte", "tipps-checklisten",
    "infografiken", "behind-the-scenes", "countdown-events",
    "interaktiv", "motivation", "eltern-content", "partner-schulen",
}

@router.post("/import/csv/preview")
async def preview_csv_import(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Preview CSV import: parse file, validate, detect duplicates.

    Returns parsed rows with validation status so user can review
    before committing the import.

    Expected CSV columns: date, time, title, category, platform, country, hashtags
    (Flexible: columns can be in any order; extra columns ignored.)
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Nur CSV-Dateien (.csv) werden unterstuetzt.")

    content = await file.read()
    try:
        text = content.decode("utf-8-sig")  # Handle BOM
    except UnicodeDecodeError:
        try:
            text = content.decode("latin-1")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Datei-Encoding nicht erkannt. Bitte UTF-8 verwenden.")

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV-Datei ist leer oder hat keine Kopfzeile.")

    # Map common column name variations
    column_map = {}
    for field in reader.fieldnames:
        fl = field.strip().lower()
        if fl in ("date", "datum"):
            column_map["date"] = field
        elif fl in ("time", "uhrzeit", "zeit"):
            column_map["time"] = field
        elif fl in ("title", "titel"):
            column_map["title"] = field
        elif fl in ("category", "kategorie"):
            column_map["category"] = field
        elif fl in ("platform", "plattform"):
            column_map["platform"] = field
        elif fl in ("country", "land"):
            column_map["country"] = field
        elif fl in ("status",):
            column_map["status"] = field
        elif fl in ("hashtags", "tags"):
            column_map["hashtags"] = field

    if "date" not in column_map:
        raise HTTPException(
            status_code=400,
            detail="CSV muss eine 'date' oder 'Datum' Spalte enthalten."
        )

    # Parse rows
    rows = []
    errors = []
    row_num = 1
    for row in reader:
        row_num += 1
        parsed = {"row_number": row_num, "valid": True, "warnings": [], "errors": []}

        # Date (required)
        date_str = row.get(column_map.get("date", ""), "").strip()
        parsed_date = None
        for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%m/%d/%Y"):
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue
        if not parsed_date:
            parsed["valid"] = False
            parsed["errors"].append(f"Ungueltiges Datum: '{date_str}'")
        parsed["date"] = parsed_date.strftime("%Y-%m-%d") if parsed_date else date_str

        # Time (optional)
        time_str = row.get(column_map.get("time", ""), "").strip()
        if time_str:
            # Validate HH:MM format
            try:
                parts = time_str.replace(".", ":").split(":")
                h, m = int(parts[0]), int(parts[1]) if len(parts) > 1 else 0
                if 0 <= h <= 23 and 0 <= m <= 59:
                    time_str = f"{h:02d}:{m:02d}"
                else:
                    parsed["warnings"].append(f"Ungueltige Uhrzeit: '{time_str}', verwende 10:00")
                    time_str = "10:00"
            except (ValueError, IndexError):
                parsed["warnings"].append(f"Ungueltige Uhrzeit: '{time_str}', verwende 10:00")
                time_str = "10:00"
        else:
            time_str = "10:00"
        parsed["time"] = time_str

        # Title (optional but recommended)
        title = row.get(column_map.get("title", ""), "").strip()
        if not title:
            parsed["warnings"].append("Kein Titel angegeben")
            title = f"Import Post {row_num}"
        parsed["title"] = title

        # Category (optional)
        category = row.get(column_map.get("category", ""), "").strip().lower()
        if category and category not in VALID_CATEGORIES:
            parsed["warnings"].append(f"Unbekannte Kategorie: '{category}', verwende 'laender-spotlight'")
            category = "laender-spotlight"
        elif not category:
            category = "laender-spotlight"
        parsed["category"] = category

        # Platform (optional)
        plat = row.get(column_map.get("platform", ""), "").strip().lower()
        # Normalize platform names
        plat_map = {
            "instagram": "instagram_feed", "ig": "instagram_feed",
            "ig feed": "instagram_feed", "instagram feed": "instagram_feed",
            "ig story": "instagram_story", "instagram story": "instagram_story",
            "story": "instagram_story", "stories": "instagram_story",
            "tiktok": "tiktok", "tt": "tiktok",
        }
        plat = plat_map.get(plat, plat)
        if plat and plat not in VALID_PLATFORMS:
            parsed["warnings"].append(f"Unbekannte Plattform: '{plat}', verwende 'instagram_feed'")
            plat = "instagram_feed"
        elif not plat:
            plat = "instagram_feed"
        parsed["platform"] = plat

        # Country (optional)
        country = row.get(column_map.get("country", ""), "").strip()
        parsed["country"] = country or None

        # Hashtags (optional)
        hashtags = row.get(column_map.get("hashtags", ""), "").strip()
        parsed["hashtags"] = hashtags or None

        rows.append(parsed)

    # Duplicate detection: check for existing posts on same date with same title
    if rows:
        valid_dates = [r["date"] for r in rows if r["valid"]]
        if valid_dates:
            # Find existing posts on those dates
            date_objects = []
            for d in set(valid_dates):
                try:
                    date_objects.append(datetime.strptime(d, "%Y-%m-%d"))
                except ValueError:
                    pass

            if date_objects:
                existing_query = (
                    select(Post)
                    .where(
                        Post.user_id == user_id,
                        Post.scheduled_date.in_(date_objects),
                    )
                )
                existing_result = await db.execute(existing_query)
                existing_posts = existing_result.scalars().all()

                # Build lookup: (date, title_lower) -> True
                existing_set = set()
                for ep in existing_posts:
                    if ep.scheduled_date and ep.title:
                        existing_set.add((
                            ep.scheduled_date.strftime("%Y-%m-%d"),
                            ep.title.lower().strip(),
                        ))

                for r in rows:
                    if r["valid"] and (r["date"], r["title"].lower().strip()) in existing_set:
                        r["duplicate"] = True
                        r["warnings"].append("Moegliches Duplikat: Post mit gleichem Datum und Titel existiert bereits")
                    else:
                        r["duplicate"] = False

    valid_count = sum(1 for r in rows if r["valid"])
    error_count = sum(1 for r in rows if not r["valid"])
    duplicate_count = sum(1 for r in rows if r.get("duplicate"))

    return {
        "columns_detected": list(column_map.keys()),
        "total_rows": len(rows),
        "valid_rows": valid_count,
        "error_rows": error_count,
        "duplicate_rows": duplicate_count,
        "rows": rows,
    }


@router.post("/import/csv")
async def import_csv(
    request: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Import posts from previously previewed CSV data.

    Expects: { "rows": [...], "skip_duplicates": true/false }
    Each row: { date, time, title, category, platform, country, hashtags, valid, duplicate }
    """
    rows = request.get("rows", [])
    skip_duplicates = request.get("skip_duplicates", True)

    if not rows:
        raise HTTPException(status_code=400, detail="Keine Zeilen zum Importieren.")

    imported = 0
    skipped = 0
    errors_list = []

    for row in rows:
        if not row.get("valid", False):
            skipped += 1
            continue

        if skip_duplicates and row.get("duplicate", False):
            skipped += 1
            continue

        try:
            scheduled_date = datetime.strptime(row["date"], "%Y-%m-%d")
        except (ValueError, KeyError):
            errors_list.append(f"Zeile {row.get('row_number', '?')}: Ungueltiges Datum")
            skipped += 1
            continue

        post = Post(
            user_id=user_id,
            title=row.get("title", "Import Post"),
            category=row.get("category", "laender-spotlight"),
            platform=row.get("platform", "instagram_feed"),
            country=row.get("country"),
            status="scheduled",
            scheduled_date=scheduled_date,
            scheduled_time=row.get("time", "10:00"),
            slide_data="[]",
            tone="jugendlich",
        )

        # Set hashtags based on platform
        if row.get("hashtags"):
            if post.platform == "tiktok":
                post.hashtags_tiktok = row["hashtags"]
            else:
                post.hashtags_instagram = row["hashtags"]

        db.add(post)
        imported += 1

    if imported > 0:
        await db.commit()

    return {
        "imported": imported,
        "skipped": skipped,
        "errors": errors_list,
        "message": f"{imported} Posts importiert, {skipped} uebersprungen.",
    }
