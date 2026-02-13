"""Video Export routes - Export videos in social media formats (9:16, 1:1, 4:5).

Supports smart cropping with focus point, compression quality control,
platform-specific presets, ffmpeg-based export pipeline, and batch export.
"""

import json
import logging
import os
import shutil
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.core.paths import get_upload_dir
from app.models.asset import Asset
from app.models.video_export import VideoExport

logger = logging.getLogger(__name__)

router = APIRouter()

ASSETS_DIR = get_upload_dir("assets")
COMPOSED_DIR = get_upload_dir("composed")
VIDEO_EXPORTS_DIR = get_upload_dir("video_exports")

FFMPEG_AVAILABLE = shutil.which("ffmpeg") is not None


# ---- Aspect ratio definitions ----
ASPECT_RATIOS = {
    "9:16": {"width": 1080, "height": 1920, "label": "Reel/TikTok (9:16)", "ratio": 9 / 16},
    "1:1": {"width": 1080, "height": 1080, "label": "Feed Quadrat (1:1)", "ratio": 1.0},
    "4:5": {"width": 1080, "height": 1350, "label": "Feed Portrait (4:5)", "ratio": 4 / 5},
}

# ---- Platform presets ----
PLATFORM_PRESETS = {
    "instagram_reel": {
        "label": "Instagram Reel",
        "aspect_ratio": "9:16",
        "max_duration": 90,
        "max_file_size_mb": 250,
        "recommended_quality": 80,
        "codec": "h264",
    },
    "instagram_feed": {
        "label": "Instagram Feed",
        "aspect_ratio": "1:1",
        "max_duration": 60,
        "max_file_size_mb": 250,
        "recommended_quality": 80,
        "codec": "h264",
    },
    "instagram_feed_portrait": {
        "label": "Instagram Feed (Portrait)",
        "aspect_ratio": "4:5",
        "max_duration": 60,
        "max_file_size_mb": 250,
        "recommended_quality": 80,
        "codec": "h264",
    },
    "tiktok": {
        "label": "TikTok",
        "aspect_ratio": "9:16",
        "max_duration": 180,
        "max_file_size_mb": 287,
        "recommended_quality": 75,
        "codec": "h264",
    },
}


# ---- Pydantic schemas ----
class VideoExportRequest(BaseModel):
    """Request to export a video in a specific format."""
    asset_id: int
    aspect_ratio: str = "9:16"  # 9:16, 1:1, 4:5
    platform: str = "instagram_reel"  # instagram_reel, instagram_feed, instagram_feed_portrait, tiktok
    quality: int = Field(default=75, ge=1, le=100)  # 1-100
    focus_x: float = Field(default=50.0, ge=0, le=100)  # Focus point X percentage
    focus_y: float = Field(default=50.0, ge=0, le=100)  # Focus point Y percentage
    max_duration: Optional[float] = None  # Override platform max duration


class BatchExportRequest(BaseModel):
    """Request to export a video in multiple formats at once."""
    asset_id: int
    formats: list[dict] = Field(..., min_length=1, max_length=5)
    # Each format: { aspect_ratio, platform, quality, focus_x, focus_y }


# ---- Helpers ----
def _get_video_info(video_path: Path) -> dict:
    """Get video metadata using ffprobe."""
    info = {"duration": 0, "width": 0, "height": 0, "has_audio": False, "codec": "unknown"}
    try:
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", str(video_path),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if proc.returncode != 0:
            return info
        data = json.loads(proc.stdout)

        fmt = data.get("format", {})
        if fmt.get("duration"):
            info["duration"] = float(fmt["duration"])

        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                info["width"] = int(stream.get("width", 0))
                info["height"] = int(stream.get("height", 0))
                info["codec"] = stream.get("codec_name", "unknown")
                if info["duration"] == 0 and stream.get("duration"):
                    info["duration"] = float(stream["duration"])
            elif stream.get("codec_type") == "audio":
                info["has_audio"] = True
    except Exception as e:
        logger.warning(f"Error getting video info: {e}")
    return info


def _quality_to_crf(quality: int) -> int:
    """Convert quality percentage (1-100) to ffmpeg CRF value (51-0).

    Higher quality = lower CRF.
    quality 100 -> CRF 15 (very high quality)
    quality 75 -> CRF 23 (good quality, balanced)
    quality 50 -> CRF 28 (medium quality, small file)
    quality 25 -> CRF 35 (low quality, very small file)
    quality 1 -> CRF 45 (minimum quality)
    """
    # Linear mapping: quality 100 -> CRF 15, quality 1 -> CRF 45
    crf = int(45 - (quality / 100.0) * 30)
    return max(15, min(45, crf))


def _build_crop_filter(
    src_w: int, src_h: int,
    target_w: int, target_h: int,
    focus_x: float, focus_y: float,
) -> str:
    """Build an ffmpeg crop+scale filter with smart focus-point cropping.

    Instead of letterboxing (black bars), this crops the video around
    the specified focus point to fill the target aspect ratio exactly.
    """
    src_ratio = src_w / src_h if src_h > 0 else 1.0
    target_ratio = target_w / target_h if target_h > 0 else 1.0

    if abs(src_ratio - target_ratio) < 0.01:
        # Same aspect ratio - just scale
        return f"scale={target_w}:{target_h},setsar=1"

    if src_ratio > target_ratio:
        # Source is wider than target - crop width
        # Calculate the width to crop to (maintaining source height)
        crop_w = int(src_h * target_ratio)
        crop_h = src_h

        # Apply focus point for horizontal offset
        max_offset = src_w - crop_w
        offset_x = int((focus_x / 100.0) * max_offset)
        offset_x = max(0, min(offset_x, max_offset))
        offset_y = 0

        return f"crop={crop_w}:{crop_h}:{offset_x}:{offset_y},scale={target_w}:{target_h},setsar=1"
    else:
        # Source is taller than target - crop height
        crop_w = src_w
        crop_h = int(src_w / target_ratio)

        # Apply focus point for vertical offset
        max_offset = src_h - crop_h
        offset_y = int((focus_y / 100.0) * max_offset)
        offset_y = max(0, min(offset_y, max_offset))
        offset_x = 0

        return f"crop={crop_w}:{crop_h}:{offset_x}:{offset_y},scale={target_w}:{target_h},setsar=1"


def _export_video(
    input_path: Path,
    output_path: Path,
    target_w: int,
    target_h: int,
    crf: int,
    focus_x: float,
    focus_y: float,
    max_duration: Optional[float],
    src_info: dict,
) -> tuple[bool, str]:
    """Run ffmpeg to export the video with crop/scale and compression.

    Returns (success, error_message).
    """
    src_w = src_info.get("width", 1920)
    src_h = src_info.get("height", 1080)

    # Build video filter
    vf = _build_crop_filter(src_w, src_h, target_w, target_h, focus_x, focus_y)
    vf += ",format=yuv420p"

    cmd = ["ffmpeg", "-y"]

    # Input
    cmd.extend(["-i", str(input_path)])

    # Duration limit
    if max_duration and src_info.get("duration", 0) > max_duration:
        cmd.extend(["-t", str(max_duration)])

    # Video filter
    cmd.extend(["-vf", vf])

    # Video codec settings (H.264 for maximum compatibility)
    cmd.extend([
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", str(crf),
        "-profile:v", "high",
        "-level", "4.0",
        "-pix_fmt", "yuv420p",
    ])

    # Audio
    if src_info.get("has_audio"):
        cmd.extend(["-c:a", "aac", "-b:a", "128k"])
    else:
        cmd.extend(["-an"])

    # Output optimization
    cmd.extend([
        "-movflags", "+faststart",
        str(output_path),
    ])

    logger.info(f"Running video export: {target_w}x{target_h}, CRF={crf}, focus=({focus_x},{focus_y})")

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if proc.returncode != 0:
            error = proc.stderr[-800:] if proc.stderr else "Unknown ffmpeg error"
            logger.error(f"ffmpeg export failed: {error}")
            return False, error

        if output_path.exists() and output_path.stat().st_size > 0:
            return True, ""
        else:
            return False, "ffmpeg produced empty or missing output file"

    except FileNotFoundError:
        return False, "ffmpeg not found on system"
    except subprocess.TimeoutExpired:
        return False, "Export timed out (>10 min)"
    except Exception as e:
        return False, str(e)


def export_to_dict(export: VideoExport) -> dict:
    """Convert VideoExport model to dict."""
    return {
        "id": export.id,
        "user_id": export.user_id,
        "asset_id": export.asset_id,
        "aspect_ratio": export.aspect_ratio,
        "platform": export.platform,
        "quality": export.quality,
        "max_duration_seconds": export.max_duration_seconds,
        "focus_x": export.focus_x,
        "focus_y": export.focus_y,
        "output_filename": export.output_filename,
        "output_path": export.output_path,
        "output_file_size": export.output_file_size,
        "output_width": export.output_width,
        "output_height": export.output_height,
        "output_duration": export.output_duration,
        "status": export.status,
        "progress": export.progress,
        "error_message": export.error_message,
        "batch_id": export.batch_id,
        "created_at": export.created_at.isoformat() if export.created_at else None,
        "completed_at": export.completed_at.isoformat() if export.completed_at else None,
    }


# ---- API Routes ----

@router.get("/formats")
async def get_export_formats(
    user_id: int = Depends(get_current_user_id),
):
    """Get available export formats and platform presets."""
    return {
        "aspect_ratios": ASPECT_RATIOS,
        "platform_presets": PLATFORM_PRESETS,
    }


@router.post("/analyze")
async def analyze_video_for_export(
    request: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Analyze a video asset and return its properties + export recommendations.

    Returns source dimensions, duration, and recommended export settings
    for each aspect ratio (whether crop or no-crop is needed, preview info).
    """
    asset_id = request.get("asset_id")
    if not asset_id:
        raise HTTPException(status_code=400, detail="asset_id is required")

    result = await db.execute(
        select(Asset).where(Asset.id == asset_id, Asset.user_id == user_id)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if not asset.file_type or not asset.file_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Asset is not a video")

    # Resolve file path
    file_path = _resolve_asset_path(asset)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found on disk")

    info = _get_video_info(file_path)

    # Analyze each aspect ratio
    ratio_analysis = {}
    for key, fmt in ASPECT_RATIOS.items():
        src_ratio = info["width"] / info["height"] if info["height"] > 0 else 1.0
        target_ratio = fmt["width"] / fmt["height"]

        needs_crop = abs(src_ratio - target_ratio) >= 0.01
        crop_direction = None
        crop_percentage = 0

        if needs_crop:
            if src_ratio > target_ratio:
                crop_direction = "horizontal"
                crop_w = int(info["height"] * target_ratio)
                crop_percentage = round((1 - crop_w / info["width"]) * 100, 1)
            else:
                crop_direction = "vertical"
                crop_h = int(info["width"] / target_ratio)
                crop_percentage = round((1 - crop_h / info["height"]) * 100, 1)

        ratio_analysis[key] = {
            "label": fmt["label"],
            "output_width": fmt["width"],
            "output_height": fmt["height"],
            "needs_crop": needs_crop,
            "crop_direction": crop_direction,
            "crop_percentage": crop_percentage,
        }

    # Platform compatibility
    platform_compat = {}
    for key, preset in PLATFORM_PRESETS.items():
        duration_ok = info["duration"] <= preset["max_duration"]
        platform_compat[key] = {
            "label": preset["label"],
            "aspect_ratio": preset["aspect_ratio"],
            "max_duration": preset["max_duration"],
            "duration_ok": duration_ok,
            "duration_over_by": round(max(0, info["duration"] - preset["max_duration"]), 1),
            "recommended_quality": preset["recommended_quality"],
        }

    return {
        "asset_id": asset.id,
        "filename": asset.original_filename or asset.filename,
        "file_path": asset.file_path,
        "thumbnail_path": asset.thumbnail_path,
        "source_width": info["width"],
        "source_height": info["height"],
        "source_duration": round(info["duration"], 2),
        "source_codec": info["codec"],
        "has_audio": info["has_audio"],
        "file_size": asset.file_size,
        "aspect_ratios": ratio_analysis,
        "platform_compatibility": platform_compat,
    }


def _resolve_asset_path(asset: Asset) -> Optional[Path]:
    """Resolve the actual file path of an asset."""
    # Try assets directory first
    path = ASSETS_DIR / asset.filename
    if path.exists():
        return path

    # Try composed directory
    path = COMPOSED_DIR / asset.filename
    if path.exists():
        return path

    # Try file_path relative to static
    if asset.file_path:
        path = APP_DIR / "static" / asset.file_path.lstrip("/")
        if path.exists():
            return path

    return None


@router.post("")
async def export_video(
    request: VideoExportRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Export a video asset in the specified format.

    Applies smart cropping (based on focus point), compression,
    and platform-specific settings. Returns the export result
    with download path.
    """
    if not FFMPEG_AVAILABLE:
        raise HTTPException(status_code=501, detail="Video-Export ist auf diesem Server nicht verfuegbar (ffmpeg fehlt).")

    # Validate aspect ratio
    if request.aspect_ratio not in ASPECT_RATIOS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid aspect_ratio. Choose from: {list(ASPECT_RATIOS.keys())}",
        )

    # Validate platform
    if request.platform not in PLATFORM_PRESETS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid platform. Choose from: {list(PLATFORM_PRESETS.keys())}",
        )

    # Fetch asset
    result = await db.execute(
        select(Asset).where(Asset.id == request.asset_id, Asset.user_id == user_id)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if not asset.file_type or not asset.file_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Asset is not a video")

    # Resolve file path
    file_path = _resolve_asset_path(asset)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found on disk")

    # Get source video info
    src_info = _get_video_info(file_path)

    # Platform settings
    preset = PLATFORM_PRESETS[request.platform]
    max_duration = request.max_duration or preset["max_duration"]

    # Target dimensions
    fmt = ASPECT_RATIOS[request.aspect_ratio]
    target_w = fmt["width"]
    target_h = fmt["height"]

    # Quality -> CRF
    crf = _quality_to_crf(request.quality)

    # Create export record
    export_record = VideoExport(
        user_id=user_id,
        asset_id=request.asset_id,
        aspect_ratio=request.aspect_ratio,
        platform=request.platform,
        quality=request.quality,
        max_duration_seconds=max_duration,
        focus_x=request.focus_x,
        focus_y=request.focus_y,
        status="processing",
        progress=10,
    )
    db.add(export_record)
    await db.flush()
    await db.refresh(export_record)

    # Generate output filename
    output_filename = f"export_{export_record.id}_{request.aspect_ratio.replace(':', 'x')}_{uuid.uuid4().hex[:6]}.mp4"
    output_path = VIDEO_EXPORTS_DIR / output_filename

    # Run ffmpeg export
    export_record.progress = 30
    await db.flush()

    success, error_msg = _export_video(
        input_path=file_path,
        output_path=output_path,
        target_w=target_w,
        target_h=target_h,
        crf=crf,
        focus_x=request.focus_x,
        focus_y=request.focus_y,
        max_duration=max_duration,
        src_info=src_info,
    )

    if success:
        # Get output file info
        file_size = output_path.stat().st_size
        out_info = _get_video_info(output_path)

        export_record.status = "done"
        export_record.progress = 100
        export_record.output_filename = output_filename
        export_record.output_path = f"/uploads/video_exports/{output_filename}"
        export_record.output_file_size = file_size
        export_record.output_width = out_info.get("width") or target_w
        export_record.output_height = out_info.get("height") or target_h
        export_record.output_duration = round(out_info.get("duration", 0), 2)
        export_record.completed_at = datetime.now(timezone.utc)
    else:
        export_record.status = "error"
        export_record.progress = 0
        export_record.error_message = error_msg
        # Clean up failed output
        if output_path.exists():
            try:
                os.remove(output_path)
            except OSError:
                pass

    await db.flush()
    await db.refresh(export_record)
    result_dict = export_to_dict(export_record)
    await db.commit()

    if not success:
        raise HTTPException(status_code=500, detail=f"Export failed: {error_msg}")

    return result_dict


@router.post("/batch")
async def batch_export_video(
    request: BatchExportRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Export a video in multiple formats at once.

    Creates separate export jobs for each format and processes them sequentially.
    Returns all results together.
    """
    if not FFMPEG_AVAILABLE:
        raise HTTPException(status_code=501, detail="Video-Export ist auf diesem Server nicht verfuegbar (ffmpeg fehlt).")

    # Validate asset
    result = await db.execute(
        select(Asset).where(Asset.id == request.asset_id, Asset.user_id == user_id)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if not asset.file_type or not asset.file_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Asset is not a video")

    file_path = _resolve_asset_path(asset)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found on disk")

    src_info = _get_video_info(file_path)
    batch_id = str(uuid.uuid4())[:8]

    results = []
    for fmt_spec in request.formats:
        aspect_ratio = fmt_spec.get("aspect_ratio", "9:16")
        platform = fmt_spec.get("platform", "instagram_reel")
        quality = fmt_spec.get("quality", 75)
        focus_x = fmt_spec.get("focus_x", 50.0)
        focus_y = fmt_spec.get("focus_y", 50.0)

        if aspect_ratio not in ASPECT_RATIOS:
            results.append({"aspect_ratio": aspect_ratio, "status": "error", "error": f"Invalid aspect ratio: {aspect_ratio}"})
            continue

        if platform not in PLATFORM_PRESETS:
            results.append({"aspect_ratio": aspect_ratio, "status": "error", "error": f"Invalid platform: {platform}"})
            continue

        preset = PLATFORM_PRESETS[platform]
        max_duration = preset["max_duration"]
        fmt = ASPECT_RATIOS[aspect_ratio]
        target_w = fmt["width"]
        target_h = fmt["height"]
        crf = _quality_to_crf(quality)

        # Create export record
        export_record = VideoExport(
            user_id=user_id,
            asset_id=request.asset_id,
            aspect_ratio=aspect_ratio,
            platform=platform,
            quality=quality,
            max_duration_seconds=max_duration,
            focus_x=focus_x,
            focus_y=focus_y,
            status="processing",
            progress=10,
            batch_id=batch_id,
        )
        db.add(export_record)
        await db.flush()
        await db.refresh(export_record)

        output_filename = f"export_{export_record.id}_{aspect_ratio.replace(':', 'x')}_{uuid.uuid4().hex[:6]}.mp4"
        output_path_file = VIDEO_EXPORTS_DIR / output_filename

        success, error_msg = _export_video(
            input_path=file_path,
            output_path=output_path_file,
            target_w=target_w,
            target_h=target_h,
            crf=crf,
            focus_x=focus_x,
            focus_y=focus_y,
            max_duration=max_duration,
            src_info=src_info,
        )

        if success:
            file_size = output_path_file.stat().st_size
            out_info = _get_video_info(output_path_file)

            export_record.status = "done"
            export_record.progress = 100
            export_record.output_filename = output_filename
            export_record.output_path = f"/uploads/video_exports/{output_filename}"
            export_record.output_file_size = file_size
            export_record.output_width = out_info.get("width") or target_w
            export_record.output_height = out_info.get("height") or target_h
            export_record.output_duration = round(out_info.get("duration", 0), 2)
            export_record.completed_at = datetime.now(timezone.utc)
        else:
            export_record.status = "error"
            export_record.progress = 0
            export_record.error_message = error_msg
            if output_path_file.exists():
                try:
                    os.remove(output_path_file)
                except OSError:
                    pass

        await db.flush()
        await db.refresh(export_record)
        results.append(export_to_dict(export_record))

    await db.commit()

    return {
        "batch_id": batch_id,
        "asset_id": request.asset_id,
        "exports": results,
        "total": len(results),
        "successful": sum(1 for r in results if isinstance(r, dict) and r.get("status") == "done"),
        "failed": sum(1 for r in results if isinstance(r, dict) and r.get("status") in ("error",)),
    }


@router.get("/{export_id}")
async def get_export(
    export_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get details of a specific video export."""
    result = await db.execute(
        select(VideoExport).where(
            VideoExport.id == export_id,
            VideoExport.user_id == user_id,
        )
    )
    export = result.scalar_one_or_none()
    if not export:
        raise HTTPException(status_code=404, detail="Export not found")
    return export_to_dict(export)


@router.get("/{export_id}/download")
async def download_export(
    export_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Download an exported video file."""
    result = await db.execute(
        select(VideoExport).where(
            VideoExport.id == export_id,
            VideoExport.user_id == user_id,
        )
    )
    export = result.scalar_one_or_none()
    if not export:
        raise HTTPException(status_code=404, detail="Export not found")

    if export.status != "done" or not export.output_path:
        raise HTTPException(status_code=400, detail="Export not ready for download")

    file_path = APP_DIR / "static" / export.output_path.lstrip("/")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Export file not found on disk")

    download_name = f"treff_video_{export.aspect_ratio.replace(':', 'x')}_{export.platform}.mp4"
    return FileResponse(
        path=str(file_path),
        filename=download_name,
        media_type="video/mp4",
    )


@router.get("")
async def list_exports(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    asset_id: Optional[int] = None,
):
    """List video exports, optionally filtered by asset_id."""
    query = (
        select(VideoExport)
        .where(VideoExport.user_id == user_id)
        .order_by(VideoExport.created_at.desc())
    )
    if asset_id:
        query = query.where(VideoExport.asset_id == asset_id)

    result = await db.execute(query)
    exports = result.scalars().all()
    return [export_to_dict(e) for e in exports]


@router.delete("/{export_id}")
async def delete_export(
    export_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete an export and its file."""
    result = await db.execute(
        select(VideoExport).where(
            VideoExport.id == export_id,
            VideoExport.user_id == user_id,
        )
    )
    export = result.scalar_one_or_none()
    if not export:
        raise HTTPException(status_code=404, detail="Export not found")

    # Delete file
    if export.output_path:
        file_path = APP_DIR / "static" / export.output_path.lstrip("/")
        if file_path.exists():
            try:
                os.remove(file_path)
            except OSError:
                pass

    await db.delete(export)
    await db.commit()
    return {"status": "deleted", "id": export_id}
