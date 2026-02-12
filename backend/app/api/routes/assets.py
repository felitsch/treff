"""Asset routes."""

import os
import uuid
from typing import Optional
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.asset import Asset

router = APIRouter()

# Resolve uploads directory: __file__ is backend/app/api/routes/assets.py
# parent.parent.parent = backend/app/ which contains static/uploads/assets
APP_DIR = Path(__file__).resolve().parent.parent.parent
ASSETS_UPLOAD_DIR = APP_DIR / "static" / "uploads" / "assets"
ASSETS_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def asset_to_dict(asset: Asset) -> dict:
    """Convert Asset model to plain dict to avoid async serialization issues."""
    return {
        "id": asset.id,
        "user_id": asset.user_id,
        "filename": asset.filename,
        "original_filename": asset.original_filename,
        "file_path": asset.file_path,
        "file_type": asset.file_type,
        "file_size": asset.file_size,
        "width": asset.width,
        "height": asset.height,
        "source": asset.source,
        "ai_prompt": asset.ai_prompt,
        "category": asset.category,
        "country": asset.country,
        "tags": asset.tags,
        "usage_count": asset.usage_count,
        "created_at": asset.created_at.isoformat() if asset.created_at else None,
    }


@router.get("")
async def list_assets(
    category: Optional[str] = None,
    country: Optional[str] = None,
    source: Optional[str] = None,
    search: Optional[str] = None,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List assets with optional filters."""
    query = select(Asset).where(Asset.user_id == user_id)

    if category:
        query = query.where(Asset.category == category)
    if country:
        query = query.where(Asset.country == country)
    if source:
        query = query.where(Asset.source == source)
    if search:
        query = query.where(
            (Asset.filename.ilike(f"%{search}%"))
            | (Asset.original_filename.ilike(f"%{search}%"))
            | (Asset.tags.ilike(f"%{search}%"))
        )

    result = await db.execute(query.order_by(Asset.created_at.desc()))
    assets = result.scalars().all()
    return [asset_to_dict(a) for a in assets]


@router.post("/upload", status_code=201)
async def upload_asset(
    file: UploadFile = File(...),
    category: Optional[str] = Form(None),
    country: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Upload an image file."""
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file.content_type} not allowed. Use: {', '.join(allowed_types)}",
        )

    # Generate unique filename
    ext = os.path.splitext(file.filename or "image.jpg")[1] or ".jpg"
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_path = ASSETS_UPLOAD_DIR / unique_filename

    # Read and save file
    content = await file.read()
    file_size = len(content)

    with open(file_path, "wb") as f:
        f.write(content)

    # Try to get image dimensions
    width = None
    height = None
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(content))
        width, height = img.size
    except Exception:
        pass  # Pillow not available or invalid image - skip dimensions

    # Create asset record
    asset = Asset(
        user_id=user_id,
        filename=unique_filename,
        original_filename=file.filename,
        file_path=f"/uploads/assets/{unique_filename}",
        file_type=file.content_type,
        file_size=file_size,
        width=width,
        height=height,
        source="upload",
        category=category,
        country=country,
        tags=tags,
    )
    db.add(asset)
    await db.flush()
    await db.refresh(asset)

    return asset_to_dict(asset)


@router.delete("/{asset_id}")
async def delete_asset(
    asset_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete an asset."""
    result = await db.execute(
        select(Asset).where(Asset.id == asset_id, Asset.user_id == user_id)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Delete file from disk
    try:
        disk_path = ASSETS_UPLOAD_DIR / asset.filename
        if disk_path.exists():
            disk_path.unlink()
    except Exception:
        pass  # File already gone or permission issue

    await db.delete(asset)
    return {"message": "Asset deleted"}


@router.put("/{asset_id}")
async def update_asset(
    asset_id: int,
    asset_data: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update asset tags, category."""
    result = await db.execute(
        select(Asset).where(Asset.id == asset_id, Asset.user_id == user_id)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    for key, value in asset_data.items():
        if hasattr(asset, key) and key not in ("id", "user_id"):
            setattr(asset, key, value)

    await db.flush()
    await db.refresh(asset)
    return asset_to_dict(asset)


@router.post("/crop")
async def crop_asset(
    request: dict,
    user_id: int = Depends(get_current_user_id),
):
    """Crop image to dimensions."""
    return {"message": "Crop endpoint - not yet implemented", "data": request}


@router.get("/stock/search")
async def search_stock(
    query: str,
    source: str = "unsplash",
    user_id: int = Depends(get_current_user_id),
):
    """Search stock photos."""
    return {"results": [], "query": query, "source": source}


@router.post("/stock/import")
async def import_stock(
    request: dict,
    user_id: int = Depends(get_current_user_id),
):
    """Import stock photo to library."""
    return {"message": "Stock import endpoint - not yet implemented", "data": request}
