"""Content Suggestions routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.content_suggestion import ContentSuggestion

router = APIRouter()


def suggestion_to_dict(s: ContentSuggestion) -> dict:
    """Convert ContentSuggestion model to dict to avoid MissingGreenlet."""
    return {
        "id": s.id,
        "suggestion_type": s.suggestion_type,
        "title": s.title,
        "description": s.description,
        "suggested_category": s.suggested_category,
        "suggested_country": s.suggested_country,
        "suggested_date": s.suggested_date.isoformat() if s.suggested_date else None,
        "reason": s.reason,
        "status": s.status,
        "accepted_post_id": s.accepted_post_id,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


@router.get("")
async def list_suggestions(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List pending suggestions."""
    result = await db.execute(
        select(ContentSuggestion)
        .where(ContentSuggestion.status == "pending")
        .order_by(ContentSuggestion.created_at.desc())
    )
    suggestions = result.scalars().all()
    return [suggestion_to_dict(s) for s in suggestions]


@router.post("/generate")
async def generate_suggestions(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Trigger AI suggestion generation."""
    # TODO: Implement AI suggestion generation
    return {"message": "Suggestion generation triggered"}


@router.put("/{suggestion_id}/accept")
async def accept_suggestion(
    suggestion_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Accept and start post creation."""
    result = await db.execute(
        select(ContentSuggestion).where(ContentSuggestion.id == suggestion_id)
    )
    suggestion = result.scalar_one_or_none()
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    suggestion.status = "accepted"
    await db.commit()
    return suggestion_to_dict(suggestion)


@router.put("/{suggestion_id}/dismiss")
async def dismiss_suggestion(
    suggestion_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Dismiss a suggestion."""
    result = await db.execute(
        select(ContentSuggestion).where(ContentSuggestion.id == suggestion_id)
    )
    suggestion = result.scalar_one_or_none()
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    suggestion.status = "dismissed"
    await db.commit()
    return suggestion_to_dict(suggestion)
