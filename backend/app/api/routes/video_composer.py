"""Video Composer routes - Multi-clip editing and composition via ffmpeg."""

import json
import logging
import os
import subprocess
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.asset import Asset

logger = logging.getLogger(__name__)

router = APIRouter()

# Resolve paths
APP_DIR = Path(__file__).resolve().parent.parent.parent
ASSETS_UPLOAD_DIR = APP_DIR / "static" / "uploads" / "assets"
THUMBNAILS_DIR = APP_DIR / "static" / "uploads" / "thumbnails"
COMPOSED_DIR = APP_DIR / "static" / "uploads" / "composed"
COMPOSED_DIR.mkdir(parents=True, exist_ok=True)

# Transition types
TRANSITION_TYPES = ["cut", "fade", "crossdissolve"]

# Output format presets
OUTPUT_FORMATS = {
    "9:16": {"width": 1080, "height": 1920, "label": "Reel/TikTok (9:16)"},
    "1:1": {"width": 1080, "height": 1080, "label": "Feed (1:1)"},
    "16:9": {"width": 1920, "height": 1080, "label": "Landscape (16:9)"},
}


class ClipItem(BaseModel):
    """A single clip in the composition."""
    asset_id: int
    trim_start: float = 0.0  # seconds
    trim_end: Optional[float] = None  # None means full clip
    transition: str = "cut"  # cut, fade, crossdissolve
    transition_duration: float = 0.5  # seconds


class ComposeRequest(BaseModel):
    """Request to compose multiple clips into one video."""
    clips: list[ClipItem] = Field(..., min_length=1)
    output_format: str = "9:16"  # 9:16, 1:1, 16:9
    save_as_asset: bool = True


class ComposePreviewRequest(BaseModel):
    """Request for preview metadata about a composition."""
    clips: list[ClipItem] = Field(..., min_length=1)
    output_format: str = "9:16"


def _extract_video_metadata(video_path: Path) -> dict:
    """Extract video metadata using ffprobe."""
    metadata = {"duration_seconds": None, "width": None, "height": None}
    try:
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", str(video_path),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if proc.returncode != 0:
            return metadata
        data = json.loads(proc.stdout)
        fmt = data.get("format", {})
        if fmt.get("duration"):
            metadata["duration_seconds"] = round(float(fmt["duration"]), 2)
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                if stream.get("width"):
                    metadata["width"] = int(stream["width"])
                if stream.get("height"):
                    metadata["height"] = int(stream["height"])
                if metadata["duration_seconds"] is None and stream.get("duration"):
                    metadata["duration_seconds"] = round(float(stream["duration"]), 2)
                break
    except Exception as e:
        logger.warning(f"Error extracting metadata: {e}")
    return metadata


def _generate_thumbnail(video_path: Path, thumbnail_filename: str) -> Optional[str]:
    """Generate thumbnail from first frame."""
    thumbnail_path = THUMBNAILS_DIR / thumbnail_filename
    try:
        cmd = [
            "ffmpeg", "-i", str(video_path),
            "-vf", "thumbnail,scale=480:-1",
            "-frames:v", "1", "-y", str(thumbnail_path),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if proc.returncode == 0 and thumbnail_path.exists() and thumbnail_path.stat().st_size > 0:
            return f"/uploads/thumbnails/{thumbnail_filename}"
    except Exception as e:
        logger.warning(f"Thumbnail generation failed: {e}")
    return None


@router.get("/formats")
async def get_output_formats(
    user_id: int = Depends(get_current_user_id),
):
    """Get available output format presets."""
    return {
        "formats": OUTPUT_FORMATS,
        "transitions": TRANSITION_TYPES,
    }


@router.post("/preview")
async def preview_composition(
    request: ComposePreviewRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get preview metadata for a composition without rendering.

    Returns estimated duration, clip details, and validation info.
    """
    if not request.clips:
        raise HTTPException(status_code=400, detail="At least one clip is required")

    if request.output_format not in OUTPUT_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid output_format. Choose from: {list(OUTPUT_FORMATS.keys())}",
        )

    clip_details = []
    total_duration = 0.0
    total_transition_time = 0.0

    for i, clip in enumerate(request.clips):
        # Fetch asset
        result = await db.execute(
            select(Asset).where(Asset.id == clip.asset_id, Asset.user_id == user_id)
        )
        asset = result.scalar_one_or_none()
        if not asset:
            raise HTTPException(status_code=404, detail=f"Asset {clip.asset_id} not found")

        if not asset.file_type or not asset.file_type.startswith("video/"):
            raise HTTPException(
                status_code=400, detail=f"Asset {clip.asset_id} is not a video"
            )

        # Calculate clip duration
        asset_duration = asset.duration_seconds or 0
        effective_start = clip.trim_start
        effective_end = clip.trim_end if clip.trim_end is not None else asset_duration
        clip_duration = max(0, effective_end - effective_start)

        # Transition time (between clips, not on first clip)
        trans_time = 0.0
        if i > 0 and clip.transition in ("fade", "crossdissolve"):
            trans_time = clip.transition_duration
            total_transition_time += trans_time

        total_duration += clip_duration

        clip_details.append({
            "index": i,
            "asset_id": asset.id,
            "filename": asset.original_filename or asset.filename,
            "file_path": asset.file_path,
            "thumbnail_path": asset.thumbnail_path,
            "asset_duration": asset_duration,
            "trim_start": effective_start,
            "trim_end": effective_end,
            "clip_duration": round(clip_duration, 2),
            "transition": clip.transition if i > 0 else "none",
            "transition_duration": trans_time,
            "width": asset.width,
            "height": asset.height,
        })

    # Total duration accounts for transition overlaps
    effective_total = max(0, total_duration - total_transition_time)
    fmt = OUTPUT_FORMATS[request.output_format]

    return {
        "clips": clip_details,
        "clip_count": len(clip_details),
        "total_duration": round(total_duration, 2),
        "transition_overlap": round(total_transition_time, 2),
        "effective_duration": round(effective_total, 2),
        "output_format": request.output_format,
        "output_width": fmt["width"],
        "output_height": fmt["height"],
        "output_label": fmt["label"],
    }


@router.post("/compose")
async def compose_video(
    request: ComposeRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Compose multiple video clips into a single video.

    Supports transitions (cut, fade, crossdissolve) and output format presets.
    Uses ffmpeg for all video processing.
    """
    if not request.clips:
        raise HTTPException(status_code=400, detail="At least one clip is required")

    if len(request.clips) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 clips allowed")

    if request.output_format not in OUTPUT_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid output_format. Choose from: {list(OUTPUT_FORMATS.keys())}",
        )

    fmt = OUTPUT_FORMATS[request.output_format]
    target_w = fmt["width"]
    target_h = fmt["height"]

    # Resolve all clips to file paths
    clip_paths = []
    for i, clip in enumerate(request.clips):
        if clip.transition not in TRANSITION_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Clip {i}: invalid transition '{clip.transition}'. Use: {TRANSITION_TYPES}",
            )

        result = await db.execute(
            select(Asset).where(Asset.id == clip.asset_id, Asset.user_id == user_id)
        )
        asset = result.scalar_one_or_none()
        if not asset:
            raise HTTPException(status_code=404, detail=f"Asset {clip.asset_id} not found")

        if not asset.file_type or not asset.file_type.startswith("video/"):
            raise HTTPException(
                status_code=400, detail=f"Asset {clip.asset_id} is not a video"
            )

        file_path = ASSETS_UPLOAD_DIR / asset.filename
        if not file_path.exists():
            raise HTTPException(
                status_code=404, detail=f"Video file for asset {clip.asset_id} not found on disk"
            )

        clip_paths.append({
            "path": file_path,
            "asset": asset,
            "clip": clip,
            "index": i,
        })

    # Generate output filename
    output_filename = f"composed_{uuid.uuid4()}.mp4"
    output_path = COMPOSED_DIR / output_filename

    try:
        # Build the ffmpeg command based on number of clips and transitions
        if len(clip_paths) == 1:
            # Single clip - just scale/pad to target format
            _compose_single_clip(clip_paths[0], target_w, target_h, output_path)
        else:
            # Multiple clips with transitions
            _compose_multiple_clips(clip_paths, target_w, target_h, output_path)

    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="ffmpeg not found on system - video composition unavailable",
        )
    except subprocess.TimeoutExpired:
        if output_path.exists():
            output_path.unlink()
        raise HTTPException(status_code=504, detail="Video composition timed out")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video composition failed: {e}")
        if output_path.exists():
            output_path.unlink()
        raise HTTPException(status_code=500, detail=f"Video composition failed: {str(e)}")

    # Verify output
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise HTTPException(status_code=500, detail="Composed video is empty or missing")

    # Extract metadata from composed video
    meta = _extract_video_metadata(output_path)
    file_size = output_path.stat().st_size

    # Generate thumbnail
    thumb_filename = f"{uuid.uuid4()}.jpg"
    thumbnail_path = _generate_thumbnail(output_path, thumb_filename)

    result_data = {
        "filename": output_filename,
        "file_path": f"/uploads/composed/{output_filename}",
        "file_size": file_size,
        "duration_seconds": meta["duration_seconds"],
        "width": meta["width"] or target_w,
        "height": meta["height"] or target_h,
        "thumbnail_path": thumbnail_path,
        "output_format": request.output_format,
        "clip_count": len(clip_paths),
    }

    # Optionally save as a new asset
    if request.save_as_asset:
        new_asset = Asset(
            user_id=user_id,
            filename=output_filename,
            original_filename=f"composed_{len(clip_paths)}_clips.mp4",
            file_path=f"/uploads/composed/{output_filename}",
            file_type="video/mp4",
            file_size=file_size,
            width=meta["width"] or target_w,
            height=meta["height"] or target_h,
            source="composed",
            category="video",
            tags=f"composed,{len(clip_paths)} clips,{request.output_format}",
            duration_seconds=meta["duration_seconds"],
            thumbnail_path=thumbnail_path,
        )
        db.add(new_asset)
        await db.flush()
        await db.refresh(new_asset)
        result_data["asset_id"] = new_asset.id
        result_data["asset"] = {
            "id": new_asset.id,
            "filename": new_asset.filename,
            "original_filename": new_asset.original_filename,
            "file_path": new_asset.file_path,
            "file_type": new_asset.file_type,
            "file_size": new_asset.file_size,
            "width": new_asset.width,
            "height": new_asset.height,
            "duration_seconds": new_asset.duration_seconds,
            "thumbnail_path": new_asset.thumbnail_path,
        }

    return result_data


def _compose_single_clip(clip_info: dict, target_w: int, target_h: int, output_path: Path):
    """Compose a single clip with scaling/padding."""
    clip = clip_info["clip"]
    path = clip_info["path"]

    cmd = ["ffmpeg", "-i", str(path)]

    # Trim parameters
    if clip.trim_start > 0:
        cmd.extend(["-ss", str(clip.trim_start)])
    if clip.trim_end is not None:
        cmd.extend(["-to", str(clip.trim_end)])

    # Scale and pad to target dimensions (letterbox/pillarbox with black bars)
    vf = f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:black,setsar=1"
    cmd.extend([
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-profile:v", "high", "-level", "4.0",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        "-y", str(output_path),
    ])

    logger.info(f"Running single-clip compose: {' '.join(cmd[:6])}...")
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if proc.returncode != 0:
        logger.error(f"ffmpeg single-clip compose failed: {proc.stderr[:1000]}")
        raise HTTPException(status_code=500, detail="Video composition failed (single clip)")


def _compose_multiple_clips(clip_infos: list, target_w: int, target_h: int, output_path: Path):
    """Compose multiple clips with transitions using ffmpeg complex filter graph."""
    # Check if we have any transitions that need xfade (fade or crossdissolve)
    has_transitions = any(
        ci["clip"].transition in ("fade", "crossdissolve") and ci["index"] > 0
        for ci in clip_infos
    )

    if not has_transitions:
        # Simple concat without transitions - faster
        _compose_concat_only(clip_infos, target_w, target_h, output_path)
    else:
        # Complex filter with xfade transitions
        _compose_with_transitions(clip_infos, target_w, target_h, output_path)


def _compose_concat_only(clip_infos: list, target_w: int, target_h: int, output_path: Path):
    """Compose clips by simple concatenation (cut transitions only)."""
    # Build filter complex: scale each input, then concat
    cmd = ["ffmpeg"]
    filter_parts = []

    for i, ci in enumerate(clip_infos):
        clip = ci["clip"]
        path = ci["path"]

        # Input with optional trim
        if clip.trim_start > 0 or clip.trim_end is not None:
            cmd.extend(["-ss", str(clip.trim_start)])
            if clip.trim_end is not None:
                cmd.extend(["-to", str(clip.trim_end)])
        cmd.extend(["-i", str(path)])

        # Scale/pad each input to target dimensions
        scale_filter = (
            f"[{i}:v]scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,"
            f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:black,setsar=1,"
            f"fps=30,format=yuv420p[v{i}]"
        )
        filter_parts.append(scale_filter)

        # Audio - ensure same format
        filter_parts.append(f"[{i}:a]aresample=44100,aformat=sample_fmts=fltp:channel_layouts=stereo[a{i}]")

    # Concat
    n = len(clip_infos)
    video_inputs = "".join(f"[v{i}]" for i in range(n))
    audio_inputs = "".join(f"[a{i}]" for i in range(n))
    filter_parts.append(f"{video_inputs}{audio_inputs}concat=n={n}:v=1:a=1[outv][outa]")

    filter_complex = ";".join(filter_parts)
    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", "[outv]", "-map", "[outa]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-profile:v", "high", "-level", "4.0",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        "-y", str(output_path),
    ])

    logger.info(f"Running concat compose with {n} clips...")
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        logger.error(f"ffmpeg concat failed: {proc.stderr[:2000]}")
        # Fallback: try without audio
        _compose_concat_video_only(clip_infos, target_w, target_h, output_path)


def _compose_concat_video_only(clip_infos: list, target_w: int, target_h: int, output_path: Path):
    """Fallback: concat video only (no audio) when audio stream concat fails."""
    cmd = ["ffmpeg"]
    filter_parts = []

    for i, ci in enumerate(clip_infos):
        clip = ci["clip"]
        path = ci["path"]
        if clip.trim_start > 0 or clip.trim_end is not None:
            cmd.extend(["-ss", str(clip.trim_start)])
            if clip.trim_end is not None:
                cmd.extend(["-to", str(clip.trim_end)])
        cmd.extend(["-i", str(path)])
        scale_filter = (
            f"[{i}:v]scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,"
            f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:black,setsar=1,"
            f"fps=30,format=yuv420p[v{i}]"
        )
        filter_parts.append(scale_filter)

    n = len(clip_infos)
    video_inputs = "".join(f"[v{i}]" for i in range(n))
    filter_parts.append(f"{video_inputs}concat=n={n}:v=1:a=0[outv]")

    filter_complex = ";".join(filter_parts)
    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-profile:v", "high", "-level", "4.0",
        "-movflags", "+faststart",
        "-an",
        "-y", str(output_path),
    ])

    logger.info(f"Running video-only concat compose with {n} clips...")
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        logger.error(f"ffmpeg video-only concat failed: {proc.stderr[:2000]}")
        raise HTTPException(status_code=500, detail="Video composition failed")


def _compose_with_transitions(clip_infos: list, target_w: int, target_h: int, output_path: Path):
    """Compose clips with xfade transitions between them."""
    n = len(clip_infos)
    cmd = ["ffmpeg"]
    filter_parts = []

    # First, we need clip durations for offset calculation
    clip_durations = []
    for i, ci in enumerate(clip_infos):
        clip = ci["clip"]
        path = ci["path"]
        asset = ci["asset"]

        if clip.trim_start > 0 or clip.trim_end is not None:
            cmd.extend(["-ss", str(clip.trim_start)])
            if clip.trim_end is not None:
                cmd.extend(["-to", str(clip.trim_end)])
        cmd.extend(["-i", str(path)])

        # Calculate duration
        asset_dur = asset.duration_seconds or 10
        effective_end = clip.trim_end if clip.trim_end is not None else asset_dur
        dur = max(0.5, effective_end - clip.trim_start)
        clip_durations.append(dur)

        # Scale/pad each input
        scale_filter = (
            f"[{i}:v]scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,"
            f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:black,setsar=1,"
            f"fps=30,format=yuv420p[v{i}]"
        )
        filter_parts.append(scale_filter)

    # Build xfade chain
    # For each pair of consecutive clips, apply xfade
    # Track cumulative offset for each transition
    current_label = "v0"
    cumulative_offset = 0.0

    for i in range(1, n):
        clip = clip_infos[i]["clip"]
        trans_type = clip.transition
        trans_dur = clip.transition_duration

        # Ensure transition duration doesn't exceed clip duration
        trans_dur = min(trans_dur, clip_durations[i - 1] - 0.1, clip_durations[i] - 0.1)
        trans_dur = max(0.1, trans_dur)

        # Offset = cumulative duration of previous segments minus transition overlaps
        if i == 1:
            offset = clip_durations[0] - trans_dur
        else:
            offset = cumulative_offset + clip_durations[i - 1] - trans_dur

        # Ensure offset is non-negative
        offset = max(0, offset)

        # Map transition type to ffmpeg xfade name
        if trans_type == "fade":
            xfade_transition = "fade"
        elif trans_type == "crossdissolve":
            xfade_transition = "dissolve"
        else:
            xfade_transition = "fade"  # fallback

        out_label = f"xf{i}"
        if i < n - 1:
            filter_parts.append(
                f"[{current_label}][v{i}]xfade=transition={xfade_transition}:duration={trans_dur:.2f}:offset={offset:.2f}[{out_label}]"
            )
            current_label = out_label
        else:
            # Last transition outputs to [outv] with browser-compatible pixel format
            filter_parts.append(
                f"[{current_label}][v{i}]xfade=transition={xfade_transition}:duration={trans_dur:.2f}:offset={offset:.2f},format=yuv420p[outv]"
            )

        cumulative_offset = offset

    # Audio: simple concat (no audio crossfade for simplicity)
    has_audio = True
    for i in range(n):
        filter_parts.append(f"[{i}:a]aresample=44100,aformat=sample_fmts=fltp:channel_layouts=stereo[a{i}]")
    audio_inputs = "".join(f"[a{i}]" for i in range(n))
    filter_parts.append(f"{audio_inputs}concat=n={n}:v=0:a=1[outa]")

    filter_complex = ";".join(filter_parts)
    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", "[outv]", "-map", "[outa]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-profile:v", "high", "-level", "4.0",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        "-y", str(output_path),
    ])

    logger.info(f"Running xfade compose with {n} clips...")
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        logger.error(f"ffmpeg xfade failed: {proc.stderr[:2000]}")
        # Fallback: try without audio
        _compose_with_transitions_video_only(clip_infos, clip_durations, target_w, target_h, output_path)


def _compose_with_transitions_video_only(
    clip_infos: list, clip_durations: list,
    target_w: int, target_h: int, output_path: Path
):
    """Fallback: xfade transitions without audio."""
    n = len(clip_infos)
    cmd = ["ffmpeg"]
    filter_parts = []

    for i, ci in enumerate(clip_infos):
        clip = ci["clip"]
        path = ci["path"]
        if clip.trim_start > 0 or clip.trim_end is not None:
            cmd.extend(["-ss", str(clip.trim_start)])
            if clip.trim_end is not None:
                cmd.extend(["-to", str(clip.trim_end)])
        cmd.extend(["-i", str(path)])
        scale_filter = (
            f"[{i}:v]scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,"
            f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:black,setsar=1,"
            f"fps=30,format=yuv420p[v{i}]"
        )
        filter_parts.append(scale_filter)

    current_label = "v0"
    cumulative_offset = 0.0

    for i in range(1, n):
        clip = clip_infos[i]["clip"]
        trans_type = clip.transition
        trans_dur = min(clip.transition_duration, clip_durations[i - 1] - 0.1, clip_durations[i] - 0.1)
        trans_dur = max(0.1, trans_dur)

        if i == 1:
            offset = clip_durations[0] - trans_dur
        else:
            offset = cumulative_offset + clip_durations[i - 1] - trans_dur
        offset = max(0, offset)

        if trans_type == "fade":
            xfade_transition = "fade"
        elif trans_type == "crossdissolve":
            xfade_transition = "dissolve"
        else:
            xfade_transition = "fade"

        if i < n - 1:
            out_label = f"xf{i}"
            filter_parts.append(
                f"[{current_label}][v{i}]xfade=transition={xfade_transition}:duration={trans_dur:.2f}:offset={offset:.2f}[{out_label}]"
            )
            current_label = out_label
        else:
            # Last transition outputs to [outv] with browser-compatible pixel format
            filter_parts.append(
                f"[{current_label}][v{i}]xfade=transition={xfade_transition}:duration={trans_dur:.2f}:offset={offset:.2f},format=yuv420p[outv]"
            )

        cumulative_offset = offset

    filter_complex = ";".join(filter_parts)
    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-profile:v", "high", "-level", "4.0",
        "-movflags", "+faststart",
        "-an",
        "-y", str(output_path),
    ])

    logger.info(f"Running video-only xfade compose with {n} clips...")
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        logger.error(f"ffmpeg video-only xfade failed: {proc.stderr[:2000]}")
        # Final fallback: simple concat without transitions
        _compose_concat_video_only(clip_infos, target_w, target_h, output_path)
