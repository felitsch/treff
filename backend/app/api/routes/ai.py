"""AI Generation routes."""

import io
import os
import uuid
import logging
import base64
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.core.text_generator import generate_text_content, regenerate_single_field
from app.core.config import settings
from app.models.asset import Asset
from app.models.setting import Setting

router = APIRouter()
logger = logging.getLogger(__name__)

# Asset upload directory (same as assets.py)
APP_DIR = Path(__file__).resolve().parent.parent.parent
ASSETS_UPLOAD_DIR = APP_DIR / "static" / "uploads" / "assets"
ASSETS_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def asset_to_dict(asset: Asset) -> dict:
    """Convert Asset model to plain dict."""
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


async def _get_gemini_api_key(user_id: int, db: AsyncSession) -> str | None:
    """Get Gemini API key: first from user settings, then from env."""
    # Check user settings
    result = await db.execute(
        select(Setting).where(
            Setting.user_id == user_id, Setting.key == "gemini_api_key"
        )
    )
    setting = result.scalar_one_or_none()
    if setting and setting.value and setting.value.strip():
        return setting.value.strip()

    # Check environment
    if settings.GEMINI_API_KEY:
        return settings.GEMINI_API_KEY

    return None


async def _generate_with_gemini(
    prompt: str,
    api_key: str,
    width: int = 1024,
    height: int = 1024,
    aspect_ratio: str | None = None,
    image_size: str | None = None,
) -> bytes | None:
    """Try to generate an image using Nano Banana Pro (gemini-3-pro-image-preview).

    Supports aspect_ratio (e.g. '1:1', '9:16', '16:9') and
    image_size ('1K', '2K', '4K') for high-quality output.
    Falls back to gemini-2.0-flash-exp if gemini-3-pro-image-preview fails.
    Returns PNG bytes or None.
    """
    # Valid aspect ratios for Nano Banana Pro
    VALID_ASPECT_RATIOS = {"1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"}
    # Valid image sizes
    VALID_IMAGE_SIZES = {"1K", "2K", "4K"}

    # Default aspect ratio based on dimensions if not provided
    if not aspect_ratio:
        if width == height:
            aspect_ratio = "1:1"
        elif width > height:
            aspect_ratio = "16:9"
        else:
            aspect_ratio = "9:16"

    # Validate aspect_ratio
    if aspect_ratio not in VALID_ASPECT_RATIOS:
        aspect_ratio = "1:1"

    # Default image size
    if not image_size:
        image_size = "2K"

    # Validate image_size (must be uppercase K)
    image_size = image_size.upper().replace("k", "K") if image_size else "2K"
    if image_size not in VALID_IMAGE_SIZES:
        image_size = "2K"

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        # Try Nano Banana Pro (gemini-3-pro-image-preview) first — higher quality,
        # better text rendering, thinking mode, up to 4K resolution
        image_config = types.ImageConfig(
            aspectRatio=aspect_ratio,
            imageSize=image_size,
        )

        logger.info(
            f"Trying Nano Banana Pro (gemini-3-pro-image-preview) with "
            f"aspect_ratio={aspect_ratio}, image_size={image_size}"
        )

        response = client.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                responseModalities=["TEXT", "IMAGE"],
                imageConfig=image_config,
            ),
        )

        # Extract image using part.as_image() (new SDK method)
        if response.candidates:
            for part in response.candidates[0].content.parts:
                image = part.as_image()
                if image is not None and image.image_bytes:
                    logger.info("Nano Banana Pro image generation succeeded")
                    return image.image_bytes

        logger.warning("Nano Banana Pro returned no image, trying fallback model")

    except Exception as e:
        logger.warning(f"Nano Banana Pro (gemini-3-pro-image-preview) failed: {e}")

    # Fallback: try gemini-2.0-flash-exp (older model)
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        logger.info("Falling back to gemini-2.0-flash-exp for image generation")
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt,
            config=types.GenerateContentConfig(
                responseModalities=["IMAGE", "TEXT"],
            ),
        )

        # Extract image — try new as_image() first, then inline_data fallback
        if response.candidates:
            for part in response.candidates[0].content.parts:
                # Try new API (as_image returns types.Image with .image_bytes)
                image = part.as_image()
                if image is not None and image.image_bytes:
                    logger.info("gemini-2.0-flash-exp image generation succeeded (as_image)")
                    return image.image_bytes
                # Try legacy inline_data
                if hasattr(part, 'inline_data') and part.inline_data and hasattr(part.inline_data, 'mime_type'):
                    if part.inline_data.mime_type.startswith("image/"):
                        logger.info("gemini-2.0-flash-exp image generation succeeded (inline_data)")
                        return part.inline_data.data

        return None
    except Exception as e:
        logger.warning(f"Gemini fallback image generation also failed: {e}")
        return None


def _generate_placeholder_image(prompt: str, width: int = 1024, height: int = 1024) -> bytes:
    """Generate a branded placeholder image with the prompt theme using Pillow.

    Creates a visually appealing gradient image with TREFF branding
    that represents the AI-generated concept.
    """
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)

    # TREFF brand colors
    treff_blue = (59, 122, 177)  # #3B7AB1
    treff_yellow = (253, 208, 0)  # #FDD000
    dark_bg = (26, 26, 46)  # #1A1A2E

    # Determine theme colors based on prompt keywords
    prompt_lower = prompt.lower()
    if any(w in prompt_lower for w in ["usa", "american", "high school", "hallway"]):
        color1 = (30, 60, 120)  # Deep blue
        color2 = (180, 60, 40)  # Red accent
        accent = treff_yellow
    elif any(w in prompt_lower for w in ["canada", "kanada", "maple", "mountain"]):
        color1 = (120, 20, 20)  # Maple red
        color2 = (40, 80, 40)  # Forest green
        accent = (255, 255, 255)
    elif any(w in prompt_lower for w in ["australia", "australien", "sydney", "beach"]):
        color1 = (20, 100, 160)  # Ocean blue
        color2 = (200, 160, 60)  # Sandy gold
        accent = (255, 255, 255)
    elif any(w in prompt_lower for w in ["neuseeland", "new zealand", "green"]):
        color1 = (20, 80, 40)  # Deep green
        color2 = (60, 140, 180)  # Sky blue
        accent = (255, 255, 255)
    elif any(w in prompt_lower for w in ["ireland", "irland", "green"]):
        color1 = (20, 100, 50)  # Irish green
        color2 = (40, 60, 80)  # Celtic dark
        accent = treff_yellow
    else:
        color1 = dark_bg
        color2 = treff_blue
        accent = treff_yellow

    # Draw gradient background
    for y in range(height):
        ratio = y / height
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Add subtle geometric shapes for visual interest
    import random
    random.seed(hash(prompt) % 2**32)

    for _ in range(15):
        x = random.randint(0, width)
        y = random.randint(0, height)
        size = random.randint(40, 200)
        opacity_color = (
            min(255, color1[0] + 30),
            min(255, color1[1] + 30),
            min(255, color1[2] + 30),
        )
        shape_type = random.choice(["circle", "rect"])
        if shape_type == "circle":
            draw.ellipse(
                [x - size, y - size, x + size, y + size],
                fill=None,
                outline=opacity_color,
                width=2,
            )
        else:
            draw.rectangle(
                [x, y, x + size, y + size * 0.6],
                fill=None,
                outline=opacity_color,
                width=2,
            )

    # Apply a slight blur for atmosphere
    img = img.filter(ImageFilter.GaussianBlur(radius=2))
    draw = ImageDraw.Draw(img)

    # Add TREFF branding badge (top-left)
    badge_w, badge_h = 120, 40
    badge_x, badge_y = 30, 30
    draw.rounded_rectangle(
        [badge_x, badge_y, badge_x + badge_w, badge_y + badge_h],
        radius=8,
        fill=treff_blue,
    )

    # Try to use a font, fall back to default
    try:
        font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32)
        font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
        font_badge = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
        font_prompt = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
    except (OSError, IOError):
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
            font_badge = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
            font_prompt = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        except (OSError, IOError):
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
            font_badge = ImageFont.load_default()
            font_prompt = ImageFont.load_default()

    # Draw badge text
    draw.text(
        (badge_x + 15, badge_y + 8),
        "TREFF",
        fill=(255, 255, 255),
        font=font_badge,
    )

    # Add "AI Generated" label (top-right)
    ai_label = "KI-generiert"
    ai_label_w = 140
    draw.rounded_rectangle(
        [width - ai_label_w - 30, 30, width - 30, 70],
        radius=8,
        fill=(0, 0, 0, 128),
    )
    draw.text(
        (width - ai_label_w - 15, 38),
        ai_label,
        fill=accent,
        font=font_small,
    )

    # Add prompt text in center area (wrapped)
    prompt_display = prompt[:120] + ("..." if len(prompt) > 120 else "")
    # Simple word wrap
    words = prompt_display.split()
    lines = []
    current_line = ""
    max_chars_per_line = 35
    for word in words:
        if len(current_line) + len(word) + 1 <= max_chars_per_line:
            current_line = current_line + " " + word if current_line else word
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)

    # Draw prompt text with shadow
    text_y = height // 2 - (len(lines) * 28) // 2
    for line in lines:
        # Shadow
        draw.text((width // 2 - 2, text_y + 2), line, fill=(0, 0, 0), font=font_large, anchor="mt")
        # Text
        draw.text((width // 2, text_y), line, fill=(255, 255, 255), font=font_large, anchor="mt")
        text_y += 38

    # Add bottom bar with info
    bar_h = 60
    draw.rectangle([0, height - bar_h, width, height], fill=(0, 0, 0))
    draw.text(
        (20, height - bar_h + 18),
        f"Prompt: {prompt[:60]}{'...' if len(prompt) > 60 else ''}",
        fill=(180, 180, 180),
        font=font_prompt,
    )

    # Convert to PNG bytes
    buffer = io.BytesIO()
    img.save(buffer, format="PNG", quality=95)
    return buffer.getvalue()


@router.post("/generate-text")
async def generate_text(
    request: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Generate slide texts, captions, hashtags, CTA.

    Uses Gemini 2.5 Flash when an API key is available, with rule-based fallback.

    Expects:
    - category (str): Post category (e.g., laender_spotlight)
    - country (str, optional): Target country
    - topic (str, optional): Topic or subject
    - key_points (str, optional): Key points to include
    - tone (str, optional): jugendlich or serioess (default: jugendlich)
    - platform (str, optional): Target platform
    - slide_count (int, optional): Number of slides (default: 1)

    Returns structured content for all slides, captions, and hashtags.
    Includes 'source' field: "gemini" or "rule_based".
    """
    try:
        category = request.get("category", "laender_spotlight")
        country = request.get("country")
        topic = request.get("topic")
        key_points = request.get("key_points")
        tone = request.get("tone", "jugendlich")
        platform = request.get("platform", "instagram_feed")
        slide_count = request.get("slide_count", 1)

        if slide_count < 1:
            slide_count = 1
        if slide_count > 10:
            slide_count = 10

        # Get Gemini API key for AI-powered text generation
        api_key = await _get_gemini_api_key(user_id, db)

        result = generate_text_content(
            category=category,
            country=country,
            topic=topic,
            key_points=key_points,
            tone=tone,
            platform=platform,
            slide_count=slide_count,
            api_key=api_key,
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text generation failed: {str(e)}")


@router.post("/regenerate-field")
async def regenerate_field(
    request: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Regenerate a single text field without changing other content.

    Uses Gemini 2.5 Flash when an API key is available, with rule-based fallback.

    Expects:
    - field (str): Which field to regenerate (headline, subheadline, body_text,
      cta_text, caption_instagram, caption_tiktok, hashtags_instagram, hashtags_tiktok)
    - category (str): Post category
    - country (str, optional): Target country
    - topic (str, optional): Topic
    - key_points (str, optional): Key points
    - tone (str, optional): jugendlich or serioess
    - platform (str, optional): Target platform
    - slide_index (int, optional): Which slide to regenerate for (default: 0)
    - slide_count (int, optional): Total number of slides (default: 1)
    - current_headline (str, optional): Current headline for caption context
    - current_body (str, optional): Current body text for caption context

    Returns:
    - field: name of the regenerated field
    - value: new value for that field
    """
    try:
        field = request.get("field")
        if not field:
            raise HTTPException(status_code=400, detail="Field parameter is required")

        valid_fields = [
            "headline", "subheadline", "body_text", "cta_text",
            "caption_instagram", "caption_tiktok",
            "hashtags_instagram", "hashtags_tiktok",
        ]
        if field not in valid_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid field '{field}'. Must be one of: {', '.join(valid_fields)}"
            )

        # Get Gemini API key for AI-powered field regeneration
        api_key = await _get_gemini_api_key(user_id, db)

        result = regenerate_single_field(
            field=field,
            category=request.get("category", "laender_spotlight"),
            country=request.get("country"),
            topic=request.get("topic"),
            key_points=request.get("key_points"),
            tone=request.get("tone", "jugendlich"),
            platform=request.get("platform", "instagram_feed"),
            slide_index=request.get("slide_index", 0),
            slide_count=request.get("slide_count", 1),
            current_headline=request.get("current_headline"),
            current_body=request.get("current_body"),
            api_key=api_key,
        )

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Field regeneration failed: {str(e)}")


@router.post("/generate-image")
async def generate_image(
    request: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Generate image via AI (Nano Banana Pro / Gemini API or local fallback).

    Expects:
    - prompt (str): Image description / prompt
    - width (int, optional): Image width in pixels (default: 1024)
    - height (int, optional): Image height in pixels (default: 1024)
    - aspect_ratio (str, optional): Aspect ratio for Nano Banana Pro
      (e.g. '1:1', '9:16', '16:9', '3:4', '4:3'). Default: auto from width/height.
    - image_size (str, optional): Output resolution for Nano Banana Pro
      ('1K', '2K', '4K'). Default: '2K'.
    - category (str, optional): Asset category for library
    - country (str, optional): Country tag for the image

    Returns:
    - status: "success"
    - image_url: URL to access the generated image
    - asset: Full asset object stored in the library
    - source: "gemini" or "local_generated"
    """
    prompt = request.get("prompt", "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt darf nicht leer sein.")

    if len(prompt) > 500:
        raise HTTPException(status_code=400, detail="Prompt darf maximal 500 Zeichen lang sein.")

    req_width = min(max(request.get("width", 1024), 256), 4096)
    req_height = min(max(request.get("height", 1024), 256), 4096)
    aspect_ratio = request.get("aspect_ratio")  # e.g. "1:1", "9:16", "16:9"
    image_size = request.get("image_size")  # e.g. "1K", "2K", "4K"
    category = request.get("category", "ai_generated")
    country = request.get("country")

    image_bytes = None
    source = "local_generated"

    # Try Gemini API first (Nano Banana Pro with fallback to Flash)
    api_key = await _get_gemini_api_key(user_id, db)
    if api_key:
        logger.info(f"Attempting Gemini image generation for prompt: {prompt[:50]}...")
        image_bytes = await _generate_with_gemini(
            prompt, api_key, req_width, req_height,
            aspect_ratio=aspect_ratio,
            image_size=image_size,
        )
        if image_bytes:
            source = "gemini"
            logger.info("Gemini image generation succeeded")
        else:
            logger.info("Gemini failed, falling back to local generation")

    # Fallback: generate a branded placeholder image
    if not image_bytes:
        logger.info(f"Generating local branded image for: {prompt[:50]}...")
        image_bytes = _generate_placeholder_image(prompt, req_width, req_height)

    # Save image to disk and database with proper error handling
    try:
        unique_filename = f"ai_{uuid.uuid4().hex[:12]}.png"
        file_path = ASSETS_UPLOAD_DIR / unique_filename

        with open(file_path, "wb") as f:
            f.write(image_bytes)

        # Get dimensions
        img = Image.open(io.BytesIO(image_bytes))
        width, height = img.size

        # Save to asset library
        asset = Asset(
            user_id=user_id,
            filename=unique_filename,
            original_filename=f"AI: {prompt[:80]}",
            file_path=f"/uploads/assets/{unique_filename}",
            file_type="image/png",
            file_size=len(image_bytes),
            width=width,
            height=height,
            source="ai_generated",
            ai_prompt=prompt,
            category=category,
            country=country,
            tags="ai,generated",
        )
        db.add(asset)
        await db.flush()
        await db.refresh(asset)

        asset_data = asset_to_dict(asset)

        return {
            "status": "success",
            "image_url": f"/api/uploads/assets/{unique_filename}",
            "asset": asset_data,
            "source": source,
            "message": "Bild erfolgreich generiert!" if source == "gemini" else "Bild generiert (lokale Vorschau - fuer KI-Bilder Gemini API-Key in Einstellungen hinterlegen)",
        }
    except OSError as e:
        logger.error(f"Failed to save AI-generated image to disk: {e}")
        raise HTTPException(
            status_code=500,
            detail="Das generierte Bild konnte nicht gespeichert werden. Bitte versuche es erneut.",
        )
    except Exception as e:
        logger.error(f"Failed to store AI-generated image in database: {e}")
        raise HTTPException(
            status_code=500,
            detail="Beim Speichern des generierten Bildes ist ein Fehler aufgetreten. Bitte versuche es erneut.",
        )


@router.post("/edit-image")
async def edit_image(
    request: dict,
    user_id: int = Depends(get_current_user_id),
):
    """Edit existing image via natural language."""
    return {
        "status": "api_key_required",
        "message": "Bildbearbeitung benoetigt einen Gemini API-Key. Bitte in den Einstellungen konfigurieren.",
    }


@router.post("/suggest-content")
async def suggest_content(
    request: dict,
    user_id: int = Depends(get_current_user_id),
):
    """Get content suggestions for calendar."""
    return {
        "status": "api_key_required",
        "message": "Content-Vorschlaege benoetigen einen Gemini API-Key.",
    }


@router.post("/suggest-weekly-plan")
async def suggest_weekly_plan(
    request: dict,
    user_id: int = Depends(get_current_user_id),
):
    """Generate full week content plan."""
    return {
        "status": "api_key_required",
        "message": "Wochenplan-Vorschlaege benoetigen einen Gemini API-Key.",
    }
