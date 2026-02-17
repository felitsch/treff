"""Audio Suggestions API routes.

Provides endpoints for browsing, filtering and managing trending audio
recommendations for Instagram Reels and TikTok videos.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.audio_suggestion import AudioSuggestion

logger = logging.getLogger(__name__)

router = APIRouter()


def _suggestion_to_dict(s: AudioSuggestion) -> dict:
    """Convert an AudioSuggestion model to API response dict."""
    suitable_for = []
    if s.suitable_for:
        try:
            suitable_for = json.loads(s.suitable_for) if isinstance(s.suitable_for, str) else s.suitable_for
        except (json.JSONDecodeError, TypeError):
            suitable_for = []

    return {
        "id": s.id,
        "title": s.title,
        "artist": s.artist,
        "platform": s.platform,
        "mood": s.mood,
        "tempo": s.tempo,
        "trending_score": s.trending_score,
        "url_hint": s.url_hint,
        "suitable_for": suitable_for,
        "description": s.description,
        "is_royalty_free": s.is_royalty_free,
        "is_default": s.is_default,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


@router.get("")
async def list_audio_suggestions(
    platform: Optional[str] = Query(None, description="Filter by platform: tiktok, instagram, both"),
    mood: Optional[str] = Query(None, description="Filter by mood: energetic, emotional, funny, chill, dramatic"),
    tempo: Optional[str] = Query(None, description="Filter by tempo: slow, medium, fast"),
    content_pillar: Optional[str] = Query(None, description="Filter by content pillar suitability"),
    is_royalty_free: Optional[bool] = Query(None, description="Filter by royalty-free status"),
    sort_by: str = Query("trending_score", description="Sort field: trending_score, title, created_at"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List audio suggestions with optional filters.

    Filter by platform (tiktok/instagram/both), mood, tempo, content_pillar.
    Results sorted by trending_score descending by default.
    """
    query = select(AudioSuggestion)

    # Apply filters
    if platform:
        # "both" matches everything; specific platform matches "both" + that platform
        if platform in ("tiktok", "instagram"):
            query = query.where(
                AudioSuggestion.platform.in_([platform, "both"])
            )
        else:
            query = query.where(AudioSuggestion.platform == platform)

    if mood:
        query = query.where(AudioSuggestion.mood == mood)

    if tempo:
        query = query.where(AudioSuggestion.tempo == tempo)

    if content_pillar:
        # Search within JSON array stored as text
        query = query.where(
            AudioSuggestion.suitable_for.contains(content_pillar)
        )

    if is_royalty_free is not None:
        query = query.where(AudioSuggestion.is_royalty_free == is_royalty_free)

    # Sorting
    if sort_by == "title":
        query = query.order_by(AudioSuggestion.title)
    elif sort_by == "created_at":
        query = query.order_by(desc(AudioSuggestion.created_at))
    else:
        query = query.order_by(desc(AudioSuggestion.trending_score))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    suggestions = result.scalars().all()

    return {
        "suggestions": [_suggestion_to_dict(s) for s in suggestions],
        "count": len(suggestions),
        "total": total,
    }


@router.get("/moods")
async def get_available_moods(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Return available mood categories with counts."""
    result = await db.execute(
        select(
            AudioSuggestion.mood,
            func.count(AudioSuggestion.id).label("count")
        ).group_by(AudioSuggestion.mood)
    )
    moods = [{"mood": row[0], "count": row[1]} for row in result.all()]
    return {"moods": moods}


@router.get("/platforms")
async def get_available_platforms(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Return available platforms with counts."""
    result = await db.execute(
        select(
            AudioSuggestion.platform,
            func.count(AudioSuggestion.id).label("count")
        ).group_by(AudioSuggestion.platform)
    )
    platforms = [{"platform": row[0], "count": row[1]} for row in result.all()]
    return {"platforms": platforms}


@router.get("/{suggestion_id}")
async def get_audio_suggestion(
    suggestion_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a single audio suggestion by ID."""
    result = await db.execute(
        select(AudioSuggestion).where(AudioSuggestion.id == suggestion_id)
    )
    suggestion = result.scalar_one_or_none()
    if not suggestion:
        raise HTTPException(status_code=404, detail="Audio suggestion not found")
    return _suggestion_to_dict(suggestion)


@router.post("")
async def create_audio_suggestion(
    request: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a new audio suggestion manually.

    Body:
    - title (str, required): Track/audio title
    - artist (str, optional): Artist name
    - platform (str): tiktok, instagram, or both (default: both)
    - mood (str): energetic, emotional, funny, chill, dramatic (default: energetic)
    - tempo (str): slow, medium, fast (default: medium)
    - trending_score (float): 1.0-10.0 (default: 5.0)
    - url_hint (str, optional): Link to the audio on the platform
    - suitable_for (list[str], optional): Content pillars this audio suits
    - description (str, optional): Description of the audio
    - is_royalty_free (bool, optional): Whether the audio is royalty-free
    """
    title = request.get("title", "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="title is required")

    # Validate mood
    valid_moods = ["energetic", "emotional", "funny", "chill", "dramatic"]
    mood = request.get("mood", "energetic")
    if mood not in valid_moods:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mood: {mood}. Must be one of {valid_moods}"
        )

    # Validate platform
    valid_platforms = ["tiktok", "instagram", "both"]
    platform = request.get("platform", "both")
    if platform not in valid_platforms:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid platform: {platform}. Must be one of {valid_platforms}"
        )

    # Validate tempo
    valid_tempos = ["slow", "medium", "fast"]
    tempo = request.get("tempo", "medium")
    if tempo not in valid_tempos:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tempo: {tempo}. Must be one of {valid_tempos}"
        )

    # Validate trending_score
    trending_score = float(request.get("trending_score", 5.0))
    trending_score = max(1.0, min(10.0, trending_score))

    # Process suitable_for
    suitable_for = request.get("suitable_for", [])
    if isinstance(suitable_for, list):
        suitable_for_json = json.dumps(suitable_for, ensure_ascii=False)
    else:
        suitable_for_json = json.dumps([], ensure_ascii=False)

    suggestion = AudioSuggestion(
        title=title,
        artist=request.get("artist"),
        platform=platform,
        mood=mood,
        tempo=tempo,
        trending_score=trending_score,
        url_hint=request.get("url_hint", ""),
        suitable_for=suitable_for_json,
        description=request.get("description", ""),
        is_royalty_free=request.get("is_royalty_free", False),
        is_default=False,
        user_id=user_id,
    )
    db.add(suggestion)
    await db.commit()
    await db.refresh(suggestion)

    logger.info(
        "Audio suggestion created: id=%d, title=%s, mood=%s",
        suggestion.id, title, mood
    )

    return _suggestion_to_dict(suggestion)


@router.delete("/{suggestion_id}")
async def delete_audio_suggestion(
    suggestion_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete an audio suggestion (only user-created ones)."""
    result = await db.execute(
        select(AudioSuggestion).where(AudioSuggestion.id == suggestion_id)
    )
    suggestion = result.scalar_one_or_none()
    if not suggestion:
        raise HTTPException(status_code=404, detail="Audio suggestion not found")

    # Only allow deleting user-created suggestions
    if suggestion.is_default and suggestion.user_id is None:
        raise HTTPException(
            status_code=403,
            detail="Cannot delete system default audio suggestions"
        )

    await db.delete(suggestion)
    await db.commit()

    return {"success": True, "deleted_id": suggestion_id}
