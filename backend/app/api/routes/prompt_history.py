"""Prompt History API routes — CRUD, favorites, filtering."""

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.prompt_history import PromptHistory

router = APIRouter()
logger = logging.getLogger(__name__)


# ─── Pydantic schemas ────────────────────────────────────────────

class PromptHistoryCreate(BaseModel):
    prompt_type: str = Field(..., description="Type: text, image, hashtags, optimization, video_script")
    prompt_text: str = Field(..., description="The prompt/input sent to the AI")
    options: Optional[str] = Field(None, description="JSON string of options/parameters")
    result_text: Optional[str] = Field(None, description="The AI result/output")
    tokens_used: Optional[int] = Field(None, description="Tokens consumed")
    estimated_cost: Optional[float] = Field(None, description="Cost in EUR cents")
    model: Optional[str] = Field(None, description="AI model used")


class PromptHistoryOut(BaseModel):
    id: int
    user_id: int
    prompt_type: str
    prompt_text: str
    options: Optional[str] = None
    result_text: Optional[str] = None
    tokens_used: Optional[int] = None
    estimated_cost: Optional[float] = None
    model: Optional[str] = None
    is_favorite: bool
    created_at: str

    class Config:
        from_attributes = True


class PromptHistoryListResponse(BaseModel):
    items: list[PromptHistoryOut]
    total: int
    page: int
    page_size: int
    total_pages: int


# ─── Helper: serialize a PromptHistory row ────────────────────────

def _serialize(row: PromptHistory) -> dict:
    return {
        "id": row.id,
        "user_id": row.user_id,
        "prompt_type": row.prompt_type,
        "prompt_text": row.prompt_text,
        "options": row.options,
        "result_text": row.result_text,
        "tokens_used": row.tokens_used,
        "estimated_cost": row.estimated_cost,
        "model": row.model,
        "is_favorite": row.is_favorite,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


# ─── GET /api/ai/history — List with pagination & filters ────────

@router.get("/history")
async def list_prompt_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    prompt_type: Optional[str] = Query(None, description="Filter by type: text, image, hashtags, optimization, video_script"),
    favorites_only: bool = Query(False, description="Show only favorites"),
    search: Optional[str] = Query(None, description="Search in prompt text"),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """List AI prompt history with pagination and filtering."""
    query = select(PromptHistory).where(PromptHistory.user_id == user_id)

    # Apply filters
    if prompt_type:
        query = query.where(PromptHistory.prompt_type == prompt_type)
    if favorites_only:
        query = query.where(PromptHistory.is_favorite == True)
    if search:
        query = query.where(PromptHistory.prompt_text.ilike(f"%{search}%"))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination and ordering (newest first)
    query = query.order_by(desc(PromptHistory.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    rows = result.scalars().all()

    total_pages = max(1, (total + page_size - 1) // page_size)

    return {
        "items": [_serialize(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


# ─── POST /api/ai/history — Create a new entry ───────────────────

@router.post("/history", status_code=201)
async def create_prompt_history(
    body: PromptHistoryCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Record an AI prompt call in the history."""
    entry = PromptHistory(
        user_id=user_id,
        prompt_type=body.prompt_type,
        prompt_text=body.prompt_text,
        options=body.options,
        result_text=body.result_text,
        tokens_used=body.tokens_used,
        estimated_cost=body.estimated_cost,
        model=body.model,
    )
    db.add(entry)
    await db.flush()
    await db.refresh(entry)
    return _serialize(entry)


# ─── GET /api/ai/history/stats — Summary stats ──────────────────
# NOTE: This must be defined BEFORE /history/{entry_id} to avoid path conflict.

@router.get("/history/stats")
async def get_prompt_history_stats(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Get summary statistics for the user's prompt history."""
    # Total count
    total_result = await db.execute(
        select(func.count()).where(PromptHistory.user_id == user_id)
    )
    total = total_result.scalar() or 0

    # Favorites count
    fav_result = await db.execute(
        select(func.count()).where(
            PromptHistory.user_id == user_id,
            PromptHistory.is_favorite == True,
        )
    )
    favorites = fav_result.scalar() or 0

    # Counts by type
    type_result = await db.execute(
        select(PromptHistory.prompt_type, func.count())
        .where(PromptHistory.user_id == user_id)
        .group_by(PromptHistory.prompt_type)
    )
    by_type = {row[0]: row[1] for row in type_result.all()}

    # Total tokens
    tokens_result = await db.execute(
        select(func.sum(PromptHistory.tokens_used)).where(PromptHistory.user_id == user_id)
    )
    total_tokens = tokens_result.scalar() or 0

    # Total estimated cost
    cost_result = await db.execute(
        select(func.sum(PromptHistory.estimated_cost)).where(PromptHistory.user_id == user_id)
    )
    total_cost = round(cost_result.scalar() or 0, 2)

    return {
        "total": total,
        "favorites": favorites,
        "by_type": by_type,
        "total_tokens": total_tokens,
        "total_estimated_cost": total_cost,
    }


# ─── GET /api/ai/history/{id} — Get single entry ─────────────────

@router.get("/history/{entry_id}")
async def get_prompt_history_entry(
    entry_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Get a single prompt history entry."""
    result = await db.execute(
        select(PromptHistory).where(
            PromptHistory.id == entry_id,
            PromptHistory.user_id == user_id,
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="History entry not found")
    return _serialize(entry)


# ─── PATCH /api/ai/history/{id}/favorite — Toggle favorite ───────

@router.patch("/history/{entry_id}/favorite")
async def toggle_favorite(
    entry_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Toggle favorite status of a prompt history entry."""
    result = await db.execute(
        select(PromptHistory).where(
            PromptHistory.id == entry_id,
            PromptHistory.user_id == user_id,
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="History entry not found")

    entry.is_favorite = not entry.is_favorite
    await db.flush()
    await db.refresh(entry)
    return _serialize(entry)


# ─── DELETE /api/ai/history/{id} — Delete single entry ───────────

@router.delete("/history/{entry_id}", status_code=204)
async def delete_prompt_history_entry(
    entry_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Delete a prompt history entry."""
    result = await db.execute(
        select(PromptHistory).where(
            PromptHistory.id == entry_id,
            PromptHistory.user_id == user_id,
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="History entry not found")

    await db.delete(entry)
    return None
