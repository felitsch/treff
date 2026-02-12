"""Post Slides routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.post import Post
from app.models.post_slide import PostSlide

router = APIRouter()


@router.get("/{post_id}/slides")
async def get_slides(
    post_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get all slides for a post."""
    result = await db.execute(
        select(PostSlide).where(PostSlide.post_id == post_id).order_by(PostSlide.slide_index)
    )
    return result.scalars().all()


@router.put("/{post_id}/slides")
async def update_slides(
    post_id: int,
    slides_data: list[dict],
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update all slides for a post (including reorder)."""
    # Delete existing slides
    result = await db.execute(select(PostSlide).where(PostSlide.post_id == post_id))
    existing = result.scalars().all()
    for slide in existing:
        await db.delete(slide)

    # Create new slides
    new_slides = []
    for i, slide_data in enumerate(slides_data):
        slide = PostSlide(post_id=post_id, slide_index=i, **slide_data)
        db.add(slide)
        new_slides.append(slide)

    await db.flush()
    return new_slides


@router.post("/{post_id}/slides", status_code=201)
async def add_slide(
    post_id: int,
    slide_data: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Add a slide to a post."""
    # Get max slide_index
    result = await db.execute(
        select(PostSlide).where(PostSlide.post_id == post_id).order_by(PostSlide.slide_index.desc())
    )
    last_slide = result.scalar_one_or_none()
    next_index = (last_slide.slide_index + 1) if last_slide else 0

    slide = PostSlide(post_id=post_id, slide_index=next_index, **slide_data)
    db.add(slide)
    await db.flush()
    await db.refresh(slide)
    return slide


@router.delete("/{post_id}/slides/{slide_id}")
async def delete_slide(
    post_id: int,
    slide_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a slide from a post."""
    result = await db.execute(
        select(PostSlide).where(PostSlide.id == slide_id, PostSlide.post_id == post_id)
    )
    slide = result.scalar_one_or_none()
    if not slide:
        raise HTTPException(status_code=404, detail="Slide not found")

    await db.delete(slide)
    return {"message": "Slide deleted"}
