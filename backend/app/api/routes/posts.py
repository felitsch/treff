"""Post routes.

CRUD operations for social media posts. Supports filtering, sorting, pagination,
multi-platform creation, batch status updates, draft management, and scheduling.
"""

import json
import uuid
from typing import Optional
from datetime import datetime, date, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func, and_

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.core.cache import invalidate_cache
from app.models.post import Post

router = APIRouter()


def post_to_dict(post: Post) -> dict:
    """Convert a Post model to a plain dict to avoid lazy-loading issues."""
    # Calculate engagement rate: (likes + comments + shares) / reach
    perf_likes = getattr(post, "perf_likes", None) or 0
    perf_comments = getattr(post, "perf_comments", None) or 0
    perf_shares = getattr(post, "perf_shares", None) or 0
    perf_saves = getattr(post, "perf_saves", None) or 0
    perf_reach = getattr(post, "perf_reach", None) or 0
    engagement_rate = None
    if perf_reach > 0:
        engagement_rate = round(((perf_likes + perf_comments + perf_shares) / perf_reach) * 100, 2)

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
        "student_id": post.student_id,
        "story_arc_id": post.story_arc_id,
        "episode_number": post.episode_number,
        "linked_post_group_id": post.linked_post_group_id,
        "recurring_rule_id": post.recurring_rule_id,
        "is_recurring_instance": bool(post.is_recurring_instance) if post.is_recurring_instance is not None else None,
        "pillar_id": getattr(post, "pillar_id", None),
        "hook_formula": getattr(post, "hook_formula", None),
        "scheduled_date": post.scheduled_date.isoformat() if post.scheduled_date else None,
        "scheduled_time": post.scheduled_time,
        "exported_at": post.exported_at.isoformat() if post.exported_at else None,
        "posted_at": post.posted_at.isoformat() if post.posted_at else None,
        "created_at": post.created_at.isoformat() if post.created_at else None,
        "updated_at": post.updated_at.isoformat() if post.updated_at else None,
        # Performance metrics
        "perf_likes": getattr(post, "perf_likes", None),
        "perf_comments": getattr(post, "perf_comments", None),
        "perf_shares": getattr(post, "perf_shares", None),
        "perf_saves": getattr(post, "perf_saves", None),
        "perf_reach": getattr(post, "perf_reach", None),
        "perf_updated_at": getattr(post, "perf_updated_at", None).isoformat() if getattr(post, "perf_updated_at", None) else None,
        "engagement_rate": engagement_rate,
    }


@router.get(
    "",
    summary="List Posts",
    description="List all posts with optional filters (category, platform, status, country, date range, student), sorting, and pagination. When `page` and `limit` are provided, returns paginated results with metadata. Otherwise returns a flat array.",
    responses={
        200: {"description": "List of posts (paginated or flat array)"},
        401: {"description": "Not authenticated"},
    },
)
async def list_posts(
    category: Optional[str] = Query(default=None, description="Filter by content category (e.g., 'Laender-Spotlight')"),
    platform: Optional[str] = Query(default=None, description="Filter by platform ('instagram', 'tiktok')"),
    status: Optional[str] = Query(default=None, description="Filter by post status ('draft', 'scheduled', 'published', 'archived')"),
    country: Optional[str] = Query(default=None, description="Filter by country ('USA', 'Kanada', 'Australien', etc.)"),
    search: Optional[str] = Query(default=None, description="Full-text search across title, slides, and captions"),
    date_from: Optional[str] = Query(default=None, description="Filter posts created on or after this date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(default=None, description="Filter posts created on or before this date (YYYY-MM-DD)"),
    sort_by: Optional[str] = Query(default="created_at", pattern="^(created_at|updated_at|title|scheduled_date)$", description="Sort field"),
    student_id: Optional[int] = Query(default=None, description="Filter by associated student ID"),
    sort_direction: Optional[str] = Query(default="desc", pattern="^(asc|desc)$", description="Sort direction"),
    page: Optional[int] = Query(default=None, ge=1, description="Page number (1-based) for pagination"),
    limit: Optional[int] = Query(default=None, ge=1, le=100, description="Items per page (max 100)"),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List posts with optional filters, sorting, and pagination.

    When page and limit are provided, returns paginated results with metadata.
    When not provided, returns all results as a flat array (backward compatible).
    """
    base_where = [Post.user_id == user_id]

    if category:
        base_where.append(Post.category == category)
    if platform:
        base_where.append(Post.platform == platform)
    if status:
        base_where.append(Post.status == status)
    if country:
        base_where.append(Post.country == country)
    if student_id:
        base_where.append(Post.student_id == student_id)
    if search and search.strip():
        search_pattern = f"%{search.strip()}%"
        base_where.append(
            or_(
                Post.title.ilike(search_pattern),
                Post.slide_data.ilike(search_pattern),
                Post.caption_instagram.ilike(search_pattern),
                Post.caption_tiktok.ilike(search_pattern),
                Post.cta_text.ilike(search_pattern),
            )
        )
    if date_from:
        try:
            from_date = datetime.strptime(date_from, "%Y-%m-%d")
            base_where.append(Post.created_at >= from_date)
        except (ValueError, TypeError):
            pass
    if date_to:
        try:
            # Set to end of day (23:59:59) to include the entire day
            to_date = datetime.strptime(date_to, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            base_where.append(Post.created_at <= to_date)
        except (ValueError, TypeError):
            pass

    # Build the query with filters
    query = select(Post).where(*base_where)

    # Dynamic sorting
    sort_field_map = {
        "created_at": Post.created_at,
        "updated_at": Post.updated_at,
        "title": Post.title,
        "scheduled_date": Post.scheduled_date,
    }
    sort_column = sort_field_map.get(sort_by, Post.created_at)
    if sort_direction == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # If pagination params provided, return paginated response
    if page is not None and limit is not None:
        # Get total count
        count_query = select(func.count()).select_from(Post).where(*base_where)
        count_result = await db.execute(count_query)
        total = count_result.scalar()

        # Calculate total pages
        total_pages = max(1, (total + limit - 1) // limit)

        # Clamp page to valid range
        effective_page = min(page, total_pages)

        # Apply pagination
        offset = (effective_page - 1) * limit
        query = query.offset(offset).limit(limit)

        result = await db.execute(query)
        posts = result.scalars().all()

        return {
            "items": [post_to_dict(p) for p in posts],
            "total": total,
            "page": effective_page,
            "limit": limit,
            "total_pages": total_pages,
        }

    # No pagination - return flat array (backward compatible)
    result = await db.execute(query)
    posts = result.scalars().all()
    return [post_to_dict(p) for p in posts]


@router.put("/sync-siblings")
async def sync_sibling_posts(
    data: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Apply field changes from a source post to its sibling posts.

    Must be declared before /{post_id} routes so FastAPI doesn't match
    'sync-siblings' as a post_id path parameter.
    """
    source_post_id = data.get("source_post_id")
    fields = data.get("fields", {})
    sibling_ids = data.get("sibling_ids")

    if not source_post_id or not fields:
        raise HTTPException(status_code=400, detail="source_post_id and fields are required")

    result = await db.execute(
        select(Post).where(Post.id == source_post_id, Post.user_id == user_id)
    )
    source = result.scalar_one_or_none()
    if not source or not source.linked_post_group_id:
        raise HTTPException(status_code=404, detail="Source post not found or not part of a group")

    conditions = [
        Post.user_id == user_id,
        Post.linked_post_group_id == source.linked_post_group_id,
        Post.id != source_post_id,
    ]
    if sibling_ids:
        conditions.append(Post.id.in_(sibling_ids))

    result = await db.execute(select(Post).where(and_(*conditions)))
    siblings = result.scalars().all()

    protected_fields = {"id", "user_id", "created_at", "platform", "linked_post_group_id"}
    updated = []
    for sibling in siblings:
        for field, value in fields.items():
            if field in protected_fields:
                continue
            if hasattr(sibling, field):
                if field == "scheduled_date" and value and isinstance(value, str):
                    try:
                        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
                    except (ValueError, TypeError):
                        try:
                            value = datetime.strptime(value, "%Y-%m-%d")
                        except (ValueError, TypeError):
                            pass
                setattr(sibling, field, value)
        updated.append(post_to_dict(sibling))

    await db.commit()
    return {"updated": updated, "count": len(updated)}


# ═══════════════════════════════════════════════════════════════════════
# Draft Auto-Save Endpoints (must be before /{post_id} to avoid route conflict)
# ═══════════════════════════════════════════════════════════════════════

@router.get("/drafts/list")
async def list_drafts(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List all draft posts for the current user, ordered by most recently updated."""
    result = await db.execute(
        select(Post)
        .where(Post.user_id == user_id, Post.status == "draft")
        .order_by(Post.updated_at.desc())
    )
    drafts = result.scalars().all()
    return {
        "drafts": [post_to_dict(d) for d in drafts],
        "count": len(drafts),
    }


@router.get("/drafts/latest")
async def get_latest_draft(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get the most recently updated draft for auto-restoration."""
    result = await db.execute(
        select(Post)
        .where(Post.user_id == user_id, Post.status == "draft")
        .order_by(Post.updated_at.desc())
        .limit(1)
    )
    draft = result.scalar_one_or_none()
    if not draft:
        return {"draft": None, "message": "Kein Entwurf vorhanden"}
    return {
        "draft": post_to_dict(draft),
        "message": "Letzter Entwurf geladen",
    }


@router.post("/drafts/save")
async def save_draft(
    draft_data: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Save or update a draft post.

    If draft_id is provided, updates the existing draft.
    If not, creates a new draft post with status='draft'.
    """
    draft_id = draft_data.pop("draft_id", None)
    wizard_state = draft_data.pop("wizard_state", None)
    draft_data["status"] = "draft"

    # Parse scheduled_date if present
    if "scheduled_date" in draft_data and draft_data["scheduled_date"] and isinstance(draft_data["scheduled_date"], str):
        try:
            draft_data["scheduled_date"] = datetime.fromisoformat(draft_data["scheduled_date"].replace("Z", "+00:00"))
        except (ValueError, TypeError):
            try:
                draft_data["scheduled_date"] = datetime.strptime(draft_data["scheduled_date"], "%Y-%m-%d")
            except (ValueError, TypeError):
                draft_data.pop("scheduled_date", None)

    # Store wizard state in custom_fonts JSON field for restoration
    if wizard_state:
        draft_data["custom_fonts"] = json.dumps({"_wizard_state": wizard_state}) if isinstance(wizard_state, dict) else wizard_state

    if draft_id:
        result = await db.execute(
            select(Post).where(Post.id == draft_id, Post.user_id == user_id, Post.status == "draft")
        )
        draft = result.scalar_one_or_none()
        if not draft:
            raise HTTPException(status_code=404, detail="Entwurf nicht gefunden")

        for key, value in draft_data.items():
            if hasattr(draft, key) and key not in ("id", "user_id", "created_at"):
                setattr(draft, key, value)

        draft.updated_at = datetime.now(timezone.utc)
        await db.flush()
        await db.refresh(draft)
        return {"status": "updated", "draft": post_to_dict(draft), "message": "Entwurf aktualisiert"}
    else:
        draft_data.setdefault("category", "allgemein")
        draft_data.setdefault("platform", "instagram_feed")
        draft_data.setdefault("slide_data", "[]")
        draft_data.pop("id", None)
        draft_data.pop("created_at", None)
        draft_data.pop("updated_at", None)

        draft = Post(user_id=user_id, **draft_data)
        db.add(draft)
        await db.flush()
        await db.refresh(draft)
        return {"status": "created", "draft": post_to_dict(draft), "message": "Entwurf gespeichert"}


@router.delete("/drafts/{draft_id}")
async def delete_draft(
    draft_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a draft post."""
    result = await db.execute(
        select(Post).where(Post.id == draft_id, Post.user_id == user_id, Post.status == "draft")
    )
    draft = result.scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=404, detail="Entwurf nicht gefunden")
    await db.delete(draft)
    return {"detail": "Entwurf geloescht", "draft_id": draft_id}


# ═══════════════════════════════════════════════════════════════════════


@router.put("/batch-status")
async def batch_update_status(
    data: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update status for multiple posts at once.

    Expects:
    - post_ids: list of post IDs
    - status: target status string
    """
    valid_statuses = {"draft", "scheduled", "reminded", "in_review", "exported", "posted", "archived"}
    post_ids = data.get("post_ids", [])
    new_status = data.get("status")

    if not post_ids or not isinstance(post_ids, list):
        raise HTTPException(status_code=400, detail="post_ids must be a non-empty list")
    if not new_status or new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(sorted(valid_statuses))}")

    allowed_transitions = {
        "draft": {"scheduled", "in_review", "archived"},
        "scheduled": {"draft", "in_review", "exported", "reminded", "archived"},
        "in_review": {"draft", "scheduled", "exported", "archived"},
        "reminded": {"scheduled", "in_review", "exported", "posted", "archived"},
        "exported": {"scheduled", "in_review", "posted", "archived"},
        "posted": {"archived"},
        "archived": {"draft"},
    }

    result = await db.execute(
        select(Post).where(Post.id.in_(post_ids), Post.user_id == user_id)
    )
    posts = result.scalars().all()

    updated = []
    skipped = []
    for post in posts:
        current = post.status or "draft"
        if current in allowed_transitions and new_status not in allowed_transitions.get(current, set()):
            skipped.append({"id": post.id, "title": post.title, "reason": f"Wechsel von '{current}' nicht erlaubt"})
            continue
        post.status = new_status
        if new_status == "posted" and not post.posted_at:
            post.posted_at = datetime.now(timezone.utc)
        if new_status == "exported" and not post.exported_at:
            post.exported_at = datetime.now(timezone.utc)
        updated.append(post.id)

    await db.commit()
    return {
        "updated": updated,
        "updated_count": len(updated),
        "skipped": skipped,
        "skipped_count": len(skipped),
        "target_status": new_status,
    }


@router.get(
    "/{post_id}",
    summary="Get Post by ID",
    description="Retrieve a single post by its ID. Returns all post fields including captions, hashtags, scheduling info, and performance metrics.",
)
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


@router.post(
    "",
    status_code=201,
    summary="Create Post",
    description="Create a new social media post. Supports all fields including category, platform, template, captions, hashtags, CTA, scheduling, and student/story-arc association.",
)
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
    invalidate_cache("dashboard", "analytics", "overview", "categories", "platforms", "countries", "frequency", "goals", "content_mix")
    return result


@router.put(
    "/{post_id}",
    summary="Update Post",
    description="Update an existing post. Only the provided fields are modified; omitted fields remain unchanged.",
)
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
    invalidate_cache("dashboard", "analytics", "overview", "categories", "platforms", "countries", "frequency", "goals", "content_mix")
    return response


@router.delete(
    "/{post_id}",
    summary="Delete Post",
    description="Permanently delete a post and all associated data (slides, interactive elements, relations).",
)
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
    invalidate_cache("dashboard", "analytics", "overview", "categories", "platforms", "countries", "frequency", "goals", "content_mix")
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
        student_id=original.student_id,
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

    # Reject past dates - scheduling must be today or in the future
    today = date.today()
    if parsed_date.date() < today:
        raise HTTPException(
            status_code=400,
            detail="Vergangene Daten koennen nicht ausgewaehlt werden. Bitte waehlen Sie ein Datum ab heute."
        )

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
    valid_statuses = {"draft", "scheduled", "reminded", "in_review", "exported", "posted", "archived"}
    new_status = status_data.get("status")
    if not new_status or new_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(sorted(valid_statuses))}"
        )

    # Status transition rules: define allowed transitions
    allowed_transitions = {
        "draft": {"scheduled", "in_review", "archived"},
        "scheduled": {"draft", "in_review", "exported", "reminded", "archived"},
        "in_review": {"draft", "scheduled", "exported", "archived"},
        "reminded": {"scheduled", "in_review", "exported", "posted", "archived"},
        "exported": {"scheduled", "in_review", "posted", "archived"},
        "posted": {"archived"},
        "archived": {"draft"},  # Can only unarchive back to draft
    }

    result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    current_status = post.status or "draft"
    if current_status in allowed_transitions and new_status not in allowed_transitions.get(current_status, set()):
        raise HTTPException(
            status_code=400,
            detail=f"Statuswechsel von '{current_status}' nach '{new_status}' nicht erlaubt. Erlaubt: {', '.join(sorted(allowed_transitions.get(current_status, set())))}"
        )

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


@router.post("/multi-platform", status_code=201)
async def create_multi_platform_posts(
    data: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create linked posts for multiple platforms at once.

    Body:
    - post_data: dict - Base post fields (category, country, title, slide_data, tone, etc.)
    - platforms: list[str] - List of platforms: instagram_feed, instagram_story, tiktok
    - adapt_content: bool (optional) - Whether to flag for AI adaptation per platform

    Returns: List of created posts with shared linked_post_group_id.
    """
    post_data = data.get("post_data", {})
    platforms = data.get("platforms", [])

    if not platforms or len(platforms) < 1:
        raise HTTPException(status_code=400, detail="At least one platform is required")

    valid_platforms = {"instagram_feed", "instagram_story", "tiktok"}
    for p in platforms:
        if p not in valid_platforms:
            raise HTTPException(status_code=400, detail=f"Invalid platform: {p}. Must be one of: {', '.join(sorted(valid_platforms))}")

    adapt_content = data.get("adapt_content", False)
    source_platform = data.get("source_platform", platforms[0] if platforms else "instagram_feed")

    # Generate a shared group ID to link all sibling posts
    group_id = str(uuid.uuid4())

    # Platform-specific text adaptation guidelines
    platform_guidelines = {
        "instagram_feed": {
            "caption_style": "Laengere Captions (bis 2200 Zeichen), Storytelling, Hashtags am Ende, ausfuehrlicher CTA",
            "max_caption_length": 2200,
            "format_note": "Quadratisch (1:1) oder Hochformat (4:5)",
        },
        "instagram_story": {
            "caption_style": "Kurz und knackig (max 100 Zeichen), CTA mit Swipe-Up/Link, 1-2 Emojis, Frage oder Poll",
            "max_caption_length": 100,
            "format_note": "Vollformat (9:16)",
        },
        "tiktok": {
            "caption_style": "Hook-fokussiert (erste 3 Sekunden), kurz (max 150 Zeichen), trendige Sprache, Hashtags inline",
            "max_caption_length": 150,
            "format_note": "Hochformat (9:16), Video-orientiert",
        },
    }

    created_posts = []
    for platform in platforms:
        # Parse scheduled_date string to datetime if provided
        pd = dict(post_data)
        if "scheduled_date" in pd and pd["scheduled_date"] and isinstance(pd["scheduled_date"], str):
            try:
                pd["scheduled_date"] = datetime.fromisoformat(pd["scheduled_date"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                try:
                    pd["scheduled_date"] = datetime.strptime(pd["scheduled_date"], "%Y-%m-%d")
                except (ValueError, TypeError):
                    pass

        # Remove platform from post_data if present (we set it explicitly)
        pd.pop("platform", None)
        pd.pop("linked_post_group_id", None)

        # Auto-adapt captions for non-source platforms if adapt_content is True
        if adapt_content and platform != source_platform:
            guidelines = platform_guidelines.get(platform, {})
            caption_style = guidelines.get("caption_style", "")
            max_len = guidelines.get("max_caption_length", 2200)

            # Adapt Instagram caption
            source_caption = pd.get("caption_instagram", "") or ""
            if source_caption and platform == "instagram_story":
                # Shorten for stories
                sentences = source_caption.split('. ')
                adapted = '. '.join(sentences[:2]) + ('...' if len(sentences) > 2 else '')
                if len(adapted) > max_len:
                    adapted = adapted[:max_len - 3] + '...'
                pd["caption_instagram"] = adapted

            # Adapt TikTok caption
            source_tiktok = pd.get("caption_tiktok", "") or ""
            source_ig = pd.get("caption_instagram", "") or ""
            if platform == "tiktok" and (source_ig or source_tiktok):
                base_text = source_tiktok or source_ig
                sentences = base_text.split('. ')
                hook = sentences[0]
                adapted = hook + (' ' + sentences[1] if len(sentences) > 1 else '')
                if len(adapted) > max_len:
                    adapted = adapted[:max_len - 3] + '...'
                pd["caption_tiktok"] = adapted

            # Adapt slide data for story format (shorter text)
            if platform == "instagram_story" and pd.get("slide_data"):
                try:
                    slides = json.loads(pd["slide_data"]) if isinstance(pd["slide_data"], str) else pd["slide_data"]
                    for slide in slides:
                        if isinstance(slide, dict):
                            # Shorten body text for stories
                            body = slide.get("body_text", "")
                            if body and len(body) > 80:
                                slide["body_text"] = body[:77] + "..."
                            # Add CTA for stories
                            if not slide.get("cta_text"):
                                slide["cta_text"] = "Mehr erfahren ↑"
                    pd["slide_data"] = json.dumps(slides, ensure_ascii=False) if isinstance(post_data.get("slide_data"), str) else slides
                except (json.JSONDecodeError, TypeError):
                    pass

        new_post = Post(
            user_id=user_id,
            platform=platform,
            linked_post_group_id=group_id,
            **pd,
        )
        db.add(new_post)
        await db.flush()
        await db.refresh(new_post)
        created_posts.append(post_to_dict(new_post))

    await db.commit()

    return {
        "posts": created_posts,
        "linked_post_group_id": group_id,
        "count": len(created_posts),
        "adapted": adapt_content,
    }


@router.get("/{post_id}/siblings")
async def get_sibling_posts(
    post_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get all posts linked to the same multi-platform group as the given post."""
    result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if not post.linked_post_group_id:
        return {"siblings": [], "linked_post_group_id": None}

    result = await db.execute(
        select(Post).where(
            and_(
                Post.user_id == user_id,
                Post.linked_post_group_id == post.linked_post_group_id,
                Post.id != post_id,
            )
        ).order_by(Post.platform.asc())
    )
    siblings = result.scalars().all()

    return {
        "siblings": [post_to_dict(s) for s in siblings],
        "linked_post_group_id": post.linked_post_group_id,
    }


@router.post("/{post_id}/suggest-sibling-update")
async def suggest_sibling_update(
    post_id: int,
    data: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """When a linked post is edited, get suggestions for updating sibling posts."""
    changed_fields = data.get("changed_fields", {})

    result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if not post.linked_post_group_id:
        return {"suggestions": [], "siblings": []}

    result = await db.execute(
        select(Post).where(
            and_(
                Post.user_id == user_id,
                Post.linked_post_group_id == post.linked_post_group_id,
                Post.id != post_id,
            )
        ).order_by(Post.platform.asc())
    )
    siblings = result.scalars().all()

    syncable_fields = {"title", "category", "country", "tone", "scheduled_date", "scheduled_time", "cta_text", "slide_data", "custom_colors", "custom_fonts", "story_arc_id", "episode_number"}
    platform_specific = {"caption_instagram", "caption_tiktok", "hashtags_instagram", "hashtags_tiktok", "platform"}

    suggestions = []
    for field, value in changed_fields.items():
        if field in syncable_fields:
            suggestions.append({
                "field": field,
                "new_value": value,
                "apply_to": [{"id": s.id, "platform": s.platform, "title": s.title} for s in siblings],
                "auto_sync": True,
            })
        elif field in platform_specific:
            suggestions.append({
                "field": field,
                "new_value": value,
                "apply_to": [{"id": s.id, "platform": s.platform, "title": s.title} for s in siblings],
                "auto_sync": False,
                "note": "Plattform-spezifisch - manuell pruefen",
            })

    return {
        "suggestions": suggestions,
        "siblings": [post_to_dict(s) for s in siblings],
        "source_post_id": post_id,
        "source_platform": post.platform,
    }


    # sync-siblings route moved above /{post_id} routes for correct FastAPI routing
