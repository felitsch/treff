"""Content Suggestions routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.content_suggestion import ContentSuggestion

router = APIRouter()


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
    return result.scalars().all()


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
    await db.flush()
    return suggestion


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
    await db.flush()
    return suggestion
