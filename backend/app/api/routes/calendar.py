"""Calendar routes."""

import csv
import io
from typing import Optional
from datetime import datetime, date, timedelta
from calendar import monthrange
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, extract, func

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.post import Post
from app.models.setting import Setting
from app.models.story_arc import StoryArc

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
