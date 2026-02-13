"""Hashtag Set CRUD routes."""

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.hashtag_set import HashtagSet

router = APIRouter()
logger = logging.getLogger(__name__)


# ── Pydantic schemas ─────────────────────────────────

class HashtagSetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    hashtags: list[str] = Field(..., min_length=1)
    category: Optional[str] = None
    country: Optional[str] = None
    performance_score: float = Field(default=0.0, ge=0.0, le=10.0)


class HashtagSetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    hashtags: Optional[list[str]] = None
    category: Optional[str] = None
    country: Optional[str] = None
    performance_score: Optional[float] = Field(None, ge=0.0, le=10.0)


# ── Helper ────────────────────────────────────────────

def hashtag_set_to_dict(hs: HashtagSet) -> dict:
    """Convert HashtagSet model to dict."""
    try:
        hashtags = json.loads(hs.hashtags) if isinstance(hs.hashtags, str) else hs.hashtags
    except (json.JSONDecodeError, TypeError):
        hashtags = []

    return {
        "id": hs.id,
        "user_id": hs.user_id,
        "name": hs.name,
        "hashtags": hashtags,
        "category": hs.category,
        "country": hs.country,
        "performance_score": hs.performance_score,
        "is_default": bool(hs.is_default),
        "created_at": hs.created_at.isoformat() if hs.created_at else None,
        "updated_at": hs.updated_at.isoformat() if hs.updated_at else None,
    }


# ── Endpoints ─────────────────────────────────────────

@router.get("")
async def list_hashtag_sets(
    category: Optional[str] = None,
    country: Optional[str] = None,
    search: Optional[str] = None,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List all hashtag sets (user's own + system defaults).

    Supports optional filtering by category, country, and search term.
    """
    # Show both user's sets and system defaults (user_id IS NULL)
    query = select(HashtagSet).where(
        or_(
            HashtagSet.user_id == user_id,
            HashtagSet.user_id.is_(None),
        )
    )

    if category:
        query = query.where(HashtagSet.category == category)
    if country:
        query = query.where(HashtagSet.country == country)
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                HashtagSet.name.ilike(search_term),
                HashtagSet.hashtags.ilike(search_term),
            )
        )

    query = query.order_by(HashtagSet.performance_score.desc(), HashtagSet.name)

    result = await db.execute(query)
    sets = result.scalars().all()

    return {
        "hashtag_sets": [hashtag_set_to_dict(s) for s in sets],
        "total": len(sets),
    }


@router.get("/{set_id}")
async def get_hashtag_set(
    set_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a single hashtag set by ID."""
    result = await db.execute(
        select(HashtagSet).where(
            and_(
                HashtagSet.id == set_id,
                or_(
                    HashtagSet.user_id == user_id,
                    HashtagSet.user_id.is_(None),
                ),
            )
        )
    )
    hs = result.scalar_one_or_none()
    if not hs:
        raise HTTPException(status_code=404, detail="Hashtag-Set nicht gefunden")
    return hashtag_set_to_dict(hs)


@router.post("", status_code=201)
async def create_hashtag_set(
    data: HashtagSetCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a new custom hashtag set."""
    # Ensure all hashtags start with #
    cleaned_hashtags = []
    for tag in data.hashtags:
        tag = tag.strip()
        if tag and not tag.startswith("#"):
            tag = f"#{tag}"
        if tag:
            cleaned_hashtags.append(tag)

    if not cleaned_hashtags:
        raise HTTPException(status_code=400, detail="Mindestens ein Hashtag ist erforderlich")

    hs = HashtagSet(
        user_id=user_id,
        name=data.name,
        hashtags=json.dumps(cleaned_hashtags),
        category=data.category,
        country=data.country,
        performance_score=data.performance_score,
        is_default=0,
    )
    db.add(hs)
    await db.flush()
    await db.refresh(hs)
    return hashtag_set_to_dict(hs)


@router.put("/{set_id}")
async def update_hashtag_set(
    set_id: int,
    data: HashtagSetUpdate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing hashtag set (user-owned only, not system defaults)."""
    result = await db.execute(
        select(HashtagSet).where(
            and_(
                HashtagSet.id == set_id,
                HashtagSet.user_id == user_id,
            )
        )
    )
    hs = result.scalar_one_or_none()
    if not hs:
        raise HTTPException(
            status_code=404,
            detail="Hashtag-Set nicht gefunden oder du hast keine Berechtigung es zu bearbeiten"
        )

    update_data = data.model_dump(exclude_unset=True)

    # Clean hashtags if provided
    if "hashtags" in update_data and update_data["hashtags"] is not None:
        cleaned = []
        for tag in update_data["hashtags"]:
            tag = tag.strip()
            if tag and not tag.startswith("#"):
                tag = f"#{tag}"
            if tag:
                cleaned.append(tag)
        update_data["hashtags"] = json.dumps(cleaned)

    for field, value in update_data.items():
        setattr(hs, field, value)

    await db.flush()
    await db.refresh(hs)
    return hashtag_set_to_dict(hs)


@router.delete("/{set_id}")
async def delete_hashtag_set(
    set_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a custom hashtag set (user-owned only, not system defaults)."""
    result = await db.execute(
        select(HashtagSet).where(
            and_(
                HashtagSet.id == set_id,
                HashtagSet.user_id == user_id,
            )
        )
    )
    hs = result.scalar_one_or_none()
    if not hs:
        raise HTTPException(
            status_code=404,
            detail="Hashtag-Set nicht gefunden oder du hast keine Berechtigung es zu loeschen"
        )

    await db.delete(hs)
    return {"detail": "Hashtag-Set geloescht"}
