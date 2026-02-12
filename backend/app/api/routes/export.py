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
from app.models.post import Post
from app.models.export_history import ExportHistory

router = APIRouter()

EXPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)


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

    file_path = os.path.join(EXPORT_DIR, os.path.basename(export.file_path))
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Export file not found on disk")

    return FileResponse(file_path, filename=os.path.basename(export.file_path))


@router.post("/batch")
async def batch_export(
    request: dict,
    user_id: int = Depends(get_current_user_id),
):
    """Render multiple posts."""
    return {"message": "Batch export is handled client-side", "status": "ok"}
