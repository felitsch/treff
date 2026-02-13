"""Story Arc routes - CRUD for multi-part story series."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.story_arc import StoryArc

router = APIRouter()


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
    await db.commit()
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
    await db.commit()
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
