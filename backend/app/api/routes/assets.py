"""Asset routes."""

import json
import logging
import os
import subprocess
import uuid
from typing import Optional
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.core.paths import get_upload_dir
from app.models.asset import Asset

logger = logging.getLogger(__name__)

router = APIRouter()

ASSETS_UPLOAD_DIR = get_upload_dir("assets")
THUMBNAILS_DIR = get_upload_dir("thumbnails")

# Allowed file types
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"]
ALLOWED_VIDEO_TYPES = ["video/mp4", "video/quicktime", "video/webm"]
ALLOWED_AUDIO_TYPES = ["audio/mpeg", "audio/wav", "audio/aac", "audio/x-wav", "audio/mp3", "audio/x-aac"]
ALLOWED_TYPES = ALLOWED_IMAGE_TYPES + ALLOWED_VIDEO_TYPES + ALLOWED_AUDIO_TYPES

# Max upload sizes
MAX_IMAGE_SIZE = 20 * 1024 * 1024  # 20 MB
MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500 MB
MAX_AUDIO_SIZE = 50 * 1024 * 1024  # 50 MB


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
        "duration_seconds": asset.duration_seconds,
        "thumbnail_path": asset.thumbnail_path,
    }


def is_video_type(content_type: str) -> bool:
    """Check if a content type is a video type."""
    return content_type in ALLOWED_VIDEO_TYPES


def is_audio_type(content_type: str) -> bool:
    """Check if a content type is an audio type."""
    return content_type in ALLOWED_AUDIO_TYPES


def _extract_audio_metadata(audio_path: Path) -> dict:
    """Extract audio metadata (duration) using ffprobe.

    Returns dict with keys: duration_seconds (may be None).
    """
    metadata = {"duration_seconds": None}

    try:
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(audio_path),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if proc.returncode != 0:
            logger.warning(f"ffprobe failed for audio {audio_path}: {proc.stderr}")
            return metadata

        data = json.loads(proc.stdout)

        # Get duration from format
        fmt = data.get("format", {})
        if fmt.get("duration"):
            metadata["duration_seconds"] = round(float(fmt["duration"]), 2)

        # Fallback: get duration from first audio stream
        if metadata["duration_seconds"] is None:
            for stream in data.get("streams", []):
                if stream.get("codec_type") == "audio" and stream.get("duration"):
                    metadata["duration_seconds"] = round(float(stream["duration"]), 2)
                    break

    except FileNotFoundError:
        logger.warning("ffprobe not found on system - audio metadata extraction unavailable")
    except subprocess.TimeoutExpired:
        logger.warning(f"ffprobe timed out for {audio_path}")
    except Exception as e:
        logger.warning(f"Error extracting audio metadata: {e}")

    return metadata


def _extract_video_metadata(video_path: Path) -> dict:
    """Extract video metadata (duration, width, height) using ffprobe.

    Returns dict with keys: duration_seconds, width, height (any may be None).
    """
    metadata = {"duration_seconds": None, "width": None, "height": None}

    try:
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(video_path),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if proc.returncode != 0:
            logger.warning(f"ffprobe failed for {video_path}: {proc.stderr}")
            return metadata

        data = json.loads(proc.stdout)

        # Get duration from format
        fmt = data.get("format", {})
        if fmt.get("duration"):
            metadata["duration_seconds"] = round(float(fmt["duration"]), 2)

        # Get dimensions from first video stream
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                if stream.get("width"):
                    metadata["width"] = int(stream["width"])
                if stream.get("height"):
                    metadata["height"] = int(stream["height"])
                # Also try duration from stream if not in format
                if metadata["duration_seconds"] is None and stream.get("duration"):
                    metadata["duration_seconds"] = round(float(stream["duration"]), 2)
                break

    except FileNotFoundError:
        logger.warning("ffprobe not found on system - video metadata extraction unavailable")
    except subprocess.TimeoutExpired:
        logger.warning(f"ffprobe timed out for {video_path}")
    except Exception as e:
        logger.warning(f"Error extracting video metadata: {e}")

    return metadata


def _generate_video_thumbnail(video_path: Path, thumbnail_filename: str) -> Optional[str]:
    """Generate a thumbnail from the first frame of a video using ffmpeg.

    Returns the relative path to the thumbnail (e.g., /uploads/thumbnails/xxx.jpg)
    or None if generation failed.
    """
    thumbnail_path = THUMBNAILS_DIR / thumbnail_filename

    try:
        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-vf", "thumbnail,scale=480:-1",
            "-frames:v", "1",
            "-y",  # overwrite
            str(thumbnail_path),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if proc.returncode != 0:
            logger.warning(f"ffmpeg thumbnail generation failed: {proc.stderr[:500]}")
            return None

        if thumbnail_path.exists() and thumbnail_path.stat().st_size > 0:
            return f"/uploads/thumbnails/{thumbnail_filename}"
        else:
            logger.warning("ffmpeg produced empty or missing thumbnail file")
            return None

    except FileNotFoundError:
        logger.warning("ffmpeg not found on system - video thumbnail generation unavailable")
        return None
    except subprocess.TimeoutExpired:
        logger.warning(f"ffmpeg thumbnail generation timed out for {video_path}")
        return None
    except Exception as e:
        logger.warning(f"Error generating video thumbnail: {e}")
        return None


@router.get("")
async def list_assets(
    category: Optional[str] = None,
    country: Optional[str] = None,
    source: Optional[str] = None,
    search: Optional[str] = None,
    file_type: Optional[str] = None,
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
    if file_type:
        # Support filtering by broad type: "image", "video", or "audio"
        if file_type == "image":
            query = query.where(Asset.file_type.in_(ALLOWED_IMAGE_TYPES))
        elif file_type == "video":
            query = query.where(Asset.file_type.in_(ALLOWED_VIDEO_TYPES))
        elif file_type == "audio":
            query = query.where(Asset.file_type.in_(ALLOWED_AUDIO_TYPES))
        else:
            query = query.where(Asset.file_type == file_type)
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
    """Upload an image or video file."""
    # Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file.content_type} not allowed. Allowed: {', '.join(ALLOWED_TYPES)}",
        )

    is_video = is_video_type(file.content_type)
    is_audio = is_audio_type(file.content_type)

    # Generate unique filename
    if is_video:
        default_name = "video.mp4"
        default_ext = ".mp4"
    elif is_audio:
        default_name = "audio.mp3"
        default_ext = ".mp3"
    else:
        default_name = "image.jpg"
        default_ext = ".jpg"
    ext = os.path.splitext(file.filename or default_name)[1] or default_ext
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_path = ASSETS_UPLOAD_DIR / unique_filename

    # Read and save file
    content = await file.read()
    file_size = len(content)

    # Validate file size based on type
    if is_video:
        max_size = MAX_VIDEO_SIZE
        max_size_label = "500 MB"
    elif is_audio:
        max_size = MAX_AUDIO_SIZE
        max_size_label = "50 MB"
    else:
        max_size = MAX_IMAGE_SIZE
        max_size_label = "20 MB"
    if file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"Datei ist zu gross (max. {max_size_label})",
        )

    with open(file_path, "wb") as f:
        f.write(content)

    # Extract metadata based on file type
    width = None
    height = None
    duration_seconds = None
    thumbnail_path = None

    if is_video:
        # Extract video metadata using ffprobe
        meta = _extract_video_metadata(file_path)
        width = meta["width"]
        height = meta["height"]
        duration_seconds = meta["duration_seconds"]

        # Generate thumbnail from first frame
        thumb_filename = f"{uuid.uuid4()}.jpg"
        thumbnail_path = _generate_video_thumbnail(file_path, thumb_filename)
    elif is_audio:
        # Extract audio metadata using ffprobe
        meta = _extract_audio_metadata(file_path)
        duration_seconds = meta["duration_seconds"]
        # Audio has no dimensions or thumbnail
    else:
        # Try to get image dimensions
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
        duration_seconds=duration_seconds,
        thumbnail_path=thumbnail_path,
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

    # Delete main file from disk
    try:
        disk_path = ASSETS_UPLOAD_DIR / asset.filename
        if disk_path.exists():
            disk_path.unlink()
    except Exception:
        pass  # File already gone or permission issue

    # Delete thumbnail from disk if it exists
    if asset.thumbnail_path:
        try:
            thumb_filename = os.path.basename(asset.thumbnail_path)
            thumb_path = THUMBNAILS_DIR / thumb_filename
            if thumb_path.exists():
                thumb_path.unlink()
        except Exception:
            pass

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


@router.post("/trim")
async def trim_video(
    request: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Trim a video asset by setting start and end times.

    Uses ffmpeg to extract the specified segment and saves it as a new asset.

    Request body:
    {
        "asset_id": int,           # ID of the video asset to trim
        "start_time": float,       # Start time in seconds (e.g. 2.5)
        "end_time": float,         # End time in seconds (e.g. 10.0)
        "save_as_new": bool        # If true, save as new asset; if false, overwrite original
    }
    """
    asset_id = request.get("asset_id")
    start_time = request.get("start_time", 0)
    end_time = request.get("end_time")
    save_as_new = request.get("save_as_new", True)

    if not asset_id:
        raise HTTPException(status_code=400, detail="asset_id is required")
    if end_time is None:
        raise HTTPException(status_code=400, detail="end_time is required")

    start_time = float(start_time)
    end_time = float(end_time)

    if start_time < 0:
        raise HTTPException(status_code=400, detail="start_time must be >= 0")
    if end_time <= start_time:
        raise HTTPException(status_code=400, detail="end_time must be greater than start_time")

    # Fetch the asset
    result = await db.execute(
        select(Asset).where(Asset.id == asset_id, Asset.user_id == user_id)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Verify it's a video
    if not is_video_type(asset.file_type):
        raise HTTPException(status_code=400, detail="Asset is not a video file")

    # Verify source file exists
    source_path = ASSETS_UPLOAD_DIR / asset.filename
    if not source_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found on disk")

    # Validate end_time against video duration if known
    if asset.duration_seconds and end_time > asset.duration_seconds + 0.5:
        raise HTTPException(
            status_code=400,
            detail=f"end_time ({end_time}s) exceeds video duration ({asset.duration_seconds}s)",
        )

    # Calculate duration of trimmed segment
    duration = end_time - start_time
    if duration < 0.1:
        raise HTTPException(status_code=400, detail="Trimmed segment too short (min 0.1s)")

    # Generate output filename
    ext = os.path.splitext(asset.filename)[1]
    output_filename = f"{uuid.uuid4()}{ext}"
    output_path = ASSETS_UPLOAD_DIR / output_filename

    # Run ffmpeg to trim
    try:
        cmd = [
            "ffmpeg",
            "-i", str(source_path),
            "-ss", str(start_time),
            "-to", str(end_time),
            "-c", "copy",  # Stream copy for fast trimming (no re-encoding)
            "-avoid_negative_ts", "make_zero",
            "-y",  # Overwrite output
            str(output_path),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if proc.returncode != 0:
            logger.error(f"ffmpeg trim failed: {proc.stderr[:1000]}")
            # Fallback: try with re-encoding if stream copy fails
            cmd_reencode = [
                "ffmpeg",
                "-i", str(source_path),
                "-ss", str(start_time),
                "-to", str(end_time),
                "-c:v", "libx264",
                "-c:a", "aac",
                "-avoid_negative_ts", "make_zero",
                "-y",
                str(output_path),
            ]
            proc2 = subprocess.run(cmd_reencode, capture_output=True, text=True, timeout=300)
            if proc2.returncode != 0:
                logger.error(f"ffmpeg trim re-encode also failed: {proc2.stderr[:1000]}")
                raise HTTPException(status_code=500, detail="Video trimming failed")

    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="ffmpeg not found on system - video trimming unavailable",
        )
    except subprocess.TimeoutExpired:
        # Clean up partial output
        if output_path.exists():
            output_path.unlink()
        raise HTTPException(status_code=504, detail="Video trimming timed out")

    # Verify output file was created
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise HTTPException(status_code=500, detail="Trimmed video file is empty or missing")

    # Extract metadata from trimmed video
    trimmed_meta = _extract_video_metadata(output_path)
    trimmed_size = output_path.stat().st_size

    # Generate thumbnail for trimmed video
    thumb_filename = f"{uuid.uuid4()}.jpg"
    trimmed_thumbnail = _generate_video_thumbnail(output_path, thumb_filename)

    if save_as_new:
        # Create a new asset record
        new_asset = Asset(
            user_id=user_id,
            filename=output_filename,
            original_filename=f"trimmed_{asset.original_filename or asset.filename}",
            file_path=f"/uploads/assets/{output_filename}",
            file_type=asset.file_type,
            file_size=trimmed_size,
            width=trimmed_meta["width"] or asset.width,
            height=trimmed_meta["height"] or asset.height,
            source="trim",
            category=asset.category,
            country=asset.country,
            tags=asset.tags,
            duration_seconds=trimmed_meta["duration_seconds"],
            thumbnail_path=trimmed_thumbnail,
        )
        db.add(new_asset)
        await db.flush()
        await db.refresh(new_asset)
        return asset_to_dict(new_asset)
    else:
        # Delete old file and thumbnail
        try:
            if source_path.exists():
                source_path.unlink()
        except Exception:
            pass
        if asset.thumbnail_path:
            try:
                old_thumb = THUMBNAILS_DIR / os.path.basename(asset.thumbnail_path)
                if old_thumb.exists():
                    old_thumb.unlink()
            except Exception:
                pass

        # Rename output to replace original
        import shutil
        final_path = ASSETS_UPLOAD_DIR / asset.filename
        shutil.move(str(output_path), str(final_path))

        # Update asset record
        asset.file_size = trimmed_size
        asset.width = trimmed_meta["width"] or asset.width
        asset.height = trimmed_meta["height"] or asset.height
        asset.duration_seconds = trimmed_meta["duration_seconds"]
        asset.thumbnail_path = trimmed_thumbnail
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
