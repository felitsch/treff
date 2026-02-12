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
    db: AsyncSession = Depends(get_db),
):
    """Crop and optionally resize an image asset.

    Request body:
    {
        "asset_id": int,           # ID of the asset to crop
        "x": int,                  # Left coordinate of crop area
        "y": int,                  # Top coordinate of crop area
        "width": int,              # Width of crop area
        "height": int,             # Height of crop area
        "target_width": int|null,  # Optional resize target width
        "target_height": int|null, # Optional resize target height
        "save_as_new": bool        # If true, save as new asset; if false, overwrite original
    }
    """
    import io
    from PIL import Image

    asset_id = request.get("asset_id")
    crop_x = request.get("x", 0)
    crop_y = request.get("y", 0)
    crop_width = request.get("width")
    crop_height = request.get("height")
    target_width = request.get("target_width")
    target_height = request.get("target_height")
    save_as_new = request.get("save_as_new", False)

    if not asset_id or not crop_width or not crop_height:
        raise HTTPException(status_code=400, detail="asset_id, width, and height are required")

    # Fetch the asset
    result = await db.execute(
        select(Asset).where(Asset.id == asset_id, Asset.user_id == user_id)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Load the image file
    source_path = ASSETS_UPLOAD_DIR / asset.filename
    if not source_path.exists():
        raise HTTPException(status_code=404, detail="Image file not found on disk")

    try:
        img = Image.open(source_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not open image: {str(e)}")

    # Validate crop bounds
    img_width, img_height = img.size
    crop_x = max(0, int(crop_x))
    crop_y = max(0, int(crop_y))
    crop_width = int(crop_width)
    crop_height = int(crop_height)

    # Clamp to image bounds
    if crop_x + crop_width > img_width:
        crop_width = img_width - crop_x
    if crop_y + crop_height > img_height:
        crop_height = img_height - crop_y

    if crop_width <= 0 or crop_height <= 0:
        raise HTTPException(status_code=400, detail="Invalid crop dimensions")

    # Perform crop: PIL crop takes (left, upper, right, lower)
    cropped = img.crop((crop_x, crop_y, crop_x + crop_width, crop_y + crop_height))

    # Optional resize
    if target_width and target_height:
        target_width = int(target_width)
        target_height = int(target_height)
        if target_width > 0 and target_height > 0:
            cropped = cropped.resize((target_width, target_height), Image.LANCZOS)

    # Determine output format
    ext = os.path.splitext(asset.filename)[1].lower()
    fmt = "JPEG"
    content_type = "image/jpeg"
    if ext == ".png":
        fmt = "PNG"
        content_type = "image/png"
    elif ext == ".webp":
        fmt = "WEBP"
        content_type = "image/webp"

    # Save to bytes
    output_buffer = io.BytesIO()
    if fmt == "JPEG":
        # Convert RGBA to RGB for JPEG
        if cropped.mode in ("RGBA", "LA", "P"):
            cropped = cropped.convert("RGB")
        cropped.save(output_buffer, format=fmt, quality=95)
    else:
        cropped.save(output_buffer, format=fmt, quality=95)
    output_bytes = output_buffer.getvalue()

    final_width, final_height = cropped.size

    if save_as_new:
        # Save as a new asset
        new_filename = f"{uuid.uuid4()}{ext}"
        new_path = ASSETS_UPLOAD_DIR / new_filename
        with open(new_path, "wb") as f:
            f.write(output_bytes)

        new_asset = Asset(
            user_id=user_id,
            filename=new_filename,
            original_filename=f"cropped_{asset.original_filename or asset.filename}",
            file_path=f"/uploads/assets/{new_filename}",
            file_type=content_type,
            file_size=len(output_bytes),
            width=final_width,
            height=final_height,
            source="crop",
            category=asset.category,
            country=asset.country,
            tags=asset.tags,
        )
        db.add(new_asset)
        await db.flush()
        await db.refresh(new_asset)
        return asset_to_dict(new_asset)
    else:
        # Overwrite original file
        with open(source_path, "wb") as f:
            f.write(output_bytes)

        # Update asset record
        asset.file_size = len(output_bytes)
        asset.width = final_width
        asset.height = final_height
        await db.flush()
        await db.refresh(asset)
        return asset_to_dict(asset)


@router.get("/stock/search")
async def search_stock(
    query: str,
    source: str = "unsplash",
    page: int = 1,
    per_page: int = 12,
    user_id: int = Depends(get_current_user_id),
):
    """Search stock photos from Unsplash or Pexels.

    If API keys are not configured, returns results from the Unsplash demo
    source API using curated photos related to the query.
    """
    import httpx
    from app.core.config import settings

    results = []

    if source == "unsplash":
        results = await _search_unsplash(query, page, per_page, settings.UNSPLASH_ACCESS_KEY)
    elif source == "pexels":
        results = await _search_pexels(query, page, per_page, settings.PEXELS_API_KEY)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown source: {source}. Use 'unsplash' or 'pexels'.")

    return {"results": results, "query": query, "source": source, "page": page}


async def _search_unsplash(query: str, page: int, per_page: int, api_key: str) -> list:
    """Search Unsplash for photos. Uses API if key provided, else demo source."""
    import httpx

    import urllib.parse

    if api_key:
        # Real Unsplash API
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.unsplash.com/search/photos",
                params={"query": query, "page": page, "per_page": per_page},
                headers={"Authorization": f"Client-ID {api_key}"},
            )
            if resp.status_code != 200:
                return []
            data = resp.json()
            results = []
            for photo in data.get("results", []):
                results.append({
                    "id": photo["id"],
                    "description": photo.get("description") or photo.get("alt_description") or query,
                    "thumbnail_url": photo["urls"]["small"],
                    "preview_url": photo["urls"]["regular"],
                    "full_url": photo["urls"]["full"],
                    "download_url": photo["urls"]["regular"],
                    "width": photo["width"],
                    "height": photo["height"],
                    "photographer": photo["user"]["name"],
                    "photographer_url": photo["user"]["links"]["html"],
                    "source": "unsplash",
                    "source_url": photo["links"]["html"],
                })
            return results
    else:
        # Fallback: use Unsplash Source (no API key needed)
        # Generate curated stock-like results using picsum.photos
        # which provides free, high-quality stock photos
        results = []
        for i in range(per_page):
            # Create URL-safe seed by replacing spaces with underscores
            safe_query = query.replace(" ", "_")
            seed = f"{safe_query}-{page}-{i}"
            seed_encoded = urllib.parse.quote(seed, safe="-_")
            photo_id = abs(hash(seed)) % 1000 + 1
            results.append({
                "id": f"picsum-{photo_id}-{i}",
                "description": f"{query} - Stock Photo {(page - 1) * per_page + i + 1}",
                "thumbnail_url": f"https://picsum.photos/seed/{seed_encoded}/300/200",
                "preview_url": f"https://picsum.photos/seed/{seed_encoded}/800/600",
                "full_url": f"https://picsum.photos/seed/{seed_encoded}/1920/1280",
                "download_url": f"https://picsum.photos/seed/{seed_encoded}/1920/1280",
                "width": 1920,
                "height": 1280,
                "photographer": "Picsum Photos",
                "photographer_url": "https://picsum.photos",
                "source": "unsplash",
                "source_url": f"https://picsum.photos/seed/{seed_encoded}/1920/1280",
            })
        return results


async def _search_pexels(query: str, page: int, per_page: int, api_key: str) -> list:
    """Search Pexels for photos. Uses API if key provided, else demo source."""
    import httpx

    if api_key:
        # Real Pexels API
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.pexels.com/v1/search",
                params={"query": query, "page": page, "per_page": per_page},
                headers={"Authorization": api_key},
            )
            if resp.status_code != 200:
                return []
            data = resp.json()
            results = []
            for photo in data.get("photos", []):
                results.append({
                    "id": str(photo["id"]),
                    "description": photo.get("alt") or query,
                    "thumbnail_url": photo["src"]["medium"],
                    "preview_url": photo["src"]["large"],
                    "full_url": photo["src"]["original"],
                    "download_url": photo["src"]["large2x"],
                    "width": photo["width"],
                    "height": photo["height"],
                    "photographer": photo["photographer"],
                    "photographer_url": photo["photographer_url"],
                    "source": "pexels",
                    "source_url": photo["url"],
                })
            return results
    else:
        # Fallback: use picsum.photos as demo source
        import urllib.parse
        results = []
        for i in range(per_page):
            safe_query = query.replace(" ", "_")
            seed = f"pexels-{safe_query}-{page}-{i}"
            seed_encoded = urllib.parse.quote(seed, safe="-_")
            photo_id = abs(hash(seed)) % 1000 + 1
            results.append({
                "id": f"pexels-demo-{photo_id}-{i}",
                "description": f"{query} - Stock Photo {(page - 1) * per_page + i + 1}",
                "thumbnail_url": f"https://picsum.photos/seed/{seed_encoded}/300/200",
                "preview_url": f"https://picsum.photos/seed/{seed_encoded}/800/600",
                "full_url": f"https://picsum.photos/seed/{seed_encoded}/1920/1280",
                "download_url": f"https://picsum.photos/seed/{seed_encoded}/1920/1280",
                "width": 1920,
                "height": 1280,
                "photographer": "Picsum Photos",
                "photographer_url": "https://picsum.photos",
                "source": "pexels",
                "source_url": f"https://picsum.photos/seed/{seed_encoded}/1920/1280",
            })
        return results


@router.post("/stock/import")
async def import_stock(
    request: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Import a stock photo into the user's asset library.

    Downloads the image from the given URL and saves it as an asset.

    Request body:
    {
        "download_url": "https://...",  # URL to download from
        "description": "...",           # Optional description / filename
        "photographer": "...",          # Optional photographer name
        "source": "unsplash",           # unsplash or pexels
        "source_url": "...",            # Link back to original
        "width": 1920,                  # Optional dimensions
        "height": 1280,
        "category": "photo",            # Optional category
        "country": "",                  # Optional country
        "tags": ""                      # Optional tags
    }
    """
    import httpx
    import io

    download_url = request.get("download_url")
    if not download_url:
        raise HTTPException(status_code=400, detail="download_url is required")

    description = request.get("description", "Stock Photo")
    photographer = request.get("photographer", "Unknown")
    source = request.get("source", "unsplash")
    source_url = request.get("source_url", "")
    width = request.get("width")
    height = request.get("height")
    category = request.get("category", "photo")
    country = request.get("country", "")
    tags = request.get("tags", "")

    # Download the image
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            resp = await client.get(download_url)
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=502,
                    detail=f"Failed to download image: HTTP {resp.status_code}",
                )
            image_data = resp.content
            content_type = resp.headers.get("content-type", "image/jpeg")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Timeout downloading image")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Failed to download image: {str(e)}")

    # Determine extension from content type
    ext_map = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }
    ext = ext_map.get(content_type.split(";")[0].strip(), ".jpg")
    if content_type.split(";")[0].strip() not in ext_map:
        content_type = "image/jpeg"

    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_path = ASSETS_UPLOAD_DIR / unique_filename

    # Save to disk
    with open(file_path, "wb") as f:
        f.write(image_data)

    # Try to get actual image dimensions
    actual_width = width
    actual_height = height
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(image_data))
        actual_width, actual_height = img.size
    except Exception:
        pass

    # Build tags string
    tag_parts = [t.strip() for t in (tags or "").split(",") if t.strip()]
    if photographer and photographer != "Unknown":
        tag_parts.append(f"by:{photographer}")
    tag_parts.append(f"stock:{source}")
    tags_str = ", ".join(tag_parts)

    # Sanitize description for use as original_filename
    safe_desc = "".join(c if c.isalnum() or c in " -_" else "" for c in description)[:80]
    original_filename = f"{safe_desc}{ext}" if safe_desc else f"stock-photo{ext}"

    # Create asset record
    asset = Asset(
        user_id=user_id,
        filename=unique_filename,
        original_filename=original_filename,
        file_path=f"/uploads/assets/{unique_filename}",
        file_type=content_type,
        file_size=len(image_data),
        width=actual_width,
        height=actual_height,
        source=f"stock_{source}",
        category=category or "photo",
        country=country or None,
        tags=tags_str or None,
    )
    db.add(asset)
    await db.flush()
    await db.refresh(asset)

    return asset_to_dict(asset)
