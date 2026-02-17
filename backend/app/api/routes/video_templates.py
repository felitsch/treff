"""Video Template routes - CRUD for intro/outro branding templates + ffmpeg concat."""

import json
import logging
import os
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.core.paths import get_upload_dir
from app.models.video_template import VideoTemplate
from app.models.asset import Asset

logger = logging.getLogger(__name__)

router = APIRouter()

ASSETS_UPLOAD_DIR = get_upload_dir("assets")
COMPOSED_DIR = get_upload_dir("composed")
THUMBNAILS_DIR = get_upload_dir("thumbnails")
TEMPLATES_DIR = get_upload_dir("video_templates")

FFMPEG_AVAILABLE = shutil.which("ffmpeg") is not None

# Country metadata for templates
COUNTRY_META = {
    "usa": {"flag": "🇺🇸", "label": "USA"},
    "kanada": {"flag": "🇨🇦", "label": "Kanada"},
    "australien": {"flag": "🇦🇺", "label": "Australien"},
    "neuseeland": {"flag": "🇳🇿", "label": "Neuseeland"},
    "irland": {"flag": "🇮🇪", "label": "Irland"},
}

STYLE_META = {
    "default": {"label": "Klassisch", "icon": "🎬"},
    "minimal": {"label": "Minimal", "icon": "✨"},
    "bold": {"label": "Bold", "icon": "💥"},
    "elegant": {"label": "Elegant", "icon": "🎭"},
}


# ── Pydantic Schemas ──

class VideoTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    template_type: str = Field(..., pattern="^(intro|outro)$")
    country: Optional[str] = None
    duration_seconds: float = Field(default=3.0, ge=1.0, le=10.0)
    style: str = Field(default="default")
    primary_color: str = Field(default="#4C8BC2")
    secondary_color: str = Field(default="#FDD000")
    social_handle_instagram: Optional[str] = "@treff_sprachreisen"
    social_handle_tiktok: Optional[str] = "@treff_sprachreisen"
    website_url: Optional[str] = "www.treff-sprachreisen.de"
    cta_text: Optional[str] = None
    branding_config: Optional[dict] = None


class VideoTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    country: Optional[str] = None
    duration_seconds: Optional[float] = None
    style: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    social_handle_instagram: Optional[str] = None
    social_handle_tiktok: Optional[str] = None
    website_url: Optional[str] = None
    cta_text: Optional[str] = None
    branding_config: Optional[dict] = None


class ApplyTemplateRequest(BaseModel):
    """Request to apply intro/outro templates to a video asset."""
    video_asset_id: int
    intro_template_id: Optional[int] = None
    outro_template_id: Optional[int] = None
    output_format: str = Field(default="9:16", pattern="^(9:16|1:1|16:9)$")
    save_as_asset: bool = True


# Output format presets (same as video_composer)
OUTPUT_FORMATS = {
    "9:16": {"width": 1080, "height": 1920},
    "1:1": {"width": 1080, "height": 1080},
    "16:9": {"width": 1920, "height": 1080},
}


def _template_to_dict(tmpl: VideoTemplate) -> dict:
    """Convert a VideoTemplate to API response dict."""
    config = None
    if tmpl.branding_config:
        try:
            config = json.loads(tmpl.branding_config)
        except (json.JSONDecodeError, TypeError):
            config = None

    country_info = COUNTRY_META.get(tmpl.country) if tmpl.country else None
    style_info = STYLE_META.get(tmpl.style, STYLE_META["default"])

    # Extract country-specific motif and HTML template path from config
    motif = config.get("motif") if config else None
    html_template = config.get("html_template") if config else None
    country_accent = config.get("country_accent") if config else None
    background_gradient = config.get("background_gradient") if config else None

    return {
        "id": tmpl.id,
        "name": tmpl.name,
        "description": tmpl.description,
        "template_type": tmpl.template_type,
        "country": tmpl.country,
        "country_flag": country_info["flag"] if country_info else None,
        "country_label": country_info["label"] if country_info else None,
        "duration_seconds": tmpl.duration_seconds,
        "width": tmpl.width,
        "height": tmpl.height,
        "aspect_ratio": tmpl.aspect_ratio,
        "style": tmpl.style,
        "style_label": style_info["label"],
        "style_icon": style_info["icon"],
        "primary_color": tmpl.primary_color,
        "secondary_color": tmpl.secondary_color,
        "social_handle_instagram": tmpl.social_handle_instagram,
        "social_handle_tiktok": tmpl.social_handle_tiktok,
        "website_url": tmpl.website_url,
        "cta_text": tmpl.cta_text,
        "branding_config": config,
        "motif": motif,
        "html_template": html_template,
        "country_accent": country_accent,
        "background_gradient": background_gradient,
        "is_default": tmpl.is_default,
        "preview_image_path": tmpl.preview_image_path,
        "created_at": tmpl.created_at.isoformat() if tmpl.created_at else None,
        "updated_at": tmpl.updated_at.isoformat() if tmpl.updated_at else None,
    }


# ── CRUD Routes ──

@router.get("")
async def list_video_templates(
    template_type: Optional[str] = Query(None, description="Filter by 'intro' or 'outro'"),
    country: Optional[str] = Query(None, description="Filter by country code"),
    style: Optional[str] = Query(None, description="Filter by style"),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List all video templates (system defaults + user-created)."""
    query = select(VideoTemplate).where(
        or_(VideoTemplate.is_default == True, VideoTemplate.user_id == user_id)
    )

    if template_type:
        query = query.where(VideoTemplate.template_type == template_type)
    if country:
        query = query.where(VideoTemplate.country == country)
    if style:
        query = query.where(VideoTemplate.style == style)

    query = query.order_by(VideoTemplate.template_type, VideoTemplate.is_default.desc(), VideoTemplate.name)

    result = await db.execute(query)
    templates = result.scalars().all()

    return {
        "templates": [_template_to_dict(t) for t in templates],
        "total": len(templates),
        "countries": COUNTRY_META,
        "styles": STYLE_META,
    }


@router.get("/{template_id}")
async def get_video_template(
    template_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific video template by ID."""
    result = await db.execute(
        select(VideoTemplate).where(
            VideoTemplate.id == template_id,
            or_(VideoTemplate.is_default == True, VideoTemplate.user_id == user_id),
        )
    )
    tmpl = result.scalar_one_or_none()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Video template not found")

    return _template_to_dict(tmpl)


@router.post("", status_code=201)
async def create_video_template(
    data: VideoTemplateCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a custom video template."""
    branding_json = json.dumps(data.branding_config) if data.branding_config else None

    tmpl = VideoTemplate(
        name=data.name,
        description=data.description,
        template_type=data.template_type,
        country=data.country,
        duration_seconds=data.duration_seconds,
        style=data.style,
        primary_color=data.primary_color,
        secondary_color=data.secondary_color,
        social_handle_instagram=data.social_handle_instagram,
        social_handle_tiktok=data.social_handle_tiktok,
        website_url=data.website_url,
        cta_text=data.cta_text,
        branding_config=branding_json,
        is_default=False,
        user_id=user_id,
    )
    db.add(tmpl)
    await db.flush()
    await db.refresh(tmpl)

    return _template_to_dict(tmpl)


@router.put("/{template_id}")
async def update_video_template(
    template_id: int,
    data: VideoTemplateUpdate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update a video template. Only user-created templates can be updated."""
    result = await db.execute(
        select(VideoTemplate).where(
            VideoTemplate.id == template_id,
            VideoTemplate.user_id == user_id,
            VideoTemplate.is_default == False,
        )
    )
    tmpl = result.scalar_one_or_none()
    if not tmpl:
        raise HTTPException(
            status_code=404,
            detail="Template not found or is a system default (cannot edit)",
        )

    update_data = data.model_dump(exclude_unset=True)
    if "branding_config" in update_data and update_data["branding_config"] is not None:
        update_data["branding_config"] = json.dumps(update_data["branding_config"])

    for key, value in update_data.items():
        setattr(tmpl, key, value)

    await db.flush()
    await db.refresh(tmpl)

    return _template_to_dict(tmpl)


@router.delete("/{template_id}")
async def delete_video_template(
    template_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a user-created video template. System defaults cannot be deleted."""
    result = await db.execute(
        select(VideoTemplate).where(
            VideoTemplate.id == template_id,
            VideoTemplate.user_id == user_id,
            VideoTemplate.is_default == False,
        )
    )
    tmpl = result.scalar_one_or_none()
    if not tmpl:
        raise HTTPException(
            status_code=404,
            detail="Template not found or is a system default (cannot delete)",
        )

    await db.delete(tmpl)
    return {"message": "Template deleted", "id": template_id}


# ── Video Generation Helpers ──

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


def _generate_branding_video(template: VideoTemplate, target_w: int, target_h: int, output_path: Path):
    """Generate a branding video clip (intro or outro) using ffmpeg.

    Creates a video with TREFF branding elements:
    - Solid or gradient background in TREFF/country-specific colors
    - Centered text overlay (brand name, tagline)
    - Social handles for outro templates
    - Country-specific color theming
    - Specified duration (3-5 seconds)
    """
    duration = template.duration_seconds
    primary = template.primary_color or "#4C8BC2"
    secondary = template.secondary_color or "#FDD000"

    config = {}
    if template.branding_config:
        try:
            config = json.loads(template.branding_config)
        except (json.JSONDecodeError, TypeError):
            pass

    # Determine background style
    bg_style = config.get("background", "gradient_blue_yellow")
    country_accent = config.get("country_accent", secondary)

    # Build drawtext filter chain for brand elements
    text_filters = []

    # Main text overlay
    text_overlay = config.get("text_overlay", "TREFF Sprachreisen")
    if text_overlay:
        # Escape special characters for ffmpeg drawtext
        escaped_text = text_overlay.replace("'", "\\'").replace(":", "\\:").replace("×", "x")
        text_filters.append(
            f"drawtext=text='{escaped_text}':"
            f"fontsize={int(target_w * 0.06)}:fontcolor=white:"
            f"x=(w-text_w)/2:y=(h-text_h)/2-{int(target_h * 0.05)}:"
            f"enable='between(t,0.3,{duration})'"
        )

    # Subtitle text (country-specific subtitle like "Your American Dream")
    subtitle = config.get("subtitle")
    if subtitle:
        escaped_sub = subtitle.replace("'", "\\'").replace(":", "\\:")
        # Use country accent color for subtitle if available
        sub_color = f"white@0.9"
        text_filters.append(
            f"drawtext=text='{escaped_sub}':"
            f"fontsize={int(target_w * 0.035)}:fontcolor={sub_color}:"
            f"x=(w-text_w)/2:y=(h-text_h)/2+{int(target_h * 0.03)}:"
            f"enable='between(t,0.6,{duration})'"
        )

    # For outro: social handles, CTA, and country-specific pricing
    if template.template_type == "outro":
        show_social = config.get("show_social_handles", True)
        if show_social and template.social_handle_instagram:
            ig_text = template.social_handle_instagram.replace("'", "\\'").replace(":", "\\:")
            text_filters.append(
                f"drawtext=text='Instagram\\: {ig_text}':"
                f"fontsize={int(target_w * 0.028)}:fontcolor=white@0.85:"
                f"x=(w-text_w)/2:y=h*0.7:"
                f"enable='between(t,0.8,{duration})'"
            )
        if show_social and template.social_handle_tiktok:
            tt_text = template.social_handle_tiktok.replace("'", "\\'").replace(":", "\\:")
            text_filters.append(
                f"drawtext=text='TikTok\\: {tt_text}':"
                f"fontsize={int(target_w * 0.028)}:fontcolor=white@0.85:"
                f"x=(w-text_w)/2:y=h*0.75:"
                f"enable='between(t,1.0,{duration})'"
            )

        show_website = config.get("show_website", True)
        if show_website and template.website_url:
            web_text = template.website_url.replace("'", "\\'").replace(":", "\\:")
            # Use country accent or secondary for website text
            web_color = country_accent if template.country else secondary
            text_filters.append(
                f"drawtext=text='{web_text}':"
                f"fontsize={int(target_w * 0.032)}:fontcolor={web_color}:"
                f"x=(w-text_w)/2:y=h*0.82:"
                f"enable='between(t,1.2,{duration})'"
            )

        show_cta = config.get("show_cta", True)
        if show_cta and template.cta_text:
            cta_text = template.cta_text.replace("'", "\\'").replace(":", "\\:")
            # Use yellow/gold for CTA to stand out
            cta_color = "#FDD000" if template.country else secondary
            text_filters.append(
                f"drawtext=text='{cta_text}':"
                f"fontsize={int(target_w * 0.04)}:fontcolor={cta_color}:"
                f"x=(w-text_w)/2:y=h*0.6:"
                f"enable='between(t,0.5,{duration})'"
            )

    # Build the ffmpeg color source + filter
    # Country-specific background colors for more distinctive templates
    if "dark" in bg_style:
        bg_color = "0x1A1A2E"
    elif "white" in bg_style:
        bg_color = "0xFFFFFF"
    elif "usa" in bg_style:
        bg_color = "0x002868"  # Navy blue for USA
    elif "canada" in bg_style:
        bg_color = "0xCC0000"  # Deep red for Canada
    elif "australia" in bg_style or "surf" in bg_style:
        bg_color = "0xCC8040"  # Sandy earth tone for Australia
    elif "nz" in bg_style or "fern" in bg_style:
        bg_color = "0x1B6B1B"  # Forest green for NZ
    elif "ireland" in bg_style or "green_gold" in bg_style:
        bg_color = "0x148050"  # Irish green
    elif "yellow" in bg_style:
        bg_color = primary.replace("#", "0x")
    else:
        bg_color = primary.replace("#", "0x")

    # Build video filter chain
    vf_parts = []
    if text_filters:
        vf_parts.extend(text_filters)

    # Add fade in/out
    vf_parts.append(f"fade=t=in:st=0:d=0.3")
    vf_parts.append(f"fade=t=out:st={max(0, duration - 0.3)}:d=0.3")

    vf_string = ",".join(vf_parts) if vf_parts else "null"

    cmd = [
        "ffmpeg",
        "-f", "lavfi",
        "-i", f"color=c={bg_color}:s={target_w}x{target_h}:d={duration}:r=30",
        "-f", "lavfi",
        "-i", f"anullsrc=channel_layout=stereo:sample_rate=44100",
        "-t", str(duration),
        "-vf", vf_string,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-profile:v", "high", "-level", "4.0",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        "-movflags", "+faststart",
        "-y", str(output_path),
    ]

    logger.info(f"Generating branding video: {template.name} ({duration}s, {target_w}x{target_h})")
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if proc.returncode != 0:
        logger.error(f"Branding video generation failed: {proc.stderr[:2000]}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate branding video: {proc.stderr[:500]}",
        )


def _concat_videos(video_paths: list, output_path: Path, target_w: int, target_h: int):
    """Concatenate multiple video files using ffmpeg concat demuxer.

    All input videos should already be the same resolution.
    Uses xfade for smooth transitions between intro->content and content->outro.
    """
    n = len(video_paths)
    if n == 1:
        # Just copy the single file
        import shutil
        shutil.copy2(str(video_paths[0]), str(output_path))
        return

    # Build ffmpeg complex filter for concat with crossfade
    cmd = ["ffmpeg"]
    filter_parts = []

    # Calculate durations via ffprobe for offset calculation
    durations = []
    for vp in video_paths:
        meta = _extract_video_metadata(vp)
        dur = meta.get("duration_seconds") or 3.0
        durations.append(dur)

    # Add inputs
    for vp in video_paths:
        cmd.extend(["-i", str(vp)])

    # Scale/pad each input and set fps
    for i in range(n):
        filter_parts.append(
            f"[{i}:v]scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,"
            f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:black,setsar=1,"
            f"fps=30,format=yuv420p[v{i}]"
        )

    # Build xfade chain for smooth transitions
    trans_dur = 0.3  # Short crossfade between segments
    current_label = "v0"
    cumulative_offset = 0.0

    for i in range(1, n):
        if i == 1:
            offset = durations[0] - trans_dur
        else:
            offset = cumulative_offset + durations[i - 1] - trans_dur
        offset = max(0, offset)

        out_label = f"xf{i}"
        if i < n - 1:
            filter_parts.append(
                f"[{current_label}][v{i}]xfade=transition=fade:duration={trans_dur:.2f}:offset={offset:.2f}[{out_label}]"
            )
            current_label = out_label
        else:
            filter_parts.append(
                f"[{current_label}][v{i}]xfade=transition=fade:duration={trans_dur:.2f}:offset={offset:.2f},format=yuv420p[outv]"
            )

        cumulative_offset = offset

    # Audio concat
    for i in range(n):
        filter_parts.append(
            f"[{i}:a]aresample=44100,aformat=sample_fmts=fltp:channel_layouts=stereo[a{i}]"
        )
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

    logger.info(f"Concatenating {n} video segments with xfade transitions...")
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if proc.returncode != 0:
        logger.error(f"Video concat failed: {proc.stderr[:2000]}")
        # Fallback: simple concat without transitions
        _concat_simple(video_paths, output_path, target_w, target_h)


def _concat_simple(video_paths: list, output_path: Path, target_w: int, target_h: int):
    """Simple concat fallback without transitions."""
    n = len(video_paths)
    cmd = ["ffmpeg"]
    filter_parts = []

    for i, vp in enumerate(video_paths):
        cmd.extend(["-i", str(vp)])
        filter_parts.append(
            f"[{i}:v]scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,"
            f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:black,setsar=1,"
            f"fps=30,format=yuv420p[v{i}]"
        )

    video_inputs = "".join(f"[v{i}]" for i in range(n))
    filter_parts.append(f"{video_inputs}concat=n={n}:v=1:a=0[outv]")

    filter_complex = ";".join(filter_parts)
    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p", "-an",
        "-movflags", "+faststart",
        "-y", str(output_path),
    ])

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if proc.returncode != 0:
        logger.error(f"Simple concat also failed: {proc.stderr[:2000]}")
        raise HTTPException(status_code=500, detail="Video concatenation failed")


def _generate_thumbnail(video_path: Path, thumbnail_filename: str) -> Optional[str]:
    """Generate thumbnail from video."""
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


# ── Apply Templates Route ──

@router.post("/apply")
async def apply_video_templates(
    request: ApplyTemplateRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Apply intro and/or outro templates to a video asset.

    Generates branding videos from templates, then concatenates:
    [intro] + [content video] + [outro] using ffmpeg.

    Returns the composed video with full metadata.
    """
    if not FFMPEG_AVAILABLE:
        raise HTTPException(status_code=501, detail="Video-Templates sind auf diesem Server nicht verfuegbar (ffmpeg fehlt).")

    if not request.intro_template_id and not request.outro_template_id:
        raise HTTPException(
            status_code=400,
            detail="At least one of intro_template_id or outro_template_id is required",
        )

    # Fetch the content video asset
    result = await db.execute(
        select(Asset).where(Asset.id == request.video_asset_id, Asset.user_id == user_id)
    )
    video_asset = result.scalar_one_or_none()
    if not video_asset:
        raise HTTPException(status_code=404, detail="Video asset not found")

    if not video_asset.file_type or not video_asset.file_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Asset is not a video")

    content_path = ASSETS_UPLOAD_DIR / video_asset.filename
    if not content_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found on disk")

    # Determine output dimensions
    fmt = OUTPUT_FORMATS.get(request.output_format, OUTPUT_FORMATS["9:16"])
    target_w = fmt["width"]
    target_h = fmt["height"]

    # Fetch and generate intro if requested
    intro_path = None
    intro_template = None
    if request.intro_template_id:
        result = await db.execute(
            select(VideoTemplate).where(
                VideoTemplate.id == request.intro_template_id,
                or_(VideoTemplate.is_default == True, VideoTemplate.user_id == user_id),
            )
        )
        intro_template = result.scalar_one_or_none()
        if not intro_template:
            raise HTTPException(status_code=404, detail="Intro template not found")
        if intro_template.template_type != "intro":
            raise HTTPException(status_code=400, detail="Selected template is not an intro")

        intro_path = TEMPLATES_DIR / f"intro_{uuid.uuid4()}.mp4"
        _generate_branding_video(intro_template, target_w, target_h, intro_path)

    # Fetch and generate outro if requested
    outro_path = None
    outro_template = None
    if request.outro_template_id:
        result = await db.execute(
            select(VideoTemplate).where(
                VideoTemplate.id == request.outro_template_id,
                or_(VideoTemplate.is_default == True, VideoTemplate.user_id == user_id),
            )
        )
        outro_template = result.scalar_one_or_none()
        if not outro_template:
            raise HTTPException(status_code=404, detail="Outro template not found")
        if outro_template.template_type != "outro":
            raise HTTPException(status_code=400, detail="Selected template is not an outro")

        outro_path = TEMPLATES_DIR / f"outro_{uuid.uuid4()}.mp4"
        _generate_branding_video(outro_template, target_w, target_h, outro_path)

    # Build the concatenation sequence: [intro] + content + [outro]
    segments = []
    if intro_path and intro_path.exists():
        segments.append(intro_path)
    segments.append(content_path)
    if outro_path and outro_path.exists():
        segments.append(outro_path)

    # Compose the final video
    output_filename = f"branded_{uuid.uuid4()}.mp4"
    output_path = COMPOSED_DIR / output_filename

    try:
        _concat_videos(segments, output_path, target_w, target_h)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Template application failed: {e}")
        raise HTTPException(status_code=500, detail=f"Video composition failed: {str(e)}")
    finally:
        # Clean up temporary branding videos
        if intro_path and intro_path.exists():
            try:
                intro_path.unlink()
            except Exception:
                pass
        if outro_path and outro_path.exists():
            try:
                outro_path.unlink()
            except Exception:
                pass

    # Verify output
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise HTTPException(status_code=500, detail="Composed video is empty or missing")

    # Extract metadata
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
        "intro_template": _template_to_dict(intro_template) if intro_template else None,
        "outro_template": _template_to_dict(outro_template) if outro_template else None,
        "content_asset_id": request.video_asset_id,
    }

    # Optionally save as a new asset
    if request.save_as_asset:
        # Build descriptive name
        parts = []
        if intro_template:
            parts.append(intro_template.name)
        parts.append(video_asset.original_filename or video_asset.filename)
        if outro_template:
            parts.append(outro_template.name)
        asset_name = " + ".join(parts)

        new_asset = Asset(
            user_id=user_id,
            filename=output_filename,
            original_filename=f"branded_{asset_name}.mp4",
            file_path=f"/uploads/composed/{output_filename}",
            file_type="video/mp4",
            file_size=file_size,
            width=meta["width"] or target_w,
            height=meta["height"] or target_h,
            source="composed",
            category="video",
            tags=f"branded,intro_outro,{request.output_format}",
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


@router.post("/preview")
async def preview_branded_video(
    request: ApplyTemplateRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Preview what the branded video will look like (metadata only, no rendering).

    Returns estimated duration, segment breakdown, and template details.
    """
    # Fetch video asset
    result = await db.execute(
        select(Asset).where(Asset.id == request.video_asset_id, Asset.user_id == user_id)
    )
    video_asset = result.scalar_one_or_none()
    if not video_asset:
        raise HTTPException(status_code=404, detail="Video asset not found")

    segments = []
    total_duration = 0.0

    # Intro
    if request.intro_template_id:
        result = await db.execute(
            select(VideoTemplate).where(
                VideoTemplate.id == request.intro_template_id,
                or_(VideoTemplate.is_default == True, VideoTemplate.user_id == user_id),
            )
        )
        intro = result.scalar_one_or_none()
        if intro:
            segments.append({
                "type": "intro",
                "template": _template_to_dict(intro),
                "duration_seconds": intro.duration_seconds,
            })
            total_duration += intro.duration_seconds

    # Content
    content_duration = video_asset.duration_seconds or 0
    segments.append({
        "type": "content",
        "asset_id": video_asset.id,
        "filename": video_asset.original_filename or video_asset.filename,
        "duration_seconds": content_duration,
        "thumbnail_path": video_asset.thumbnail_path,
    })
    total_duration += content_duration

    # Outro
    if request.outro_template_id:
        result = await db.execute(
            select(VideoTemplate).where(
                VideoTemplate.id == request.outro_template_id,
                or_(VideoTemplate.is_default == True, VideoTemplate.user_id == user_id),
            )
        )
        outro = result.scalar_one_or_none()
        if outro:
            segments.append({
                "type": "outro",
                "template": _template_to_dict(outro),
                "duration_seconds": outro.duration_seconds,
            })
            total_duration += outro.duration_seconds

    # Account for crossfade transitions (0.3s each)
    transition_count = len(segments) - 1
    transition_overlap = transition_count * 0.3
    effective_duration = max(0, total_duration - transition_overlap)

    fmt = OUTPUT_FORMATS.get(request.output_format, OUTPUT_FORMATS["9:16"])

    return {
        "segments": segments,
        "segment_count": len(segments),
        "total_duration": round(total_duration, 2),
        "transition_overlap": round(transition_overlap, 2),
        "effective_duration": round(effective_duration, 2),
        "output_format": request.output_format,
        "output_width": fmt["width"],
        "output_height": fmt["height"],
    }
