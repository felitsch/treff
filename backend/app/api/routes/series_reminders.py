"""Series Reminders API - Automatic notifications for story series scheduling."""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models.user import User
from app.models.story_arc import StoryArc
from app.models.post import Post
from app.models.series_reminder import SeriesReminder

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Default Thresholds ──
DEFAULT_PAUSE_WARNING_DAYS = 3  # Warn after N days without new episode
DEFAULT_UPCOMING_DAYS = 1       # Remind N days before next episode is due


# ── Pydantic Schemas ──

class ReminderOut(BaseModel):
    id: int
    user_id: int
    story_arc_id: int
    reminder_type: str
    title: str
    message: str
    is_read: bool
    is_dismissed: bool
    created_at: str
    arc_title: Optional[str] = None
    arc_status: Optional[str] = None
    arc_country: Optional[str] = None


class ThresholdUpdate(BaseModel):
    pause_warning_days: Optional[int] = None


def reminder_to_dict(reminder: SeriesReminder, arc: Optional[StoryArc] = None) -> dict:
    """Serialize a SeriesReminder to dict."""
    d = {
        "id": reminder.id,
        "user_id": reminder.user_id,
        "story_arc_id": reminder.story_arc_id,
        "reminder_type": reminder.reminder_type,
        "title": reminder.title,
        "message": reminder.message,
        "is_read": reminder.is_read,
        "is_dismissed": reminder.is_dismissed,
        "created_at": reminder.created_at.isoformat() if reminder.created_at else None,
    }
    if arc:
        d["arc_title"] = arc.title
        d["arc_status"] = arc.status
        d["arc_country"] = arc.country
    return d


# ── GET /api/series-reminders ── List all reminders for current user
@router.get("")
async def list_reminders(
    is_read: Optional[bool] = Query(None),
    reminder_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List series reminders for the current user."""
    query = (
        select(SeriesReminder, StoryArc)
        .outerjoin(StoryArc, SeriesReminder.story_arc_id == StoryArc.id)
        .where(SeriesReminder.user_id == user.id)
        .where(SeriesReminder.is_dismissed == False)
    )

    if is_read is not None:
        query = query.where(SeriesReminder.is_read == is_read)
    if reminder_type:
        query = query.where(SeriesReminder.reminder_type == reminder_type)

    query = query.order_by(SeriesReminder.created_at.desc())

    result = await db.execute(query)
    rows = result.all()

    reminders = [reminder_to_dict(r, arc) for r, arc in rows]

    # Count unread
    count_q = (
        select(func.count(SeriesReminder.id))
        .where(SeriesReminder.user_id == user.id)
        .where(SeriesReminder.is_read == False)
        .where(SeriesReminder.is_dismissed == False)
    )
    unread_result = await db.execute(count_q)
    unread_count = unread_result.scalar() or 0

    return {
        "reminders": reminders,
        "count": len(reminders),
        "unread_count": unread_count,
    }


# ── GET /api/series-reminders/unread-count ── Quick badge count
@router.get("/unread-count")
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get count of unread, non-dismissed series reminders."""
    count_q = (
        select(func.count(SeriesReminder.id))
        .where(SeriesReminder.user_id == user.id)
        .where(SeriesReminder.is_read == False)
        .where(SeriesReminder.is_dismissed == False)
    )
    result = await db.execute(count_q)
    count = result.scalar() or 0
    return {"unread_count": count}


# ── PUT /api/series-reminders/{id}/read ── Mark a single reminder as read
@router.put("/{reminder_id}/read")
async def mark_read(
    reminder_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Mark a reminder as read."""
    result = await db.execute(
        select(SeriesReminder).where(
            SeriesReminder.id == reminder_id,
            SeriesReminder.user_id == user.id,
        )
    )
    reminder = result.scalar_one_or_none()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    reminder.is_read = True
    await db.flush()
    return {"success": True, "id": reminder_id}


# ── PUT /api/series-reminders/read-all ── Mark all reminders as read
@router.put("/read-all")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Mark all reminders as read for the current user."""
    from sqlalchemy import update
    await db.execute(
        update(SeriesReminder)
        .where(SeriesReminder.user_id == user.id)
        .where(SeriesReminder.is_read == False)
        .values(is_read=True)
    )
    await db.flush()
    return {"success": True}


# ── PUT /api/series-reminders/{id}/dismiss ── Dismiss a reminder
@router.put("/{reminder_id}/dismiss")
async def dismiss_reminder(
    reminder_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Dismiss a reminder (hide from list, keep in DB)."""
    result = await db.execute(
        select(SeriesReminder).where(
            SeriesReminder.id == reminder_id,
            SeriesReminder.user_id == user.id,
        )
    )
    reminder = result.scalar_one_or_none()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    reminder.is_dismissed = True
    reminder.is_read = True
    await db.flush()
    return {"success": True, "id": reminder_id}


# ── POST /api/series-reminders/check ── Run the series check and generate reminders
@router.post("/check")
async def check_series_reminders(
    pause_warning_days: int = Query(DEFAULT_PAUSE_WARNING_DAYS),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Analyze all active story arcs and generate reminders for:
    - series_paused: Active arc with no new episode for > pause_warning_days
    - upcoming_episode: Next episode is due within 1 day
    - series_ending: Current episode is the second-to-last planned episode
    - gap_warning: Active arc has 0 episodes scheduled in the next 7 days

    Avoids creating duplicate reminders for the same arc + type within 24 hours.
    """
    now = datetime.now(timezone.utc)
    today = now.date()
    new_reminders = []

    # Get all active arcs for this user
    arcs_result = await db.execute(
        select(StoryArc).where(
            StoryArc.user_id == user.id,
            StoryArc.status.in_(["active", "paused"]),
        )
    )
    arcs = arcs_result.scalars().all()

    for arc in arcs:
        # Get episodes (posts linked to this arc)
        episodes_result = await db.execute(
            select(Post).where(
                Post.story_arc_id == arc.id,
                Post.user_id == user.id,
            ).order_by(Post.created_at.desc())
        )
        episodes = episodes_result.scalars().all()

        # Get scheduled future episodes
        scheduled_result = await db.execute(
            select(Post).where(
                Post.story_arc_id == arc.id,
                Post.user_id == user.id,
                Post.scheduled_date != None,
                Post.status.in_(["scheduled", "draft"]),
            ).order_by(Post.scheduled_date.asc())
        )
        scheduled_episodes = scheduled_result.scalars().all()

        # ── Check 1: Series Paused Too Long ──
        if arc.status == "active" and episodes:
            last_episode = episodes[0]  # Most recent by created_at
            last_date = last_episode.created_at
            if last_date:
                if hasattr(last_date, 'date'):
                    if last_date.tzinfo is None:
                        last_date = last_date.replace(tzinfo=timezone.utc)
                    days_since = (now - last_date).days
                else:
                    days_since = (today - last_date).days if hasattr(last_date, 'day') else 0

                if days_since >= pause_warning_days:
                    reminder = await _create_reminder_if_new(
                        db, user.id, arc.id, "series_paused",
                        f"Serie pausiert: {arc.title}",
                        f"{arc.title} hat seit {days_since} Tagen keine neue Episode. Deine Follower vergessen die Story!",
                        now,
                    )
                    if reminder:
                        new_reminders.append(reminder)

        # ── Check 2: Series Paused (status = paused) ──
        if arc.status == "paused":
            reminder = await _create_reminder_if_new(
                db, user.id, arc.id, "series_paused",
                f"Serie pausiert: {arc.title}",
                f"{arc.title} ist pausiert. Setze die Serie fort, um deine Follower nicht zu verlieren!",
                now,
            )
            if reminder:
                new_reminders.append(reminder)

        # ── Check 3: Upcoming Episode (scheduled within 1 day) ──
        for ep in scheduled_episodes:
            if ep.scheduled_date:
                sched_date = ep.scheduled_date
                if hasattr(sched_date, 'date'):
                    sched_date = sched_date.date()
                days_until = (sched_date - today).days
                if 0 <= days_until <= DEFAULT_UPCOMING_DAYS:
                    time_str = f" um {ep.scheduled_time} Uhr" if ep.scheduled_time else ""
                    day_label = "Heute" if days_until == 0 else "Morgen"
                    reminder = await _create_reminder_if_new(
                        db, user.id, arc.id, "upcoming_episode",
                        f"Episode faellig: {arc.title}",
                        f"{day_label} ist Episode \"{ep.title or 'Ohne Titel'}\" fuer {arc.title}{time_str} faellig.",
                        now,
                    )
                    if reminder:
                        new_reminders.append(reminder)
                    break  # Only remind about the next upcoming episode

        # ── Check 4: Series Ending (second-to-last episode) ──
        if arc.planned_episodes > 0 and arc.current_episode >= arc.planned_episodes - 1:
            reminder = await _create_reminder_if_new(
                db, user.id, arc.id, "series_ending",
                f"Letzte Episode: {arc.title}",
                f"Die letzte Episode der Serie \"{arc.title}\" steht an! (Episode {arc.current_episode}/{arc.planned_episodes})",
                now,
            )
            if reminder:
                new_reminders.append(reminder)

        # ── Check 5: Gap Warning (no episodes scheduled in next 7 days) ──
        if arc.status == "active":
            next_week = today + timedelta(days=7)
            has_upcoming = False
            for ep in scheduled_episodes:
                if ep.scheduled_date:
                    sched_date = ep.scheduled_date
                    if hasattr(sched_date, 'date'):
                        sched_date = sched_date.date()
                    if today <= sched_date <= next_week:
                        has_upcoming = True
                        break

            if not has_upcoming and arc.current_episode < arc.planned_episodes:
                reminder = await _create_reminder_if_new(
                    db, user.id, arc.id, "gap_warning",
                    f"Keine Episode geplant: {arc.title}",
                    f"Fuer \"{arc.title}\" ist in den naechsten 7 Tagen keine Episode geplant. Plane die naechste Episode!",
                    now,
                )
                if reminder:
                    new_reminders.append(reminder)

    await db.flush()

    return {
        "checked_arcs": len(arcs),
        "new_reminders": len(new_reminders),
        "reminders": [reminder_to_dict(r) for r in new_reminders],
    }


# ── GET /api/series-reminders/series-status ── Dashboard widget data
@router.get("/series-status")
async def get_series_status(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Get series status overview for dashboard widget.
    Returns active arcs with next due dates and progress info.
    """
    now = datetime.now(timezone.utc)
    today = now.date()

    # Get active + paused arcs
    arcs_result = await db.execute(
        select(StoryArc).where(
            StoryArc.user_id == user.id,
            StoryArc.status.in_(["active", "paused", "draft"]),
        ).order_by(StoryArc.status.asc(), StoryArc.updated_at.desc())
    )
    arcs = arcs_result.scalars().all()

    series_list = []
    for arc in arcs:
        # Count episodes for this arc
        ep_count_result = await db.execute(
            select(func.count(Post.id)).where(
                Post.story_arc_id == arc.id,
                Post.user_id == user.id,
            )
        )
        episode_count = ep_count_result.scalar() or 0

        # Find next scheduled episode
        next_ep_result = await db.execute(
            select(Post).where(
                Post.story_arc_id == arc.id,
                Post.user_id == user.id,
                Post.scheduled_date != None,
                Post.status.in_(["scheduled", "draft"]),
            ).order_by(Post.scheduled_date.asc()).limit(1)
        )
        next_episode = next_ep_result.scalar_one_or_none()

        # Find last episode
        last_ep_result = await db.execute(
            select(Post).where(
                Post.story_arc_id == arc.id,
                Post.user_id == user.id,
            ).order_by(Post.created_at.desc()).limit(1)
        )
        last_episode = last_ep_result.scalar_one_or_none()

        # Calculate days since last episode
        days_since_last = None
        if last_episode and last_episode.created_at:
            last_date = last_episode.created_at
            if hasattr(last_date, 'date'):
                if last_date.tzinfo is None:
                    last_date = last_date.replace(tzinfo=timezone.utc)
                days_since_last = (now - last_date).days
            elif hasattr(last_date, 'day'):
                days_since_last = (today - last_date).days

        # Next episode info
        next_due_date = None
        next_due_time = None
        days_until_next = None
        if next_episode and next_episode.scheduled_date:
            sched_date = next_episode.scheduled_date
            if hasattr(sched_date, 'date'):
                sched_date = sched_date.date()
            next_due_date = str(sched_date)
            next_due_time = next_episode.scheduled_time
            days_until_next = (sched_date - today).days

        progress_pct = round((arc.current_episode / arc.planned_episodes) * 100) if arc.planned_episodes > 0 else 0

        series_list.append({
            "id": arc.id,
            "title": arc.title,
            "subtitle": arc.subtitle,
            "status": arc.status,
            "country": arc.country,
            "planned_episodes": arc.planned_episodes,
            "current_episode": arc.current_episode,
            "episode_count": episode_count,
            "progress_percent": progress_pct,
            "days_since_last_episode": days_since_last,
            "next_due_date": next_due_date,
            "next_due_time": next_due_time,
            "days_until_next": days_until_next,
        })

    # Summary stats
    active_count = sum(1 for s in series_list if s["status"] == "active")
    paused_count = sum(1 for s in series_list if s["status"] == "paused")
    overdue_count = sum(1 for s in series_list if s["status"] == "active" and s["days_since_last_episode"] is not None and s["days_since_last_episode"] >= DEFAULT_PAUSE_WARNING_DAYS)

    return {
        "series": series_list,
        "count": len(series_list),
        "active_count": active_count,
        "paused_count": paused_count,
        "overdue_count": overdue_count,
    }


async def _create_reminder_if_new(
    db: AsyncSession,
    user_id: int,
    arc_id: int,
    reminder_type: str,
    title: str,
    message: str,
    now: datetime,
) -> Optional[SeriesReminder]:
    """Create a reminder only if no similar one exists in the last 24 hours."""
    cutoff = now - timedelta(hours=24)

    # Check for recent duplicate
    existing = await db.execute(
        select(SeriesReminder).where(
            SeriesReminder.user_id == user_id,
            SeriesReminder.story_arc_id == arc_id,
            SeriesReminder.reminder_type == reminder_type,
            SeriesReminder.created_at >= cutoff,
        )
    )
    if existing.scalar_one_or_none():
        return None  # Already reminded recently

    reminder = SeriesReminder(
        user_id=user_id,
        story_arc_id=arc_id,
        reminder_type=reminder_type,
        title=title,
        message=message,
        is_read=False,
        is_dismissed=False,
        created_at=now,
    )
    db.add(reminder)
    return reminder
