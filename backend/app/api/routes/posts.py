"""Post routes."""

from typing import Optional
from datetime import datetime, date, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

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
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                Post.title.ilike(search_pattern),
                Post.slide_data.ilike(search_pattern),
                Post.caption_instagram.ilike(search_pattern),
                Post.caption_tiktok.ilike(search_pattern),
                Post.cta_text.ilike(search_pattern),
            )
        )

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
    # Parse scheduled_date string to datetime if provided
    if "scheduled_date" in post_data and post_data["scheduled_date"] and isinstance(post_data["scheduled_date"], str):
        try:
            post_data["scheduled_date"] = datetime.fromisoformat(post_data["scheduled_date"].replace("Z", "+00:00"))
        except (ValueError, TypeError):
            try:
                post_data["scheduled_date"] = datetime.strptime(post_data["scheduled_date"], "%Y-%m-%d")
            except (ValueError, TypeError):
                pass
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
            # Parse scheduled_date string to datetime if provided
            if key == "scheduled_date" and value and isinstance(value, str):
                try:
                    value = datetime.fromisoformat(value.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    try:
                        value = datetime.strptime(value, "%Y-%m-%d")
                    except (ValueError, TypeError):
                        pass
            setattr(post, key, value)

    # Auto-set status to "scheduled" when both scheduled_date and scheduled_time are provided
    if post.scheduled_date and post.scheduled_time and post.status == "draft":
        post.status = "scheduled"

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


@router.put("/{post_id}/schedule")
async def schedule_post(
    post_id: int,
    schedule_data: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Schedule a post by assigning a date and time. Auto-sets status to 'scheduled'."""
    result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    scheduled_date_str = schedule_data.get("scheduled_date")
    scheduled_time_str = schedule_data.get("scheduled_time")

    if not scheduled_date_str or not scheduled_time_str:
        raise HTTPException(
            status_code=400,
            detail="Both scheduled_date (YYYY-MM-DD) and scheduled_time (HH:MM) are required"
        )

    # Parse the date
    try:
        parsed_date = datetime.strptime(scheduled_date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    # Validate time format
    try:
        parts = scheduled_time_str.split(":")
        hour, minute = int(parts[0]), int(parts[1])
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
    except (ValueError, IndexError):
        raise HTTPException(status_code=400, detail="Invalid time format. Use HH:MM (24-hour)")

    post.scheduled_date = parsed_date
    post.scheduled_time = scheduled_time_str
    post.status = "scheduled"

    await db.flush()
    await db.refresh(post)
    response = post_to_dict(post)
    await db.commit()
    return response


@router.put("/{post_id}/status")
async def update_post_status(
    post_id: int,
    status_data: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update post status with proper timestamp tracking."""
    valid_statuses = {"draft", "scheduled", "reminded", "exported", "posted"}
    new_status = status_data.get("status")
    if not new_status or new_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(sorted(valid_statuses))}"
        )

    result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    post.status = new_status

    # Set posted_at timestamp when marking as posted
    if new_status == "posted" and not post.posted_at:
        post.posted_at = datetime.now(timezone.utc)

    # Set exported_at timestamp when marking as exported
    if new_status == "exported" and not post.exported_at:
        post.exported_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(post)
    response = post_to_dict(post)
    await db.commit()
    return response
