"""Post routes."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.post import Post

router = APIRouter()


@router.get("")
async def list_posts(
    category: Optional[str] = None,
    platform: Optional[str] = None,
    status: Optional[str] = None,
    country: Optional[str] = None,
    search: Optional[str] = None,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List posts with optional filters."""
    query = select(Post).where(Post.user_id == user_id)

    if category:
        query = query.where(Post.category == category)
    if platform:
        query = query.where(Post.platform == platform)
    if status:
        query = query.where(Post.status == status)
    if country:
        query = query.where(Post.country == country)
    if search:
        query = query.where(Post.title.ilike(f"%{search}%"))

    query = query.order_by(Post.created_at.desc())
    result = await db.execute(query)
    posts = result.scalars().all()
    return posts


@router.get("/{post_id}")
async def get_post(
    post_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a single post by ID."""
    result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.post("", status_code=201)
async def create_post(
    post_data: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a new post."""
    post = Post(user_id=user_id, **post_data)
    db.add(post)
    await db.flush()
    await db.refresh(post)
    return post


@router.put("/{post_id}")
async def update_post(
    post_id: int,
    post_data: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing post."""
    result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    for key, value in post_data.items():
        if hasattr(post, key):
            setattr(post, key, value)

    await db.flush()
    await db.refresh(post)
    return post


@router.delete("/{post_id}")
async def delete_post(
    post_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a post."""
    result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    await db.delete(post)
    return {"message": "Post deleted"}


@router.post("/{post_id}/duplicate")
async def duplicate_post(
    post_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Duplicate an existing post."""
    result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user_id)
    )
    original = result.scalar_one_or_none()
    if not original:
        raise HTTPException(status_code=404, detail="Post not found")

    new_post = Post(
        user_id=user_id,
        template_id=original.template_id,
        category=original.category,
        country=original.country,
        platform=original.platform,
        status="draft",
        title=f"{original.title} (copy)" if original.title else "Copy",
        slide_data=original.slide_data,
        caption_instagram=original.caption_instagram,
        caption_tiktok=original.caption_tiktok,
        hashtags_instagram=original.hashtags_instagram,
        hashtags_tiktok=original.hashtags_tiktok,
        cta_text=original.cta_text,
        tone=original.tone,
    )
    db.add(new_post)
    await db.flush()
    await db.refresh(new_post)
    return new_post


@router.put("/{post_id}/status")
async def update_post_status(
    post_id: int,
    status_data: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update post status."""
    result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    post.status = status_data.get("status", post.status)
    await db.flush()
    await db.refresh(post)
    return post
