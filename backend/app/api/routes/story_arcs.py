"""Story Arc routes - CRUD for multi-part story series."""

import logging
from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.story_arc import StoryArc
from app.models.content_suggestion import ContentSuggestion
from app.models.student import Student

router = APIRouter()
logger = logging.getLogger(__name__)


def story_arc_to_dict(arc: StoryArc) -> dict:
    """Convert a StoryArc model to a plain dict to avoid lazy-loading issues."""
    return {
        "id": arc.id,
        "user_id": arc.user_id,
        "title": arc.title,
        "subtitle": arc.subtitle,
        "description": arc.description,
        "student_id": arc.student_id,
        "country": arc.country,
        "status": arc.status,
        "planned_episodes": arc.planned_episodes,
        "current_episode": arc.current_episode,
        "cover_image_id": arc.cover_image_id,
        "tone": arc.tone,
        "created_at": arc.created_at.isoformat() if arc.created_at else None,
        "updated_at": arc.updated_at.isoformat() if arc.updated_at else None,
    }


async def _auto_suggest_story_teaser(arc: StoryArc, db: AsyncSession) -> Optional[dict]:
    """Auto-generate a content suggestion for a feed teaser when a story arc becomes active.

    Creates a 'story_teaser' type suggestion pointing users to create a feed post
    that promotes the new story series in their Instagram Stories.
    """
    # Look up student name if linked
    student_name = None
    if arc.student_id:
        result = await db.execute(
            select(Student).where(Student.id == arc.student_id)
        )
        student = result.scalar_one_or_none()
        if student:
            student_name = student.name

    # Build suggestion title and description
    title_parts = [f"Story-Teaser: {arc.title}"]
    if student_name:
        title_parts.append(f"mit {student_name}")
    suggestion_title = " ".join(title_parts)

    desc_parts = [
        f"Neue Story-Serie '{arc.title}' startet!",
    ]
    if student_name:
        desc_parts.append(f"Erstelle einen Feed-Teaser-Post fuer {student_name}s Abenteuer.")
    else:
        desc_parts.append("Erstelle einen Feed-Teaser-Post, der auf die Story-Serie hinweist.")
    desc_parts.append("Schau in unsere Stories! Verwende das Story-Teaser Template.")

    suggestion = ContentSuggestion(
        suggestion_type="story_teaser",
        title=suggestion_title,
        description=" ".join(desc_parts),
        suggested_category="story_teaser",
        suggested_country=arc.country,
        suggested_date=date.today(),
        reason=f"Story-Arc '{arc.title}' wurde aktiviert - Feed-Teaser empfohlen",
        status="pending",
    )
    db.add(suggestion)
    logger.info(f"Auto-suggested story teaser for arc '{arc.title}' (id={arc.id})")
    return {
        "suggestion_created": True,
        "suggestion_title": suggestion_title,
    }


@router.get("")
async def list_story_arcs(
    student_id: Optional[int] = None,
    country: Optional[str] = None,
    status: Optional[str] = None,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List story arcs with optional filters: student_id, country, status."""
    where_clauses = [StoryArc.user_id == user_id]

    if student_id is not None:
        where_clauses.append(StoryArc.student_id == student_id)
    if country:
        where_clauses.append(StoryArc.country == country)
    if status:
        valid_statuses = {"draft", "active", "paused", "completed"}
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(sorted(valid_statuses))}"
            )
        where_clauses.append(StoryArc.status == status)

    query = select(StoryArc).where(*where_clauses).order_by(StoryArc.created_at.desc())
    result = await db.execute(query)
    arcs = result.scalars().all()
    return [story_arc_to_dict(a) for a in arcs]


@router.get("/{arc_id}")
async def get_story_arc(
    arc_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a single story arc by ID."""
    result = await db.execute(
        select(StoryArc).where(StoryArc.id == arc_id, StoryArc.user_id == user_id)
    )
    arc = result.scalar_one_or_none()
    if not arc:
        raise HTTPException(status_code=404, detail="Story arc not found")
    return story_arc_to_dict(arc)


@router.post("", status_code=201)
async def create_story_arc(
    arc_data: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a new story arc."""
    # Validate required field
    if not arc_data.get("title"):
        raise HTTPException(status_code=400, detail="Title is required")

    # Validate status if provided
    if "status" in arc_data:
        valid_statuses = {"draft", "active", "paused", "completed"}
        if arc_data["status"] not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(sorted(valid_statuses))}"
            )

    # Validate tone if provided
    if "tone" in arc_data:
        valid_tones = {"jugendlich", "serioess"}
        if arc_data["tone"] not in valid_tones:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid tone. Must be one of: {', '.join(sorted(valid_tones))}"
            )

    # Filter to only allowed fields
    allowed_fields = {
        "title", "subtitle", "description", "student_id", "country",
        "status", "planned_episodes", "current_episode", "cover_image_id", "tone",
    }
    filtered_data = {k: v for k, v in arc_data.items() if k in allowed_fields}

    arc = StoryArc(user_id=user_id, **filtered_data)
    db.add(arc)
    await db.flush()
    await db.refresh(arc)
    response = story_arc_to_dict(arc)

    # Auto-suggest feed teaser when arc is created with status "active"
    suggestion_info = None
    if arc.status == "active":
        suggestion_info = await _auto_suggest_story_teaser(arc, db)

    await db.commit()

    if suggestion_info:
        response["teaser_suggestion"] = suggestion_info

    return response


@router.put("/{arc_id}")
async def update_story_arc(
    arc_id: int,
    arc_data: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing story arc."""
    result = await db.execute(
        select(StoryArc).where(StoryArc.id == arc_id, StoryArc.user_id == user_id)
    )
    arc = result.scalar_one_or_none()
    if not arc:
        raise HTTPException(status_code=404, detail="Story arc not found")

    # Validate status if provided
    if "status" in arc_data:
        valid_statuses = {"draft", "active", "paused", "completed"}
        if arc_data["status"] not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(sorted(valid_statuses))}"
            )

    # Validate tone if provided
    if "tone" in arc_data:
        valid_tones = {"jugendlich", "serioess"}
        if arc_data["tone"] not in valid_tones:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid tone. Must be one of: {', '.join(sorted(valid_tones))}"
            )

    # Track previous status for auto-suggestion
    previous_status = arc.status

    # Update allowed fields
    allowed_fields = {
        "title", "subtitle", "description", "student_id", "country",
        "status", "planned_episodes", "current_episode", "cover_image_id", "tone",
    }
    for key, value in arc_data.items():
        if key in allowed_fields and hasattr(arc, key):
            setattr(arc, key, value)

    await db.flush()
    await db.refresh(arc)
    response = story_arc_to_dict(arc)

    # Auto-suggest feed teaser when arc transitions to "active"
    suggestion_info = None
    if arc.status == "active" and previous_status != "active":
        suggestion_info = await _auto_suggest_story_teaser(arc, db)

    await db.commit()

    if suggestion_info:
        response["teaser_suggestion"] = suggestion_info

    return response


@router.delete("/{arc_id}")
async def delete_story_arc(
    arc_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a story arc."""
    result = await db.execute(
        select(StoryArc).where(StoryArc.id == arc_id, StoryArc.user_id == user_id)
    )
    arc = result.scalar_one_or_none()
    if not arc:
        raise HTTPException(status_code=404, detail="Story arc not found")

    await db.delete(arc)
    await db.commit()
    return {"message": "Story arc deleted"}
