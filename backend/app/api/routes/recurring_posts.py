"""Recurring Posts routes.

Manages recurring post rules: create, list, update, delete,
and generate post instances from rules.
"""

import json
from typing import Optional
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.post import Post
from app.models.recurring_post_rule import RecurringPostRule

router = APIRouter()

WEEKDAY_NAMES_DE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
FREQUENCY_LABELS = {
    "weekly": "Woechentlich",
    "biweekly": "Alle 2 Wochen",
    "monthly": "Monatlich",
}


def rule_to_dict(rule: RecurringPostRule) -> dict:
    """Convert a RecurringPostRule model to a dict."""
    return {
        "id": rule.id,
        "user_id": rule.user_id,
        "source_post_id": rule.source_post_id,
        "frequency": rule.frequency,
        "frequency_label": FREQUENCY_LABELS.get(rule.frequency, rule.frequency),
        "weekday": rule.weekday,
        "weekday_label": WEEKDAY_NAMES_DE[rule.weekday] if rule.weekday is not None and 0 <= rule.weekday <= 6 else None,
        "day_of_month": rule.day_of_month,
        "time": rule.time,
        "end_date": rule.end_date.isoformat() if rule.end_date else None,
        "max_occurrences": rule.max_occurrences,
        "is_active": rule.is_active,
        "generated_count": rule.generated_count,
        "last_generated_date": rule.last_generated_date.isoformat() if rule.last_generated_date else None,
        "created_at": rule.created_at.isoformat() if rule.created_at else None,
        "updated_at": rule.updated_at.isoformat() if rule.updated_at else None,
    }


@router.get("")
async def list_recurring_rules(
    is_active: Optional[bool] = None,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List all recurring post rules for current user."""
    conditions = [RecurringPostRule.user_id == user_id]
    if is_active is not None:
        conditions.append(RecurringPostRule.is_active == is_active)

    query = (
        select(RecurringPostRule)
        .where(and_(*conditions))
        .order_by(RecurringPostRule.created_at.desc())
    )
    result = await db.execute(query)
    rules = result.scalars().all()

    # Enrich with source post info
    enriched = []
    for rule in rules:
        d = rule_to_dict(rule)
        # Fetch source post title
        post_result = await db.execute(
            select(Post).where(Post.id == rule.source_post_id)
        )
        source_post = post_result.scalar_one_or_none()
        d["source_post_title"] = source_post.title if source_post else None
        d["source_post_category"] = source_post.category if source_post else None
        d["source_post_platform"] = source_post.platform if source_post else None
        enriched.append(d)

    return enriched


@router.get("/{rule_id}")
async def get_recurring_rule(
    rule_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific recurring rule with source post details."""
    result = await db.execute(
        select(RecurringPostRule).where(
            RecurringPostRule.id == rule_id,
            RecurringPostRule.user_id == user_id,
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Wiederkehr-Regel nicht gefunden")

    d = rule_to_dict(rule)

    # Enrich with source post
    post_result = await db.execute(
        select(Post).where(Post.id == rule.source_post_id)
    )
    source_post = post_result.scalar_one_or_none()
    if source_post:
        d["source_post_title"] = source_post.title
        d["source_post_category"] = source_post.category
        d["source_post_platform"] = source_post.platform

    return d


@router.post("")
async def create_recurring_rule(
    request: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a recurring rule for a post.

    Body:
    {
        "source_post_id": int,
        "frequency": "weekly" | "biweekly" | "monthly",
        "weekday": 0-6 (optional, for weekly/biweekly),
        "day_of_month": 1-28 (optional, for monthly),
        "time": "HH:MM",
        "end_date": "YYYY-MM-DD" (optional),
        "max_occurrences": int (optional),
        "generate_ahead_weeks": int (default 4, how many weeks to pre-generate)
    }
    """
    source_post_id = request.get("source_post_id")
    frequency = request.get("frequency")
    weekday = request.get("weekday")
    day_of_month = request.get("day_of_month")
    time_str = request.get("time", "10:00")
    end_date_str = request.get("end_date")
    max_occurrences = request.get("max_occurrences")
    generate_ahead_weeks = request.get("generate_ahead_weeks", 4)

    # Validate source post
    if not source_post_id:
        raise HTTPException(status_code=400, detail="source_post_id ist erforderlich")

    post_result = await db.execute(
        select(Post).where(Post.id == source_post_id, Post.user_id == user_id)
    )
    source_post = post_result.scalar_one_or_none()
    if not source_post:
        raise HTTPException(status_code=404, detail="Quell-Post nicht gefunden")

    # Validate frequency
    if frequency not in ("weekly", "biweekly", "monthly"):
        raise HTTPException(status_code=400, detail="frequency muss 'weekly', 'biweekly' oder 'monthly' sein")

    # Validate weekday for weekly/biweekly
    if frequency in ("weekly", "biweekly"):
        if weekday is None:
            # Default to source post's scheduled day, or Monday
            if source_post.scheduled_date:
                weekday = source_post.scheduled_date.weekday()
            else:
                weekday = 0
        if not (0 <= weekday <= 6):
            raise HTTPException(status_code=400, detail="weekday muss 0-6 sein (Mo-So)")

    # Validate day_of_month for monthly
    if frequency == "monthly":
        if day_of_month is None:
            if source_post.scheduled_date:
                day_of_month = min(source_post.scheduled_date.day, 28)
            else:
                day_of_month = 1
        if not (1 <= day_of_month <= 28):
            raise HTTPException(status_code=400, detail="day_of_month muss 1-28 sein")

    # Parse end_date
    end_date = None
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Ungueltiges end_date Format (YYYY-MM-DD)")

    # Create rule
    rule = RecurringPostRule(
        user_id=user_id,
        source_post_id=source_post_id,
        frequency=frequency,
        weekday=weekday,
        day_of_month=day_of_month,
        time=time_str,
        end_date=end_date,
        max_occurrences=max_occurrences,
        is_active=True,
    )
    db.add(rule)
    await db.flush()
    await db.refresh(rule)

    # Mark source post as having a recurring rule
    source_post.recurring_rule_id = rule.id

    # Auto-generate instances
    generated = await _generate_instances(db, rule, source_post, generate_ahead_weeks)

    await db.commit()

    result_dict = rule_to_dict(rule)
    result_dict["source_post_title"] = source_post.title
    result_dict["generated_instances"] = generated

    return result_dict


@router.put("/{rule_id}")
async def update_recurring_rule(
    rule_id: int,
    request: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update a recurring rule. Only updates the rule itself.

    Use 'apply_to': 'all_future' to also update all future generated instances.
    """
    result = await db.execute(
        select(RecurringPostRule).where(
            RecurringPostRule.id == rule_id,
            RecurringPostRule.user_id == user_id,
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Wiederkehr-Regel nicht gefunden")

    apply_to = request.get("apply_to", "rule_only")  # "rule_only" or "all_future"

    # Update fields
    if "frequency" in request:
        rule.frequency = request["frequency"]
    if "weekday" in request:
        rule.weekday = request["weekday"]
    if "day_of_month" in request:
        rule.day_of_month = request["day_of_month"]
    if "time" in request:
        rule.time = request["time"]
    if "end_date" in request:
        if request["end_date"]:
            rule.end_date = datetime.strptime(request["end_date"], "%Y-%m-%d")
        else:
            rule.end_date = None
    if "max_occurrences" in request:
        rule.max_occurrences = request["max_occurrences"]
    if "is_active" in request:
        rule.is_active = request["is_active"]

    # If applying to all future instances, update their scheduled times
    if apply_to == "all_future" and "time" in request:
        today = datetime.now()
        future_posts_result = await db.execute(
            select(Post).where(
                Post.recurring_rule_id == rule_id,
                Post.is_recurring_instance == 1,
                Post.user_id == user_id,
                Post.scheduled_date > today,
                Post.status.in_(["draft", "scheduled"]),
            )
        )
        future_posts = future_posts_result.scalars().all()
        for fp in future_posts:
            fp.scheduled_time = request["time"]

    await db.commit()

    return rule_to_dict(rule)


@router.delete("/{rule_id}")
async def delete_recurring_rule(
    rule_id: int,
    delete_future: bool = False,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a recurring rule.

    If delete_future=True, also deletes all future auto-generated instances.
    Otherwise, future instances remain as standalone posts.
    """
    result = await db.execute(
        select(RecurringPostRule).where(
            RecurringPostRule.id == rule_id,
            RecurringPostRule.user_id == user_id,
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Wiederkehr-Regel nicht gefunden")

    deleted_instances = 0

    if delete_future:
        today = datetime.now()
        future_result = await db.execute(
            select(Post).where(
                Post.recurring_rule_id == rule_id,
                Post.is_recurring_instance == 1,
                Post.user_id == user_id,
                Post.scheduled_date > today,
                Post.status.in_(["draft", "scheduled"]),
            )
        )
        future_posts = future_result.scalars().all()
        for fp in future_posts:
            await db.delete(fp)
            deleted_instances += 1
    else:
        # Unlink posts from rule but keep them
        linked_result = await db.execute(
            select(Post).where(
                Post.recurring_rule_id == rule_id,
                Post.user_id == user_id,
            )
        )
        for lp in linked_result.scalars().all():
            lp.recurring_rule_id = None
            lp.is_recurring_instance = None

    # Unlink source post
    source_result = await db.execute(
        select(Post).where(Post.id == rule.source_post_id)
    )
    source_post = source_result.scalar_one_or_none()
    if source_post:
        source_post.recurring_rule_id = None

    await db.delete(rule)
    await db.commit()

    return {
        "deleted": True,
        "rule_id": rule_id,
        "deleted_future_instances": deleted_instances,
    }


@router.post("/{rule_id}/generate")
async def generate_instances(
    rule_id: int,
    request: dict = None,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Manually generate instances for a recurring rule.

    Body (optional): { "weeks_ahead": 4 }
    """
    if request is None:
        request = {}

    result = await db.execute(
        select(RecurringPostRule).where(
            RecurringPostRule.id == rule_id,
            RecurringPostRule.user_id == user_id,
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Wiederkehr-Regel nicht gefunden")

    if not rule.is_active:
        raise HTTPException(status_code=400, detail="Regel ist deaktiviert")

    # Get source post
    post_result = await db.execute(
        select(Post).where(Post.id == rule.source_post_id)
    )
    source_post = post_result.scalar_one_or_none()
    if not source_post:
        raise HTTPException(status_code=404, detail="Quell-Post nicht mehr vorhanden")

    weeks_ahead = request.get("weeks_ahead", 4)
    generated = await _generate_instances(db, rule, source_post, weeks_ahead)
    await db.commit()

    return {
        "rule_id": rule_id,
        "generated_instances": generated,
        "total_generated": rule.generated_count,
    }


@router.put("/instance/{post_id}")
async def update_recurring_instance(
    post_id: int,
    request: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update a single recurring post instance or all future instances.

    Body: { "apply_to": "this_only" | "all_future", "title": "...", "scheduled_time": "HH:MM", ... }
    """
    result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post nicht gefunden")

    apply_to = request.get("apply_to", "this_only")

    # Fields that can be updated
    updatable = ["title", "scheduled_time", "category", "platform", "country", "tone"]
    changes = {}
    for field in updatable:
        if field in request:
            changes[field] = request[field]

    if not changes:
        return {"updated": 0, "message": "Keine Aenderungen"}

    if apply_to == "this_only":
        for field, value in changes.items():
            setattr(post, field, value)
        await db.commit()
        return {"updated": 1, "message": "Dieser Post wurde aktualisiert"}

    elif apply_to == "all_future" and post.recurring_rule_id:
        # Update this post and all future instances of the same rule
        today = datetime.now()
        future_result = await db.execute(
            select(Post).where(
                Post.recurring_rule_id == post.recurring_rule_id,
                Post.is_recurring_instance == 1,
                Post.user_id == user_id,
                Post.scheduled_date >= (post.scheduled_date or today),
                Post.status.in_(["draft", "scheduled"]),
            )
        )
        future_posts = future_result.scalars().all()
        count = 0
        for fp in future_posts:
            for field, value in changes.items():
                setattr(fp, field, value)
            count += 1

        # Also update the rule's time if scheduled_time changed
        if "scheduled_time" in changes and post.recurring_rule_id:
            rule_result = await db.execute(
                select(RecurringPostRule).where(
                    RecurringPostRule.id == post.recurring_rule_id
                )
            )
            rule = rule_result.scalar_one_or_none()
            if rule:
                rule.time = changes["scheduled_time"]

        await db.commit()
        return {"updated": count, "message": f"{count} Posts aktualisiert (alle zukuenftigen)"}

    return {"updated": 0, "message": "Ungueltige apply_to Option"}


# ========== HELPER: Generate instances ==========

async def _generate_instances(
    db: AsyncSession,
    rule: RecurringPostRule,
    source_post: Post,
    weeks_ahead: int = 4,
) -> int:
    """Generate post instances for a recurring rule.

    Creates draft posts for the next `weeks_ahead` weeks based on the rule.
    Skips dates that already have an instance.
    """
    today = date.today()
    end_date = today + timedelta(weeks=weeks_ahead)

    # Check rule end conditions
    if rule.end_date and rule.end_date.date() < end_date:
        end_date = rule.end_date.date()
    if rule.end_date and rule.end_date.date() < today:
        return 0  # Rule has expired

    # Get existing instance dates to avoid duplicates
    existing_result = await db.execute(
        select(Post.scheduled_date).where(
            Post.recurring_rule_id == rule.id,
            Post.is_recurring_instance == 1,
        )
    )
    existing_dates = set()
    for row in existing_result:
        if row[0]:
            existing_dates.add(row[0].date() if isinstance(row[0], datetime) else row[0])

    # Calculate target dates
    target_dates = _calculate_dates(rule, today, end_date)

    # Check max_occurrences
    if rule.max_occurrences:
        remaining = rule.max_occurrences - rule.generated_count
        if remaining <= 0:
            return 0
        target_dates = target_dates[:remaining]

    generated = 0
    for target_date in target_dates:
        if target_date in existing_dates:
            continue
        if target_date <= today:
            continue

        # Create instance post (copy from source)
        instance = Post(
            user_id=source_post.user_id,
            template_id=source_post.template_id,
            category=source_post.category,
            country=source_post.country,
            platform=source_post.platform,
            status="scheduled",
            title=source_post.title,
            slide_data=source_post.slide_data,
            caption_instagram=source_post.caption_instagram,
            caption_tiktok=source_post.caption_tiktok,
            hashtags_instagram=source_post.hashtags_instagram,
            hashtags_tiktok=source_post.hashtags_tiktok,
            cta_text=source_post.cta_text,
            custom_colors=source_post.custom_colors,
            custom_fonts=source_post.custom_fonts,
            tone=source_post.tone,
            scheduled_date=datetime(target_date.year, target_date.month, target_date.day),
            scheduled_time=rule.time,
            recurring_rule_id=rule.id,
            is_recurring_instance=1,
        )
        db.add(instance)
        generated += 1

    # Update rule stats
    rule.generated_count += generated
    if generated > 0:
        rule.last_generated_date = datetime.now()

    return generated


def _calculate_dates(rule: RecurringPostRule, start: date, end: date) -> list:
    """Calculate all target dates for a rule between start and end."""
    dates = []

    if rule.frequency == "weekly":
        # Find next occurrence of weekday after start
        current = start
        days_ahead = (rule.weekday - current.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7  # Skip today, start from next week
        current = current + timedelta(days=days_ahead)
        while current <= end:
            dates.append(current)
            current += timedelta(weeks=1)

    elif rule.frequency == "biweekly":
        current = start
        days_ahead = (rule.weekday - current.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 14
        current = current + timedelta(days=days_ahead)
        while current <= end:
            dates.append(current)
            current += timedelta(weeks=2)

    elif rule.frequency == "monthly":
        # Target day_of_month for each remaining month
        current_month = start.month
        current_year = start.year

        for _ in range(12):  # Max 12 months ahead
            try:
                target = date(current_year, current_month, rule.day_of_month)
            except ValueError:
                # Day doesn't exist in this month (e.g., Feb 30)
                target = None

            if target and start < target <= end:
                dates.append(target)

            # Next month
            current_month += 1
            if current_month > 12:
                current_month = 1
                current_year += 1

    return sorted(dates)
