"""Video overlay routes - CRUD and ffmpeg rendering for video overlays."""

import json
import logging
import os
import shutil
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
from app.core.paths import get_upload_dir
from app.models.video_overlay import VideoOverlay
from app.models.asset import Asset

logger = logging.getLogger(__name__)

router = APIRouter()

EXPORTS_DIR = get_upload_dir("exports")
ASSETS_DIR = get_upload_dir("assets")

FFMPEG_AVAILABLE = shutil.which("ffmpeg") is not None


# ---------- Pydantic schemas ----------

class OverlayLayer(BaseModel):
    type: str = "text"  # text, logo, subtitle, hashtag
    text: str = ""
    x: float = 50  # percentage position (0-100)
    y: float = 50
    width: float = 80  # percentage of video width
    height: float = 10  # percentage of video height
    fontSize: int = 32
    fontFamily: str = "Inter"
    color: str = "#FFFFFF"
    bgColor: str = "rgba(0,0,0,0.6)"
    opacity: float = 1.0
    startTime: float = 0.0  # seconds
    endTime: float = -1  # -1 means until end of video
    animation: str = "none"  # none, fade_in, slide_in_left, slide_in_bottom, pop_in
    bold: bool = False
    italic: bool = False
    textAlign: str = "center"  # left, center, right


class VideoOverlayCreate(BaseModel):
    asset_id: int
    name: str = "Unbenanntes Overlay"
    layers: list[OverlayLayer] = []


class VideoOverlayUpdate(BaseModel):
    name: Optional[str] = None
    layers: Optional[list[OverlayLayer]] = None


# ---------- Helpers ----------

def overlay_to_dict(overlay: VideoOverlay) -> dict:
    """Convert VideoOverlay model to dict."""
    layers = []
    if overlay.layers:
        try:
            layers = json.loads(overlay.layers)
        except (json.JSONDecodeError, TypeError):
            layers = []

    return {
        "id": overlay.id,
        "user_id": overlay.user_id,
        "asset_id": overlay.asset_id,
        "name": overlay.name,
        "layers": layers,
        "rendered_path": overlay.rendered_path,
        "render_status": overlay.render_status,
        "render_error": overlay.render_error,
        "created_at": overlay.created_at.isoformat() if overlay.created_at else None,
        "updated_at": overlay.updated_at.isoformat() if overlay.updated_at else None,
    }


def _get_video_dimensions(video_path: Path) -> tuple[int, int]:
    """Get video dimensions using ffprobe. Returns (width, height) or (1080, 1920) as default."""
    try:
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_streams",
            str(video_path),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if proc.returncode == 0:
            data = json.loads(proc.stdout)
            for stream in data.get("streams", []):
                if stream.get("codec_type") == "video":
                    return int(stream.get("width", 1080)), int(stream.get("height", 1920))
    except Exception as e:
        logger.warning(f"Failed to get video dimensions: {e}")
    return 1080, 1920


def _parse_css_color(color_str: str) -> tuple:
    """Parse a CSS color (hex or rgba) into an RGBA tuple (0-255 each)."""
    if not color_str or color_str in ("transparent", "none"):
        return (0, 0, 0, 0)

    if color_str.startswith("rgba("):
        try:
            inner = color_str[5:-1]
            parts = [p.strip() for p in inner.split(",")]
            r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
            a = int(float(parts[3]) * 255)
            return (r, g, b, a)
        except (ValueError, IndexError):
            return (0, 0, 0, 153)

    if color_str.startswith("#"):
        h = color_str.lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        if len(h) == 6:
            return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)

    return (255, 255, 255, 255)


def _render_overlay_image(layers: list[dict], video_width: int, video_height: int) -> Path:
    """Render all overlay layers to a single transparent PNG image using Pillow.

    This creates a static overlay image containing all text, logos, and branding
    that will be composited onto the video using ffmpeg's overlay filter.
    Returns the path to the generated PNG.
    """
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGBA", (video_width, video_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    for layer in layers:
        text = layer.get("text", "")
        if not text:
            continue

        x_pct = layer.get("x", 50) / 100.0
        y_pct = layer.get("y", 50) / 100.0
        w_pct = layer.get("width", 80) / 100.0
        h_pct = layer.get("height", 10) / 100.0
        font_size = layer.get("fontSize", 32)
        opacity = layer.get("opacity", 1.0)

        x = int(x_pct * video_width)
        y = int(y_pct * video_height)
        w = int(w_pct * video_width)
        h = int(h_pct * video_height)

        # Background
        bg_color = _parse_css_color(layer.get("bgColor", ""))
        if bg_color[3] > 0:
            # Apply layer opacity to bg alpha
            bg_with_opacity = (bg_color[0], bg_color[1], bg_color[2], int(bg_color[3] * opacity))
            draw.rounded_rectangle([x, y, x + w, y + h], radius=4, fill=bg_with_opacity)

        # Text color
        fg = _parse_css_color(layer.get("color", "#FFFFFF"))
        fg_with_opacity = (fg[0], fg[1], fg[2], int(fg[3] * opacity))

        # Font
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        except (OSError, IOError):
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
            except (OSError, IOError):
                font = ImageFont.load_default()

        # Text alignment
        align = layer.get("textAlign", "left")
        padding = 8

        # Draw text with alignment
        text_x = x + padding
        if align == "center":
            bbox = draw.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]
            text_x = x + (w - text_w) // 2
        elif align == "right":
            bbox = draw.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]
            text_x = x + w - text_w - padding

        text_y = y + padding

        draw.text((text_x, text_y), text, fill=fg_with_opacity, font=font)

    overlay_path = EXPORTS_DIR / f"_overlay_{uuid.uuid4().hex[:8]}.png"
    img.save(str(overlay_path), "PNG")
    return overlay_path


def _render_video_with_overlays(video_path: Path, layers: list[dict], output_path: Path) -> tuple[bool, str]:
    """Render video with text overlays using Pillow (image) + ffmpeg overlay filter.

    Strategy: Render all text layers to a transparent PNG using Pillow,
    then use ffmpeg's overlay filter to composite it on top of the video.
    Time-based visibility is handled with the enable='between(t,start,end)' option.

    Returns (success: bool, error_message: str).
    """
    video_width, video_height = _get_video_dimensions(video_path)

    # Get video duration
    duration = 10.0
    try:
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", str(video_path),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if proc.returncode == 0:
            data = json.loads(proc.stdout)
            dur = data.get("format", {}).get("duration")
            if dur:
                duration = float(dur)
    except Exception:
        pass

    # Group layers by time range for efficient rendering
    # For simplicity, render ALL layers into a single image and overlay it.
    # Time-based visibility: compute earliest start and latest end across all layers
    # to set the overlay enable window. For more precise per-layer timing,
    # we generate separate overlay images per unique time range.

    # Build time-grouped layer sets
    time_groups = {}
    for layer in layers:
        start = layer.get("startTime", 0)
        end = layer.get("endTime", -1)
        if end < 0:
            end = duration
        key = (start, end)
        if key not in time_groups:
            time_groups[key] = []
        time_groups[key].append(layer)

    if not time_groups:
        return False, "No overlay layers defined"

    # Render separate overlay images for each time group
    overlay_images = []
    try:
        for (start, end), group_layers in time_groups.items():
            overlay_path = _render_overlay_image(group_layers, video_width, video_height)
            overlay_images.append((overlay_path, start, end))
    except Exception as e:
        logger.error(f"Failed to render overlay images: {e}")
        return False, f"Failed to render overlay images: {e}"

    # Build ffmpeg complex filter with multiple overlay inputs
    # Input 0 = video, Input 1..N = overlay images
    inputs = ["-i", str(video_path)]
    for (ov_path, _, _) in overlay_images:
        inputs.extend(["-i", str(ov_path)])

    # Build filter_complex
    filter_parts = []
    current_label = "[0:v]"
    for i, (ov_path, start, end) in enumerate(overlay_images):
        next_label = f"[v{i}]" if i < len(overlay_images) - 1 else "[vout]"
        overlay_input = f"[{i + 1}:v]"
        enable_expr = f"between(t\\,{start}\\,{end})"
        filter_parts.append(
            f"{current_label}{overlay_input}overlay=0:0:enable='{enable_expr}'{next_label}"
        )
        current_label = next_label

    filter_complex = ";".join(filter_parts)

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", "0:a?",
        "-codec:a", "copy",
        "-preset", "fast",
        "-crf", "23",
        str(output_path),
    ]

    logger.info(f"Running ffmpeg overlay render: {len(overlay_images)} overlay(s) -> {output_path.name}")

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if proc.returncode != 0:
            error_msg = proc.stderr[-500:] if proc.stderr else "Unknown ffmpeg error"
            logger.error(f"ffmpeg rendering failed: {error_msg}")
            return False, error_msg

        if output_path.exists() and output_path.stat().st_size > 0:
            # Clean up temp overlay images
            for (ov_path, _, _) in overlay_images:
                try:
                    os.remove(ov_path)
                except OSError:
                    pass
            return True, ""
        else:
            return False, "ffmpeg produced empty or missing output file"

    except FileNotFoundError:
        return False, "ffmpeg not found on system"
    except subprocess.TimeoutExpired:
        return False, "ffmpeg rendering timed out (>5 min)"
    except Exception as e:
        return False, str(e)


# ---------- API Routes ----------

@router.get("")
async def list_video_overlays(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List all video overlays for the current user."""
    result = await db.execute(
        select(VideoOverlay)
        .where(VideoOverlay.user_id == user_id)
        .order_by(VideoOverlay.updated_at.desc())
    )
    overlays = result.scalars().all()
    return [overlay_to_dict(o) for o in overlays]


@router.get("/{overlay_id}")
async def get_video_overlay(
    overlay_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific video overlay."""
    result = await db.execute(
        select(VideoOverlay).where(
            VideoOverlay.id == overlay_id,
            VideoOverlay.user_id == user_id,
        )
    )
    overlay = result.scalar_one_or_none()
    if not overlay:
        raise HTTPException(status_code=404, detail="Video overlay not found")
    return overlay_to_dict(overlay)


@router.post("")
async def create_video_overlay(
    data: VideoOverlayCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a new video overlay configuration."""
    # Verify asset exists and belongs to user
    result = await db.execute(
        select(Asset).where(Asset.id == data.asset_id, Asset.user_id == user_id)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Video asset not found")
    if not asset.file_type or not asset.file_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Asset is not a video")

    layers_json = json.dumps([layer.model_dump() for layer in data.layers])

    overlay = VideoOverlay(
        user_id=user_id,
        asset_id=data.asset_id,
        name=data.name,
        layers=layers_json,
    )
    db.add(overlay)
    await db.flush()
    await db.refresh(overlay)
    result_dict = overlay_to_dict(overlay)
    await db.commit()
    return result_dict


@router.put("/{overlay_id}")
async def update_video_overlay(
    overlay_id: int,
    data: VideoOverlayUpdate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing video overlay configuration."""
    result = await db.execute(
        select(VideoOverlay).where(
            VideoOverlay.id == overlay_id,
            VideoOverlay.user_id == user_id,
        )
    )
    overlay = result.scalar_one_or_none()
    if not overlay:
        raise HTTPException(status_code=404, detail="Video overlay not found")

    if data.name is not None:
        overlay.name = data.name
    if data.layers is not None:
        overlay.layers = json.dumps([layer.model_dump() for layer in data.layers])
        # Reset render status when layers change
        overlay.render_status = "pending"
        overlay.rendered_path = None

    await db.flush()
    await db.refresh(overlay)
    result_dict = overlay_to_dict(overlay)
    await db.commit()
    return result_dict


@router.delete("/{overlay_id}")
async def delete_video_overlay(
    overlay_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a video overlay."""
    result = await db.execute(
        select(VideoOverlay).where(
            VideoOverlay.id == overlay_id,
            VideoOverlay.user_id == user_id,
        )
    )
    overlay = result.scalar_one_or_none()
    if not overlay:
        raise HTTPException(status_code=404, detail="Video overlay not found")

    # Delete rendered file if exists
    if overlay.rendered_path:
        rendered_file = APP_DIR / "static" / overlay.rendered_path.lstrip("/")
        if rendered_file.exists():
            try:
                os.remove(rendered_file)
            except OSError:
                pass

    await db.delete(overlay)
    await db.commit()
    return {"status": "deleted", "id": overlay_id}


@router.post("/{overlay_id}/render")
async def render_video_overlay(
    overlay_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Render the video with overlays using ffmpeg.

    Applies all text/branding layers to the source video and produces an MP4 output.
    """
    if not FFMPEG_AVAILABLE:
        raise HTTPException(status_code=501, detail="Video-Overlay-Rendering ist auf diesem Server nicht verfuegbar (ffmpeg fehlt).")

    result = await db.execute(
        select(VideoOverlay).where(
            VideoOverlay.id == overlay_id,
            VideoOverlay.user_id == user_id,
        )
    )
    overlay = result.scalar_one_or_none()
    if not overlay:
        raise HTTPException(status_code=404, detail="Video overlay not found")

    # Get source video asset
    asset_result = await db.execute(
        select(Asset).where(Asset.id == overlay.asset_id)
    )
    asset = asset_result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Source video asset not found")

    video_path = APP_DIR / "static" / asset.file_path.lstrip("/")
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Source video file not found on disk")

    # Parse layers
    layers = []
    try:
        layers = json.loads(overlay.layers)
    except (json.JSONDecodeError, TypeError):
        layers = []

    if not layers:
        raise HTTPException(status_code=400, detail="No overlay layers defined")

    # Generate output filename
    output_filename = f"overlay_{overlay.id}_{uuid.uuid4().hex[:8]}.mp4"
    output_path = EXPORTS_DIR / output_filename

    # Mark as rendering
    overlay.render_status = "rendering"
    await db.commit()

    # Run ffmpeg
    success, error_msg = _render_video_with_overlays(video_path, layers, output_path)

    if success:
        overlay.render_status = "done"
        overlay.rendered_path = f"/uploads/exports/{output_filename}"
        overlay.render_error = None
        # Persist rendered file in DB for Vercel
        from app.core.paths import IS_VERCEL
        if IS_VERCEL and output_path.exists():
            import base64 as _b64
            overlay.rendered_data = _b64.b64encode(output_path.read_bytes()).decode("ascii")
    else:
        overlay.render_status = "error"
        overlay.render_error = error_msg

    await db.flush()
    await db.refresh(overlay)
    result_dict = overlay_to_dict(overlay)
    await db.commit()

    if not success:
        raise HTTPException(status_code=500, detail=f"Rendering failed: {error_msg}")

    return result_dict
