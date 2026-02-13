"""Recurring Formats CRUD routes."""

import json
import logging
from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.recurring_format import RecurringFormat

logger = logging.getLogger(__name__)
router = APIRouter()


class RecurringFormatCreate(BaseModel):
    name: str
    description: str
    frequency: str = "weekly"  # daily, weekly, biweekly, monthly
    preferred_day: Optional[str] = None
    preferred_time: Optional[str] = None
    tone: Optional[str] = None
    template_id: Optional[int] = None
    hashtags: Optional[list[str]] = None
    icon: Optional[str] = None
    category: Optional[str] = None
    is_active: bool = True


class RecurringFormatUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    frequency: Optional[str] = None
    preferred_day: Optional[str] = None
    preferred_time: Optional[str] = None
    tone: Optional[str] = None
    template_id: Optional[int] = None
    hashtags: Optional[list[str]] = None
    icon: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None


def recurring_format_to_dict(rf: RecurringFormat) -> dict:
    """Convert a RecurringFormat model to a dict."""
    hashtags = []
    if rf.hashtags:
        try:
            hashtags = json.loads(rf.hashtags)
        except (json.JSONDecodeError, TypeError):
            hashtags = []
    return {
        "id": rf.id,
        "name": rf.name,
        "description": rf.description,
        "frequency": rf.frequency,
        "preferred_day": rf.preferred_day,
        "preferred_time": rf.preferred_time,
        "tone": rf.tone,
        "template_id": rf.template_id,
        "hashtags": hashtags,
        "icon": rf.icon,
        "category": rf.category,
        "is_active": rf.is_active,
        "is_default": rf.is_default,
        "user_id": rf.user_id,
        "created_at": rf.created_at.isoformat() if rf.created_at else None,
        "updated_at": rf.updated_at.isoformat() if rf.updated_at else None,
    }


@router.get("")
async def list_recurring_formats(
    frequency: Optional[str] = None,
    is_active: Optional[bool] = None,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List all recurring formats (system defaults + user-created).

    Optional filters: frequency (daily/weekly/biweekly/monthly), is_active (true/false).
    """
    query = select(RecurringFormat).where(
        or_(
            RecurringFormat.user_id == None,  # System defaults visible to all
            RecurringFormat.user_id == user_id,  # User's own formats
        )
    )

    if frequency:
        query = query.where(RecurringFormat.frequency == frequency)
    if is_active is not None:
        query = query.where(RecurringFormat.is_active == is_active)

    query = query.order_by(RecurringFormat.is_default.desc(), RecurringFormat.name)

    result = await db.execute(query)
    formats = result.scalars().all()

    return [recurring_format_to_dict(rf) for rf in formats]


@router.get("/{format_id}")
async def get_recurring_format(
    format_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a single recurring format by ID."""
    result = await db.execute(
        select(RecurringFormat).where(
            RecurringFormat.id == format_id,
            or_(
                RecurringFormat.user_id == None,
                RecurringFormat.user_id == user_id,
            ),
        )
    )
    rf = result.scalar_one_or_none()
    if not rf:
        raise HTTPException(status_code=404, detail="Recurring format not found")
    return recurring_format_to_dict(rf)


@router.post("", status_code=201)
async def create_recurring_format(
    data: RecurringFormatCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a new recurring format."""
    rf = RecurringFormat(
        name=data.name,
        description=data.description,
        frequency=data.frequency,
        preferred_day=data.preferred_day,
        preferred_time=data.preferred_time,
        tone=data.tone,
        template_id=data.template_id,
        hashtags=json.dumps(data.hashtags) if data.hashtags else None,
        icon=data.icon,
        category=data.category,
        is_active=data.is_active,
        is_default=False,  # User-created formats are never system defaults
        user_id=user_id,
    )
    db.add(rf)
    await db.commit()
    await db.refresh(rf)
    return recurring_format_to_dict(rf)


@router.put("/{format_id}")
async def update_recurring_format(
    format_id: int,
    data: RecurringFormatUpdate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update a recurring format. System defaults can be modified (e.g. activate/deactivate)."""
    result = await db.execute(
        select(RecurringFormat).where(
            RecurringFormat.id == format_id,
            or_(
                RecurringFormat.user_id == None,
                RecurringFormat.user_id == user_id,
            ),
        )
    )
    rf = result.scalar_one_or_none()
    if not rf:
        raise HTTPException(status_code=404, detail="Recurring format not found")

    # Update fields
    if data.name is not None:
        rf.name = data.name
    if data.description is not None:
        rf.description = data.description
    if data.frequency is not None:
        rf.frequency = data.frequency
    if data.preferred_day is not None:
        rf.preferred_day = data.preferred_day
    if data.preferred_time is not None:
        rf.preferred_time = data.preferred_time
    if data.tone is not None:
        rf.tone = data.tone
    if data.template_id is not None:
        rf.template_id = data.template_id
    if data.hashtags is not None:
        rf.hashtags = json.dumps(data.hashtags)
    if data.icon is not None:
        rf.icon = data.icon
    if data.category is not None:
        rf.category = data.category
    if data.is_active is not None:
        rf.is_active = data.is_active

    rf.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(rf)
    return recurring_format_to_dict(rf)


@router.delete("/{format_id}")
async def delete_recurring_format(
    format_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a recurring format. System defaults cannot be deleted (deactivate instead)."""
    result = await db.execute(
        select(RecurringFormat).where(
            RecurringFormat.id == format_id,
            or_(
                RecurringFormat.user_id == None,
                RecurringFormat.user_id == user_id,
            ),
        )
    )
    rf = result.scalar_one_or_none()
    if not rf:
        raise HTTPException(status_code=404, detail="Recurring format not found")

    if rf.is_default:
        raise HTTPException(
            status_code=400,
            detail="System-Standardformate koennen nicht geloescht werden. Deaktiviere sie stattdessen."
        )

    await db.delete(rf)
    await db.commit()
    return {"message": "Recurring format deleted", "id": format_id}
