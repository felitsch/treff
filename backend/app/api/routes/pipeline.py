"""Content Pipeline routes - Smart Content Pipeline for media analysis, inbox, processing, and multiplication."""

import json
import logging
import os
import uuid
from typing import Optional
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.core.paths import get_upload_dir
from app.models.asset import Asset
from app.models.post import Post
from app.models.student import Student
from app.models.pipeline_item import PipelineItem
from app.services.content_analyzer import analyze_media_with_ai
from app.services.content_multiplier import multiply_content

logger = logging.getLogger(__name__)
router = APIRouter()

PIPELINE_UPLOAD_DIR = get_upload_dir("pipeline")

# Allowed file types for pipeline analysis
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"]
ALLOWED_VIDEO_TYPES = ["video/mp4", "video/quicktime", "video/webm"]
ALLOWED_TYPES = ALLOWED_IMAGE_TYPES + ALLOWED_VIDEO_TYPES


def pipeline_item_to_dict(item: PipelineItem, student_name: str = None, asset: Asset = None) -> dict:
    """Convert PipelineItem to dict for API response."""
    return {
        "id": item.id,
        "user_id": item.user_id,
        "student_id": item.student_id,
        "student_name": student_name,
        "asset_id": item.asset_id,
        "asset_filename": asset.original_filename if asset else None,
        "asset_file_type": asset.file_type if asset else None,
        "asset_thumbnail_path": asset.thumbnail_path if asset else None,
        "suggested_post_type": item.suggested_post_type,
        "suggested_caption_seeds": json.loads(item.suggested_caption_seeds) if item.suggested_caption_seeds else None,
        "suggested_platforms": json.loads(item.suggested_platforms) if item.suggested_platforms else None,
        "detected_country": item.detected_country,
        "analysis_summary": item.analysis_summary,
        "status": item.status,
        "result_post_id": item.result_post_id,
        "error_message": item.error_message,
        "source_description": item.source_description,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }


# ═══════════════════════════════════════════════════════════════════════
# POST /api/pipeline/analyze-media
# Upload image/video, AI analyzes and suggests post type
# ═══════════════════════════════════════════════════════════════════════

@router.post("/analyze-media")
async def analyze_media(
    file: UploadFile = File(...),
    student_id: Optional[int] = Form(default=None),
    source_description: Optional[str] = Form(default=None),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Upload and analyze an image/video. AI suggests post type, captions, platforms, and country."""
    # Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Allowed: {', '.join(ALLOWED_TYPES)}"
        )

    # Validate student exists if provided
    if student_id:
        result = await db.execute(
            select(Student).where(Student.id == student_id, Student.user_id == user_id)
        )
        student = result.scalar_one_or_none()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

    # Save the uploaded file as an asset
    file_bytes = await file.read()
    file_ext = Path(file.filename).suffix if file.filename else ".jpg"
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = PIPELINE_UPLOAD_DIR / unique_filename

    # Ensure directory exists
    PIPELINE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # Create asset record
    asset = Asset(
        user_id=user_id,
        filename=unique_filename,
        original_filename=file.filename or unique_filename,
        file_path=f"/uploads/pipeline/{unique_filename}",
        file_type=file.content_type,
        file_size=len(file_bytes),
        source="upload",
        category="pipeline",
    )
    db.add(asset)
    await db.flush()  # Get asset ID

    # Run AI analysis
    analysis = await analyze_media_with_ai(
        file_path=str(file_path),
        file_type=file.content_type,
        source_description=source_description,
    )

    # Create pipeline item
    pipeline_item = PipelineItem(
        user_id=user_id,
        student_id=student_id,
        asset_id=asset.id,
        suggested_post_type=analysis["suggested_post_type"],
        suggested_caption_seeds=json.dumps(analysis["suggested_caption_seeds"], ensure_ascii=False),
        suggested_platforms=json.dumps(analysis["suggested_platforms"], ensure_ascii=False),
        detected_country=analysis["detected_country"],
        analysis_summary=analysis["analysis_summary"],
        status="analyzed",
        source_description=source_description,
    )
    db.add(pipeline_item)
    await db.flush()

    return {
        "pipeline_item_id": pipeline_item.id,
        "suggested_post_type": analysis["suggested_post_type"],
        "suggested_caption_seeds": analysis["suggested_caption_seeds"],
        "suggested_platforms": analysis["suggested_platforms"],
        "detected_country": analysis["detected_country"],
        "analysis_summary": analysis["analysis_summary"],
    }


# ═══════════════════════════════════════════════════════════════════════
# GET /api/pipeline/inbox
# List unprocessed student uploads with pagination and filters
# ═══════════════════════════════════════════════════════════════════════

@router.get("/inbox")
async def get_inbox(
    student_id: Optional[int] = Query(default=None),
    status: Optional[str] = Query(default=None, pattern="^(pending|analyzed|processing|processed|failed)$"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List pipeline inbox items with pagination and optional filters."""
    # Build query
    where_clauses = [PipelineItem.user_id == user_id]

    if student_id:
        where_clauses.append(PipelineItem.student_id == student_id)
    if status:
        where_clauses.append(PipelineItem.status == status)

    # Count total
    count_query = select(func.count(PipelineItem.id)).where(*where_clauses)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Fetch items with pagination
    offset = (page - 1) * limit
    items_query = (
        select(PipelineItem)
        .where(*where_clauses)
        .order_by(desc(PipelineItem.created_at))
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(items_query)
    items = result.scalars().all()

    # Enrich with student names and asset info
    response_items = []
    for item in items:
        student_name = None
        asset = None

        if item.student_id:
            s_result = await db.execute(
                select(Student.name).where(Student.id == item.student_id)
            )
            s_row = s_result.first()
            student_name = s_row[0] if s_row else None

        if item.asset_id:
            a_result = await db.execute(
                select(Asset).where(Asset.id == item.asset_id)
            )
            asset = a_result.scalar_one_or_none()

        response_items.append(pipeline_item_to_dict(item, student_name, asset))

    return {
        "items": response_items,
        "total": total,
        "page": page,
        "limit": limit,
    }


# ═══════════════════════════════════════════════════════════════════════
# POST /api/pipeline/process
# Process an inbox item into a draft post
# ═══════════════════════════════════════════════════════════════════════

@router.post("/process")
async def process_inbox_item(
    body: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Process an inbox item: create a draft post from the analyzed media."""
    inbox_item_id = body.get("inbox_item_id")
    if not inbox_item_id:
        raise HTTPException(status_code=400, detail="inbox_item_id is required")

    # Fetch the pipeline item
    result = await db.execute(
        select(PipelineItem).where(
            PipelineItem.id == inbox_item_id,
            PipelineItem.user_id == user_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Pipeline item not found")

    if item.status == "processed":
        raise HTTPException(status_code=400, detail="Item already processed")

    # Mark as processing
    item.status = "processing"
    db.add(item)
    await db.flush()

    try:
        # Determine post parameters from analysis + overrides
        post_type = body.get("post_type") or item.suggested_post_type or "instagram_feed"
        platform = body.get("platform") or post_type
        tone = body.get("tone", "jugendlich")
        country = body.get("country") or item.detected_country

        # Parse caption seeds
        caption_seeds = []
        if item.suggested_caption_seeds:
            caption_seeds = json.loads(item.suggested_caption_seeds)

        # Use first caption seed as starting caption, or generate from AI
        caption = caption_seeds[0] if caption_seeds else (item.analysis_summary or "")

        # Generate title from analysis
        title = _generate_title(item, country)

        # Determine category based on content
        category = _determine_category(item, country)

        # Set captions based on platform
        caption_instagram = None
        caption_tiktok = None
        if platform in ("instagram_feed", "instagram_story", "carousel"):
            caption_instagram = caption
        if platform == "tiktok":
            caption_tiktok = caption

        # Create the draft post
        new_post = Post(
            user_id=user_id,
            category=category,
            country=country,
            platform=platform,
            status="draft",
            title=title,
            slide_data="[]",
            caption_instagram=caption_instagram,
            caption_tiktok=caption_tiktok,
            cta_text="Mehr erfahren",
            tone=tone,
            student_id=item.student_id,
        )
        db.add(new_post)
        await db.flush()

        # Update pipeline item
        item.status = "processed"
        item.result_post_id = new_post.id
        item.error_message = None
        db.add(item)

        return {
            "post_id": new_post.id,
            "title": new_post.title,
            "category": new_post.category,
            "platform": new_post.platform,
            "country": new_post.country,
            "status": new_post.status,
            "caption_instagram": new_post.caption_instagram,
            "caption_tiktok": new_post.caption_tiktok,
            "message": f"Draft-Post '{new_post.title}' erfolgreich erstellt",
        }

    except Exception as e:
        item.status = "failed"
        item.error_message = str(e)
        db.add(item)
        logger.error(f"Failed to process pipeline item {inbox_item_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════
# POST /api/pipeline/multiply
# Content Multiplier - one post → derivative formats
# ═══════════════════════════════════════════════════════════════════════

@router.post("/multiply")
async def multiply_post(
    body: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Generate derivative posts from a source post for different platforms/formats."""
    post_id = body.get("post_id")
    if not post_id:
        raise HTTPException(status_code=400, detail="post_id is required")

    formats = body.get("formats", ["instagram_story", "tiktok"])
    if not formats or not isinstance(formats, list):
        raise HTTPException(status_code=400, detail="formats must be a non-empty list")

    valid_formats = ["instagram_feed", "instagram_story", "tiktok", "carousel"]
    for fmt in formats:
        if fmt not in valid_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid format: {fmt}. Valid: {', '.join(valid_formats)}"
            )

    # Fetch the source post
    result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user_id)
    )
    source_post = result.scalar_one_or_none()
    if not source_post:
        raise HTTPException(status_code=404, detail="Source post not found")

    # Generate derivatives
    derivatives = await multiply_content(
        source_post=source_post,
        target_formats=formats,
        user_id=user_id,
        db=db,
    )

    if not derivatives:
        return {
            "source_post_id": post_id,
            "derivatives": [],
            "message": "Keine neuen Formate zum Generieren (Quellformat uebersprungen oder alle Formate identisch)",
        }

    return {
        "source_post_id": post_id,
        "derivatives": derivatives,
        "message": f"{len(derivatives)} Derivat(e) erfolgreich erstellt",
    }


# ═══════════════════════════════════════════════════════════════════════
# Helper functions
# ═══════════════════════════════════════════════════════════════════════

def _generate_title(item: PipelineItem, country: Optional[str] = None) -> str:
    """Generate a post title from pipeline item analysis."""
    country_names = {
        "usa": "USA",
        "kanada": "Kanada",
        "australien": "Australien",
        "neuseeland": "Neuseeland",
        "irland": "Irland",
    }
    country_name = country_names.get(country, "Ausland") if country else "Ausland"

    if item.analysis_summary:
        # Use first sentence of analysis as title basis
        summary = item.analysis_summary
        if len(summary) > 60:
            summary = summary[:57].rsplit(" ", 1)[0] + "..."
        return summary

    return f"Highschool-Impressionen aus {country_name}"


def _determine_category(item: PipelineItem, country: Optional[str] = None) -> str:
    """Determine post category from pipeline item analysis."""
    post_type = item.suggested_post_type or "instagram_feed"

    # Map suggested post type to categories
    if country:
        return "laender_spotlight"

    type_to_category = {
        "instagram_feed": "schueler_spotlight",
        "instagram_story": "behind_the_scenes",
        "tiktok": "fun_facts",
        "carousel": "laender_spotlight",
    }

    return type_to_category.get(post_type, "schueler_spotlight")
