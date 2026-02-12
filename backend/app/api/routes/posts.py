"""Post routes."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.post import Post

router = APIRouter()


def post_to_dict(post: Post) -> dict:
    """Convert a Post model to a plain dict to avoid lazy-loading issues."""
    return {
        "id": post.id,
        "user_id": post.user_id,
        "template_id": post.template_id,
        "category": post.category,
        "country": post.country,
        "platform": post.platform,
        "status": post.status,
        "title": post.title,
        "slide_data": post.slide_data,
        "caption_instagram": post.caption_instagram,
        "caption_tiktok": post.caption_tiktok,
        "hashtags_instagram": post.hashtags_instagram,
        "hashtags_tiktok": post.hashtags_tiktok,
        "cta_text": post.cta_text,
        "custom_colors": post.custom_colors,
        "custom_fonts": post.custom_fonts,
        "tone": post.tone,
        "scheduled_date": post.scheduled_date.isoformat() if post.scheduled_date else None,
        "scheduled_time": post.scheduled_time,
        "exported_at": post.exported_at.isoformat() if post.exported_at else None,
        "posted_at": post.posted_at.isoformat() if post.posted_at else None,
        "created_at": post.created_at.isoformat() if post.created_at else None,
        "updated_at": post.updated_at.isoformat() if post.updated_at else None,
    }


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
    return [post_to_dict(p) for p in posts]


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
    return post_to_dict(post)


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
    result = post_to_dict(post)
    await db.commit()
    return result


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
        if hasattr(post, key) and key not in ("id", "user_id", "created_at"):
            setattr(post, key, value)

    await db.flush()
    await db.refresh(post)
    response = post_to_dict(post)
    await db.commit()
    return response


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
    await db.commit()
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
    response = post_to_dict(new_post)
    await db.commit()
    return response


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
    response = post_to_dict(post)
    await db.commit()
    return response
