"""Smart Scheduling API — AI-powered posting time suggestions."""

import logging
from collections import Counter, defaultdict
from datetime import datetime, date, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, extract

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.post import Post

router = APIRouter()
logger = logging.getLogger(__name__)


# ─── Platform-specific best practices ─────────────────────────────
# Based on social-media research for German teen/parent audiences

PLATFORM_BEST_TIMES = {
    "instagram_feed": {
        "best_hours": [9, 12, 17, 18, 19, 20],
        "peak_hours": [17, 18, 19],
        "best_days": [1, 2, 3, 4],  # Mon-Thu (0=Mon)
        "peak_days": [2, 3],  # Wed, Thu
        "max_per_day": 1,
        "label": "Instagram Feed",
        "tip": "Abends zwischen 17-19 Uhr erreichst du die meisten Schueler und Eltern.",
    },
    "instagram_story": {
        "best_hours": [8, 9, 12, 13, 17, 18, 19, 20, 21],
        "peak_hours": [12, 19, 20],
        "best_days": [0, 1, 2, 3, 4],  # Mon-Fri
        "peak_days": [1, 3],  # Tue, Thu
        "max_per_day": 3,
        "label": "Instagram Story",
        "tip": "Stories haben hoehere Frequenz-Toleranz. 2-3 pro Tag sind ideal.",
    },
    "tiktok": {
        "best_hours": [7, 8, 12, 15, 16, 17, 18, 19, 20, 21],
        "peak_hours": [17, 18, 19, 20],
        "best_days": [1, 3, 4],  # Tue, Thu, Fri
        "peak_days": [3, 4],  # Thu, Fri
        "max_per_day": 2,
        "label": "TikTok",
        "tip": "TikTok-Nutzer sind abends am aktivsten. Donnerstag und Freitag sind ideal.",
    },
}

DAY_NAMES_DE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
DAY_NAMES_FULL_DE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]


# ─── Schemas ──────────────────────────────────────────────────────

class SmartScheduleRequest(BaseModel):
    platform: str = Field("instagram_feed", description="Platform: instagram_feed, instagram_story, tiktok")
    target_date: Optional[str] = Field(None, description="Target date (YYYY-MM-DD), defaults to today+1")


# ─── GET /api/ai/smart-schedule — Get scheduling suggestions ─────

@router.get("/smart-schedule")
async def get_smart_schedule(
    platform: str = Query("instagram_feed"),
    target_date: Optional[str] = Query(None, description="Target date YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    Returns smart scheduling suggestions:
    - Heatmap data (7 days x 24 hours) with scores
    - Best time slot recommendation
    - Existing scheduled posts for conflict detection
    - Platform-specific tips
    - Over-posting warnings
    """
    # Resolve target date
    if target_date:
        try:
            t_date = date.fromisoformat(target_date)
        except ValueError:
            t_date = date.today() + timedelta(days=1)
    else:
        t_date = date.today() + timedelta(days=1)

    # Get platform config
    platform_config = PLATFORM_BEST_TIMES.get(platform, PLATFORM_BEST_TIMES["instagram_feed"])

    # ── 1. Analyze historical posting patterns ────────────────────
    result = await db.execute(
        select(Post.scheduled_date, Post.scheduled_time, Post.platform)
        .where(
            Post.user_id == user_id,
            Post.scheduled_date != None,
        )
        .order_by(Post.scheduled_date.desc())
        .limit(200)
    )
    past_posts = result.all()

    # Count posts by hour and day-of-week
    hour_counts = Counter()
    day_counts = Counter()
    for p in past_posts:
        if p.scheduled_time:
            try:
                hour = int(p.scheduled_time.split(":")[0])
                hour_counts[hour] += 1
            except (ValueError, IndexError):
                pass
        if p.scheduled_date:
            sd = p.scheduled_date
            if hasattr(sd, 'weekday'):
                day_counts[sd.weekday()] += 1

    # ── 2. Build heatmap (7 days x 24 hours) ─────────────────────
    heatmap = []
    for day in range(7):
        day_data = {
            "day": day,
            "day_name": DAY_NAMES_DE[day],
            "day_name_full": DAY_NAMES_FULL_DE[day],
            "hours": [],
        }
        for hour in range(24):
            # Score: combination of platform best-practice + historical
            score = 0

            # Base: 0 for night hours
            if hour < 6 or hour > 22:
                score = 0
            else:
                # Best-practice score (0-50)
                if hour in platform_config["peak_hours"]:
                    score += 50
                elif hour in platform_config["best_hours"]:
                    score += 30
                else:
                    score += 10

                # Day-of-week bonus (0-30)
                if day in platform_config["peak_days"]:
                    score += 30
                elif day in platform_config["best_days"]:
                    score += 15

                # Historical boost (0-20)
                if hour_counts.get(hour, 0) > 0:
                    score += min(20, hour_counts[hour] * 5)

            day_data["hours"].append({
                "hour": hour,
                "score": min(100, score),
                "label": f"{hour:02d}:00",
            })
        heatmap.append(day_data)

    # ── 3. Find best time slot ────────────────────────────────────
    target_weekday = t_date.weekday()
    best_hour = None
    best_score = -1
    for h_data in heatmap[target_weekday]["hours"]:
        if h_data["score"] > best_score:
            best_score = h_data["score"]
            best_hour = h_data["hour"]

    # ── 4. Get existing scheduled posts for target date range ─────
    # Show posts for 7 days around target date
    range_start = t_date - timedelta(days=1)
    range_end = t_date + timedelta(days=6)

    scheduled_result = await db.execute(
        select(Post.id, Post.title, Post.platform, Post.scheduled_date, Post.scheduled_time, Post.status)
        .where(
            Post.user_id == user_id,
            Post.scheduled_date != None,
            Post.scheduled_date >= datetime.combine(range_start, datetime.min.time()),
            Post.scheduled_date <= datetime.combine(range_end, datetime.max.time()),
        )
        .order_by(Post.scheduled_date, Post.scheduled_time)
    )
    scheduled_posts = []
    for p in scheduled_result.all():
        scheduled_posts.append({
            "id": p.id,
            "title": p.title,
            "platform": p.platform,
            "date": p.scheduled_date.strftime("%Y-%m-%d") if p.scheduled_date else None,
            "time": p.scheduled_time,
            "status": p.status,
        })

    # ── 5. Check for conflicts on target date ─────────────────────
    posts_on_target = [p for p in scheduled_posts if p["date"] == t_date.isoformat()]
    same_platform_count = sum(1 for p in posts_on_target if p["platform"] == platform)

    warnings = []
    if same_platform_count >= platform_config["max_per_day"]:
        warnings.append({
            "type": "over_posting",
            "severity": "warning",
            "message": f"Am {t_date.strftime('%d.%m.%Y')} ist bereits {same_platform_count} Post fuer {platform_config['label']} geplant. Mehr als {platform_config['max_per_day']}x pro Tag kann die Reichweite reduzieren.",
        })

    # Check time conflicts (same hour)
    if best_hour is not None:
        for p in posts_on_target:
            if p["time"]:
                try:
                    p_hour = int(p["time"].split(":")[0])
                    if abs(p_hour - best_hour) < 2:
                        warnings.append({
                            "type": "time_conflict",
                            "severity": "info",
                            "message": f"Um {p['time']} ist bereits '{p['title'] or 'Post'}' geplant. Mindestens 2 Stunden Abstand empfohlen.",
                        })
                except (ValueError, IndexError):
                    pass

    # Weekend warning
    if target_weekday >= 5:
        warnings.append({
            "type": "weekend",
            "severity": "info",
            "message": f"Am Wochenende ist die Reichweite fuer {platform_config['label']} typischerweise geringer. Werktage erzielen bessere Ergebnisse.",
        })

    # ── 6. Build recommended time slots ───────────────────────────
    recommended_slots = []
    target_day_hours = heatmap[target_weekday]["hours"]
    sorted_hours = sorted(target_day_hours, key=lambda h: h["score"], reverse=True)

    for h in sorted_hours[:5]:
        if h["score"] > 0:
            # Check if this slot conflicts with existing posts
            conflicts_with = None
            for p in posts_on_target:
                if p["time"]:
                    try:
                        p_hour = int(p["time"].split(":")[0])
                        if p_hour == h["hour"]:
                            conflicts_with = p["title"] or "Post"
                    except (ValueError, IndexError):
                        pass

            label = "Optimal" if h["score"] >= 70 else "Gut" if h["score"] >= 40 else "Moeglich"
            recommended_slots.append({
                "hour": h["hour"],
                "time": f"{h['hour']:02d}:00",
                "score": h["score"],
                "label": label,
                "conflict": conflicts_with,
            })

    return {
        "target_date": t_date.isoformat(),
        "target_weekday": target_weekday,
        "target_day_name": DAY_NAMES_FULL_DE[target_weekday],
        "platform": platform,
        "platform_label": platform_config["label"],

        # Best single recommendation
        "best_time": f"{best_hour:02d}:00" if best_hour is not None else "17:00",
        "best_score": best_score,

        # Heatmap data
        "heatmap": heatmap,

        # Top 5 recommended time slots
        "recommended_slots": recommended_slots,

        # Already scheduled posts nearby
        "scheduled_posts": scheduled_posts,
        "posts_on_target_date": len(posts_on_target),

        # Warnings
        "warnings": warnings,

        # Platform tips
        "platform_tip": platform_config["tip"],
        "max_per_day": platform_config["max_per_day"],
    }
