"""Post Slides routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.post import Post
from app.models.post_slide import PostSlide

router = APIRouter()


def slide_to_dict(slide: PostSlide) -> dict:
    """Convert a PostSlide model to a plain dict to avoid lazy-loading issues."""
    return {
        "id": slide.id,
        "post_id": slide.post_id,
        "slide_index": slide.slide_index,
        "headline": slide.headline,
        "subheadline": slide.subheadline,
        "body_text": slide.body_text,
        "bullet_points": slide.bullet_points,
        "quote_text": slide.quote_text,
        "quote_author": slide.quote_author,
        "cta_text": slide.cta_text,
        "image_asset_id": slide.image_asset_id,
        "background_type": slide.background_type,
        "background_value": slide.background_value,
        "custom_css_overrides": slide.custom_css_overrides,
    }


@router.get("/{post_id}/slides")
async def get_slides(
    post_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get all slides for a post."""
    # Verify post belongs to user
    post_result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user_id)
    )
    if not post_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Post not found")

    result = await db.execute(
        select(PostSlide).where(PostSlide.post_id == post_id).order_by(PostSlide.slide_index)
    )
    slides = result.scalars().all()
    return [slide_to_dict(s) for s in slides]


@router.put("/{post_id}/slides")
async def update_slides(
    post_id: int,
    slides_data: list[dict],
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update all slides for a post (including reorder)."""
    # Verify post belongs to user
    post_result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user_id)
    )
    post = post_result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Delete existing slides
    result = await db.execute(select(PostSlide).where(PostSlide.post_id == post_id))
    existing = result.scalars().all()
    for slide in existing:
        await db.delete(slide)

    # Create new slides with correct slide_index
    new_slides = []
    allowed_fields = {
        "headline", "subheadline", "body_text", "bullet_points",
        "quote_text", "quote_author", "cta_text", "image_asset_id",
        "background_type", "background_value", "custom_css_overrides",
    }
    for i, slide_data in enumerate(slides_data):
        filtered = {k: v for k, v in slide_data.items() if k in allowed_fields}
        slide = PostSlide(post_id=post_id, slide_index=i, **filtered)
        db.add(slide)
        new_slides.append(slide)

    await db.flush()
    for slide in new_slides:
        await db.refresh(slide)
    response = [slide_to_dict(s) for s in new_slides]
    await db.commit()
    return response


@router.post("/{post_id}/slides", status_code=201)
async def add_slide(
    post_id: int,
    slide_data: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Add a slide to a post."""
    # Verify post belongs to user
    post_result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user_id)
    )
    if not post_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Post not found")

    # Get max slide_index
    result = await db.execute(
        select(PostSlide).where(PostSlide.post_id == post_id).order_by(PostSlide.slide_index.desc())
    )
    last_slide = result.scalar_one_or_none()
    next_index = (last_slide.slide_index + 1) if last_slide else 0

    allowed_fields = {
        "headline", "subheadline", "body_text", "bullet_points",
        "quote_text", "quote_author", "cta_text", "image_asset_id",
        "background_type", "background_value", "custom_css_overrides",
    }
    filtered = {k: v for k, v in slide_data.items() if k in allowed_fields}
    slide = PostSlide(post_id=post_id, slide_index=next_index, **filtered)
    db.add(slide)
    await db.flush()
    await db.refresh(slide)
    response = slide_to_dict(slide)
    await db.commit()
    return response


@router.delete("/{post_id}/slides/{slide_id}")
async def delete_slide(
    post_id: int,
    slide_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a slide from a post."""
    # Verify post belongs to user
    post_result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user_id)
    )
    if not post_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Post not found")

    result = await db.execute(
        select(PostSlide).where(PostSlide.id == slide_id, PostSlide.post_id == post_id)
    )
    slide = result.scalar_one_or_none()
    if not slide:
        raise HTTPException(status_code=404, detail="Slide not found")

    await db.delete(slide)
    await db.commit()
    return {"message": "Slide deleted"}
