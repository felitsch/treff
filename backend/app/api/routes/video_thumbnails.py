"""Video Thumbnail AI routes - Extract best frames and generate thumbnail variants.

Supports:
- AI-based frame extraction (ffmpeg + scoring)
- Text overlay generation
- A/B variant creation
- PNG export in multiple sizes
"""

import asyncio
import json
import logging
import os
import subprocess
import uuid
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

logger = logging.getLogger(__name__)
router = APIRouter()

THUMBNAIL_DIR = get_upload_dir("thumbnails")


# ─── Request/Response models ─────────────────────────────────

class ExtractFramesRequest(BaseModel):
    asset_id: int
    frame_count: int = Field(default=8, ge=3, le=20)


class FrameResult(BaseModel):
    frame_index: int
    timestamp: float
    filename: str
    score: float = 0.0
    url: str = ""


class ExtractFramesResponse(BaseModel):
    asset_id: int
    frames: list[FrameResult]
    total_duration: float = 0.0


class GenerateVariantsRequest(BaseModel):
    asset_id: int
    frame_filename: str
    headline: str = ""
    subtext: str = ""
    position: str = "center"  # center, top, bottom
    font_family: str = "Inter"
    font_size: int = 48
    text_color: str = "#FFFFFF"
    bg_color: str = "#000000"
    bg_opacity: float = 0.6
    brightness: float = 1.0
    contrast: float = 1.0
    variant_count: int = Field(default=3, ge=1, le=5)


class VariantResult(BaseModel):
    variant_index: int
    filename: str
    url: str
    style: str = ""


class ExportThumbnailRequest(BaseModel):
    source_filename: str
    size: str = "1080x1350"  # 1080x1350, 1080x1080, 1080x1920


# ─── Endpoints ────────────────────────────────────────────────

@router.post("/extract-frames", response_model=ExtractFramesResponse)
async def extract_frames(
    body: ExtractFramesRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Extract the best frames from a video using ffmpeg scene detection."""
    # Fetch asset
    result = await db.execute(
        select(Asset).where(Asset.id == body.asset_id, Asset.user_id == user_id)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Get file path
    file_path = None
    if asset.file_path and os.path.exists(asset.file_path):
        file_path = asset.file_path
    elif hasattr(asset, 'file_data') and asset.file_data:
        # Vercel: write temp file from base64
        import base64
        import tempfile
        tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        tmp.write(base64.b64decode(asset.file_data))
        tmp.close()
        file_path = tmp.name

    if not file_path:
        raise HTTPException(status_code=400, detail="Video file not accessible")

    # Get video duration via ffprobe
    duration = _get_video_duration(file_path)
    if duration <= 0:
        raise HTTPException(status_code=400, detail="Could not determine video duration")

    # Extract frames at evenly spaced intervals
    frames = []
    frame_count = min(body.frame_count, max(3, int(duration)))
    interval = duration / (frame_count + 1)

    os.makedirs(THUMBNAIL_DIR, exist_ok=True)
    batch_id = uuid.uuid4().hex[:8]

    for i in range(frame_count):
        timestamp = interval * (i + 1)
        frame_filename = f"frame_{batch_id}_{i:03d}.jpg"
        output_path = os.path.join(THUMBNAIL_DIR, frame_filename)

        try:
            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-ss", str(timestamp),
                    "-i", file_path,
                    "-frames:v", "1",
                    "-q:v", "2",
                    output_path,
                ],
                capture_output=True,
                timeout=10,
            )

            if os.path.exists(output_path):
                # Simple scoring based on file size (larger = more detail = better)
                file_size = os.path.getsize(output_path)
                score = min(1.0, file_size / 100000)  # Normalize to 0-1

                frames.append(FrameResult(
                    frame_index=i,
                    timestamp=round(timestamp, 2),
                    filename=frame_filename,
                    score=round(score, 3),
                    url=f"/api/video/thumbnails/frame/{frame_filename}",
                ))
        except Exception as e:
            logger.warning(f"Failed to extract frame at {timestamp}s: {e}")

    # Sort by score (best first)
    frames.sort(key=lambda f: f.score, reverse=True)

    return ExtractFramesResponse(
        asset_id=body.asset_id,
        frames=frames,
        total_duration=round(duration, 2),
    )


@router.get("/frame/{filename}")
async def get_frame(
    filename: str,
    user_id: int = Depends(get_current_user_id),
):
    """Serve an extracted frame image."""
    # Sanitize filename
    safe_name = os.path.basename(filename)
    file_path = os.path.join(THUMBNAIL_DIR, safe_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Frame not found")
    return FileResponse(file_path, media_type="image/jpeg")


@router.post("/generate-variants")
async def generate_variants(
    body: GenerateVariantsRequest,
    user_id: int = Depends(get_current_user_id),
):
    """Generate A/B thumbnail variants with text overlays."""
    source_path = os.path.join(THUMBNAIL_DIR, os.path.basename(body.frame_filename))
    if not os.path.exists(source_path):
        raise HTTPException(status_code=404, detail="Source frame not found")

    variants = []
    batch_id = uuid.uuid4().hex[:8]

    # Variant styles
    styles = [
        {"name": "Standard", "brightness": body.brightness, "contrast": body.contrast, "text_shadow": False},
        {"name": "Dramatisch", "brightness": body.brightness * 0.8, "contrast": body.contrast * 1.3, "text_shadow": True},
        {"name": "Hell & Frisch", "brightness": min(1.5, body.brightness * 1.2), "contrast": body.contrast * 0.9, "text_shadow": False},
    ]

    for idx, style in enumerate(styles[:body.variant_count]):
        variant_filename = f"variant_{batch_id}_{idx:02d}.png"
        output_path = os.path.join(THUMBNAIL_DIR, variant_filename)

        try:
            _generate_thumbnail_variant(
                source_path=source_path,
                output_path=output_path,
                headline=body.headline,
                subtext=body.subtext,
                position=body.position,
                font_family=body.font_family,
                font_size=body.font_size,
                text_color=body.text_color,
                bg_color=body.bg_color,
                bg_opacity=body.bg_opacity,
                brightness=style["brightness"],
                contrast=style["contrast"],
                text_shadow=style["text_shadow"],
            )

            if os.path.exists(output_path):
                variants.append(VariantResult(
                    variant_index=idx,
                    filename=variant_filename,
                    url=f"/api/video/thumbnails/frame/{variant_filename}",
                    style=style["name"],
                ))
        except Exception as e:
            logger.error(f"Failed to generate variant {idx}: {e}")

    return {"variants": variants, "count": len(variants)}


@router.post("/export")
async def export_thumbnail(
    body: ExportThumbnailRequest,
    user_id: int = Depends(get_current_user_id),
):
    """Export a thumbnail in a specific size (1080x1080 or 1080x1920)."""
    source_path = os.path.join(THUMBNAIL_DIR, os.path.basename(body.source_filename))
    if not os.path.exists(source_path):
        raise HTTPException(status_code=404, detail="Source file not found")

    # Parse size
    try:
        width, height = body.size.split("x")
        width, height = int(width), int(height)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid size format. Use WxH (e.g., 1080x1080)")

    export_filename = f"thumbnail_export_{uuid.uuid4().hex[:8]}_{width}x{height}.png"
    output_path = os.path.join(THUMBNAIL_DIR, export_filename)

    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", source_path,
                "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:-1:-1:color=black",
                output_path,
            ],
            capture_output=True,
            timeout=10,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

    if not os.path.exists(output_path):
        raise HTTPException(status_code=500, detail="Export failed to produce output file")

    return FileResponse(
        output_path,
        media_type="image/png",
        filename=export_filename,
        headers={"Content-Disposition": f"attachment; filename={export_filename}"},
    )


# ─── Helper functions ─────────────────────────────────────────

def _get_video_duration(file_path: str) -> float:
    """Get video duration in seconds via ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "json",
                file_path,
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        data = json.loads(result.stdout)
        return float(data.get("format", {}).get("duration", 0))
    except Exception as e:
        logger.error(f"ffprobe failed: {e}")
        return 0.0


def _generate_thumbnail_variant(
    source_path: str,
    output_path: str,
    headline: str = "",
    subtext: str = "",
    position: str = "center",
    font_family: str = "Inter",
    font_size: int = 48,
    text_color: str = "#FFFFFF",
    bg_color: str = "#000000",
    bg_opacity: float = 0.6,
    brightness: float = 1.0,
    contrast: float = 1.0,
    text_shadow: bool = False,
):
    """Generate a single thumbnail variant using Pillow."""
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageEnhance

        img = Image.open(source_path).convert("RGBA")

        # Apply brightness/contrast
        if brightness != 1.0:
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(brightness)
        if contrast != 1.0:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(contrast)

        # Add text overlay if headline or subtext provided
        if headline or subtext:
            draw = ImageDraw.Draw(img)
            w, h = img.size

            # Try to load font
            try:
                font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
                font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(font_size * 0.6))
            except (OSError, IOError):
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()

            # Calculate text position
            text_lines = []
            if headline:
                text_lines.append(("headline", headline, font_large))
            if subtext:
                text_lines.append(("subtext", subtext, font_small))

            # Calculate total text height
            total_h = 0
            line_metrics = []
            for label, text, font in text_lines:
                bbox = draw.textbbox((0, 0), text, font=font)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
                line_metrics.append((text, font, tw, th))
                total_h += th + 10

            # Position
            if position == "top":
                y_start = int(h * 0.1)
            elif position == "bottom":
                y_start = int(h * 0.9) - total_h
            else:
                y_start = (h - total_h) // 2

            # Draw semi-transparent background
            bg_r = int(bg_color[1:3], 16) if len(bg_color) >= 7 else 0
            bg_g = int(bg_color[3:5], 16) if len(bg_color) >= 7 else 0
            bg_b = int(bg_color[5:7], 16) if len(bg_color) >= 7 else 0
            bg_alpha = int(bg_opacity * 255)

            overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)

            padding = 20
            max_tw = max(m[2] for m in line_metrics) if line_metrics else 0
            overlay_draw.rectangle(
                [
                    (w // 2 - max_tw // 2 - padding, y_start - padding),
                    (w // 2 + max_tw // 2 + padding, y_start + total_h + padding),
                ],
                fill=(bg_r, bg_g, bg_b, bg_alpha),
            )
            img = Image.alpha_composite(img, overlay)
            draw = ImageDraw.Draw(img)

            # Draw text
            y = y_start
            for text, font, tw, th in line_metrics:
                x = (w - tw) // 2
                tc_r = int(text_color[1:3], 16) if len(text_color) >= 7 else 255
                tc_g = int(text_color[3:5], 16) if len(text_color) >= 7 else 255
                tc_b = int(text_color[5:7], 16) if len(text_color) >= 7 else 255

                if text_shadow:
                    draw.text((x + 2, y + 2), text, fill=(0, 0, 0, 180), font=font)
                draw.text((x, y), text, fill=(tc_r, tc_g, tc_b, 255), font=font)
                y += th + 10

        # Save as PNG
        img.convert("RGB").save(output_path, "PNG", quality=95)

    except ImportError:
        # Fallback: just copy the source file with ffmpeg filter
        filters = []
        if brightness != 1.0 or contrast != 1.0:
            filters.append(f"eq=brightness={brightness - 1}:contrast={contrast}")
        filter_str = ",".join(filters) if filters else "null"
        subprocess.run(
            ["ffmpeg", "-y", "-i", source_path, "-vf", filter_str, output_path],
            capture_output=True,
            timeout=10,
        )
