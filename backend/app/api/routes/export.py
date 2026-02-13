"""Export routes."""

import os
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.core.paths import get_upload_dir
from app.models.post import Post
from app.models.export_history import ExportHistory

router = APIRouter()

EXPORT_DIR = str(get_upload_dir("exports"))


def export_to_dict(export: ExportHistory) -> dict:
    """Convert ExportHistory model to dict."""
    return {
        "id": export.id,
        "post_id": export.post_id,
        "platform": export.platform,
        "format": export.format,
        "file_path": export.file_path,
        "resolution": export.resolution,
        "slide_count": export.slide_count,
        "exported_at": export.exported_at.isoformat() if export.exported_at else None,
    }


@router.post("/render")
async def render_post(
    request: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Record a post export. Client-side rendering via html2canvas.

    The actual PNG rendering happens on the client side.
    This endpoint records the export in the database and updates post status.
    """
    post_id = request.get("post_id")
    platform = request.get("platform", "instagram_feed")
    resolution = request.get("resolution", "1080")
    slide_count = request.get("slide_count", 1)

    if not post_id:
        raise HTTPException(status_code=400, detail="post_id is required")

    # Verify post belongs to user
    result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Create export record
    export = ExportHistory(
        post_id=post_id,
        platform=platform,
        format="png",
        file_path=f"exports/post_{post_id}_{platform}.png",
        resolution=resolution,
        slide_count=slide_count,
        exported_at=datetime.now(timezone.utc),
    )
    db.add(export)

    # Update post status to exported
    post.exported_at = datetime.now(timezone.utc)
    if post.status == "draft":
        post.status = "exported"

    await db.flush()
    await db.refresh(export)
    result_dict = export_to_dict(export)
    await db.commit()

    return result_dict


@router.post("/render-carousel")
async def render_carousel(
    request: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Record a carousel export."""
    post_id = request.get("post_id")
    platform = request.get("platform", "instagram_feed")
    resolution = request.get("resolution", "1080")
    slide_count = request.get("slide_count", 1)

    if not post_id:
        raise HTTPException(status_code=400, detail="post_id is required")

    result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    export = ExportHistory(
        post_id=post_id,
        platform=platform,
        format="zip",
        file_path=f"exports/post_{post_id}_{platform}_carousel.zip",
        resolution=resolution,
        slide_count=slide_count,
        exported_at=datetime.now(timezone.utc),
    )
    db.add(export)

    post.exported_at = datetime.now(timezone.utc)
    if post.status == "draft":
        post.status = "exported"

    await db.flush()
    await db.refresh(export)
    result_dict = export_to_dict(export)
    await db.commit()

    return result_dict


@router.get("/download/{export_id}")
async def download_export(
    export_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Download rendered file."""
    result = await db.execute(
        select(ExportHistory).where(ExportHistory.id == export_id)
    )
    export = result.scalar_one_or_none()
    if not export:
        raise HTTPException(status_code=404, detail="Export not found")

    # Verify the export's post belongs to the current user
    post_result = await db.execute(
        select(Post).where(Post.id == export.post_id, Post.user_id == user_id)
    )
    if not post_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Export not found")

    file_path = os.path.join(EXPORT_DIR, os.path.basename(export.file_path))
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Export file not found on disk")

    return FileResponse(file_path, filename=os.path.basename(export.file_path))


@router.get("/history")
async def get_export_history(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    post_id: int | None = None,
):
    """Get export history records, optionally filtered by post_id."""
    query = (
        select(ExportHistory)
        .join(Post, ExportHistory.post_id == Post.id)
        .where(Post.user_id == user_id)
        .order_by(ExportHistory.exported_at.desc())
    )
    if post_id:
        query = query.where(ExportHistory.post_id == post_id)

    result = await db.execute(query)
    exports = result.scalars().all()
    return [export_to_dict(e) for e in exports]


@router.post("/batch")
async def batch_export(
    request: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Record batch export for multiple posts.

    Accepts a list of post_ids and creates export records for each.
    The actual rendering happens client-side; this records export history.
    """
    post_ids = request.get("post_ids", [])
    platform = request.get("platform", "instagram_feed")
    resolution = request.get("resolution", "1080")

    if not post_ids or not isinstance(post_ids, list):
        raise HTTPException(status_code=400, detail="post_ids is required and must be a list")

    if len(post_ids) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 posts per batch export")

    # Verify all posts belong to user
    result = await db.execute(
        select(Post).where(Post.id.in_(post_ids), Post.user_id == user_id)
    )
    posts = result.scalars().all()

    if len(posts) != len(post_ids):
        found_ids = {p.id for p in posts}
        missing = [pid for pid in post_ids if pid not in found_ids]
        raise HTTPException(
            status_code=404,
            detail=f"Posts not found or not owned by user: {missing}"
        )

    export_records = []
    now = datetime.now(timezone.utc)

    for post in posts:
        # Determine slide count from slide_data
        slide_count = 1
        if post.slide_data:
            try:
                import json
                slides = json.loads(post.slide_data)
                if isinstance(slides, list):
                    slide_count = len(slides)
            except (json.JSONDecodeError, TypeError):
                pass

        fmt = "zip" if slide_count > 1 else "png"
        suffix = "_carousel.zip" if slide_count > 1 else ".png"

        export = ExportHistory(
            post_id=post.id,
            platform=post.platform or platform,
            format=fmt,
            file_path=f"exports/post_{post.id}_{post.platform or platform}{suffix}",
            resolution=resolution,
            slide_count=slide_count,
            exported_at=now,
        )
        db.add(export)

        # Update post status
        post.exported_at = now
        if post.status == "draft":
            post.status = "exported"

    await db.flush()

    # Collect export records after flush (IDs assigned)
    for post in posts:
        # Get the latest export record for this post
        exp_result = await db.execute(
            select(ExportHistory)
            .where(ExportHistory.post_id == post.id)
            .order_by(ExportHistory.id.desc())
            .limit(1)
        )
        exp = exp_result.scalar_one_or_none()
        if exp:
            export_records.append(export_to_dict(exp))

    await db.commit()

    return {
        "exports": export_records,
        "count": len(export_records),
        "status": "ok",
    }
