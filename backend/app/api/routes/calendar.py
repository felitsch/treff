"""Calendar routes."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.calendar_entry import CalendarEntry

router = APIRouter()


@router.get("")
async def get_calendar(
    month: Optional[int] = None,
    year: Optional[int] = None,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get calendar entries for a month."""
    query = select(CalendarEntry)
    # TODO: Filter by month/year
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/week")
async def get_calendar_week(
    date: Optional[str] = None,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get calendar entries for a week."""
    # TODO: Implement week filtering
    result = await db.execute(select(CalendarEntry))
    return result.scalars().all()


@router.post("/entries", status_code=201)
async def create_calendar_entry(
    entry_data: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create/assign post to date."""
    entry = CalendarEntry(**entry_data)
    db.add(entry)
    await db.flush()
    await db.refresh(entry)
    return entry


@router.put("/entries/{entry_id}")
async def update_calendar_entry(
    entry_id: int,
    entry_data: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Move post to different date."""
    result = await db.execute(select(CalendarEntry).where(CalendarEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Calendar entry not found")

    for key, value in entry_data.items():
        if hasattr(entry, key):
            setattr(entry, key, value)

    await db.flush()
    await db.refresh(entry)
    return entry


@router.delete("/entries/{entry_id}")
async def delete_calendar_entry(
    entry_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete calendar entry."""
    result = await db.execute(select(CalendarEntry).where(CalendarEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Calendar entry not found")

    await db.delete(entry)
    return {"message": "Calendar entry deleted"}


@router.get("/gaps")
async def get_calendar_gaps(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get days without scheduled content."""
    # TODO: Implement gap detection
    return {"gaps": []}


@router.get("/stats")
async def get_calendar_stats(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get posting frequency and goal progress."""
    # TODO: Implement stats
    return {"posts_this_week": 0, "weekly_goal": 4, "posts_this_month": 0, "monthly_goal": 16}
