"""Asset routes."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.asset import Asset

router = APIRouter()


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
            (Asset.filename.ilike(f"%{search}%")) | (Asset.tags.ilike(f"%{search}%"))
        )

    result = await db.execute(query.order_by(Asset.created_at.desc()))
    return result.scalars().all()


@router.post("/upload", status_code=201)
async def upload_asset(
    file: UploadFile = File(...),
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

    # TODO: Save file to disk and create asset record
    import uuid
    filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = f"app/static/uploads/assets/{filename}"

    # Read and save file
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    asset = Asset(
        user_id=user_id,
        filename=filename,
        original_filename=file.filename,
        file_path=file_path,
        file_type=file.content_type,
        file_size=len(content),
        source="upload",
    )
    db.add(asset)
    await db.flush()
    await db.refresh(asset)
    return asset


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

    # TODO: Delete file from disk
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
    return asset


@router.post("/crop")
async def crop_asset(
    request: dict,
    user_id: int = Depends(get_current_user_id),
):
    """Crop image to dimensions."""
    # TODO: Implement with Pillow
    return {"message": "Crop endpoint", "data": request}


@router.get("/stock/search")
async def search_stock(
    query: str,
    source: str = "unsplash",
    user_id: int = Depends(get_current_user_id),
):
    """Search stock photos."""
    # TODO: Implement Unsplash/Pexels API
    return {"results": [], "query": query, "source": source}


@router.post("/stock/import")
async def import_stock(
    request: dict,
    user_id: int = Depends(get_current_user_id),
):
    """Import stock photo to library."""
    # TODO: Implement
    return {"message": "Stock import endpoint", "data": request}
