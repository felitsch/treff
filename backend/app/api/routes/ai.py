"""AI Generation routes."""

import io
import os
import json
import uuid
import logging
import base64
from datetime import datetime, timezone, timedelta, date
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.core.text_generator import generate_text_content, regenerate_single_field
from app.core.config import settings
from app.core.rate_limiter import ai_rate_limiter
from app.models.asset import Asset
from app.models.setting import Setting
from app.models.post import Post
from app.models.content_suggestion import ContentSuggestion

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
    # Rate limit check (raises 429 if exceeded)
    ai_rate_limiter.check_rate_limit(user_id, "generate-text")

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
    # Rate limit check (raises 429 if exceeded)
    ai_rate_limiter.check_rate_limit(user_id, "regenerate-field")

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
    # Rate limit check (raises 429 if exceeded)
    ai_rate_limiter.check_rate_limit(user_id, "generate-image")

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


# ── TREFF Seasonal Calendar for Content Suggestions ──

TREFF_SEASONAL_CALENDAR = [
    # Bewerbungsfristen (Application Deadlines)
    {"month": 3, "day": 31, "label": "Bewerbungsfrist USA Classic", "country": "usa", "type": "bewerbungsfrist"},
    {"month": 4, "day": 15, "label": "Bewerbungsfrist USA Select", "country": "usa", "type": "bewerbungsfrist"},
    {"month": 4, "day": 30, "label": "Bewerbungsfrist Kanada", "country": "canada", "type": "bewerbungsfrist"},
    {"month": 5, "day": 15, "label": "Bewerbungsfrist Irland", "country": "ireland", "type": "bewerbungsfrist"},
    {"month": 5, "day": 31, "label": "Bewerbungsfrist Australien/Neuseeland", "country": "australia", "type": "bewerbungsfrist"},
    {"month": 10, "day": 15, "label": "Stipendien-Bewerbungsfrist", "country": None, "type": "stipendium"},
    # Abflugzeiten (Departure Periods)
    {"month": 8, "day": 15, "label": "Abflug USA/Kanada/Irland", "country": "usa", "type": "abflugzeit"},
    {"month": 1, "day": 20, "label": "Abflug Australien/Neuseeland", "country": "australia", "type": "abflugzeit"},
    # Schuljahresbeginn
    {"month": 9, "day": 1, "label": "Schulstart USA/Kanada/Irland", "country": "usa", "type": "schuljahresbeginn"},
    {"month": 2, "day": 1, "label": "Schulstart Australien/Neuseeland", "country": "australia", "type": "schuljahresbeginn"},
    # Rueckkehr
    {"month": 6, "day": 15, "label": "Rueckkehr USA/Kanada/Irland", "country": "usa", "type": "rueckkehr"},
    {"month": 12, "day": 10, "label": "Rueckkehr Australien/Neuseeland", "country": "australia", "type": "rueckkehr"},
    # Messen
    {"month": 11, "day": 1, "label": "JuBi Messe Herbst", "country": None, "type": "messe"},
    {"month": 3, "day": 1, "label": "JuBi Messe Fruehling", "country": None, "type": "messe"},
]

SEASON_NAMES = {
    12: "Winter", 1: "Winter", 2: "Winter",
    3: "Fruehling", 4: "Fruehling", 5: "Fruehling",
    6: "Sommer", 7: "Sommer", 8: "Sommer",
    9: "Herbst", 10: "Herbst", 11: "Herbst",
}

COUNTRY_NAMES = {
    "usa": "USA",
    "canada": "Kanada",
    "australia": "Australien",
    "newzealand": "Neuseeland",
    "ireland": "Irland",
}

ALL_COUNTRIES = ["usa", "canada", "australia", "newzealand", "ireland"]
ALL_CATEGORIES = [
    "laender_spotlight", "erfahrungsberichte", "infografiken",
    "fristen_cta", "tipps_tricks", "faq", "foto_posts",
]

CATEGORY_DISPLAY = {
    "laender_spotlight": "Laender-Spotlight",
    "erfahrungsberichte": "Erfahrungsbericht",
    "infografiken": "Infografik",
    "fristen_cta": "Fristen/CTA",
    "tipps_tricks": "Tipps & Tricks",
    "faq": "FAQ",
    "foto_posts": "Foto-Post",
}


def _get_upcoming_deadlines(today: date, lookahead_days: int = 60) -> list[dict]:
    """Get TREFF deadlines within the next N days."""
    upcoming = []
    for marker in TREFF_SEASONAL_CALENDAR:
        try:
            marker_date = date(today.year, marker["month"], marker["day"])
        except ValueError:
            continue
        # If the date has passed this year, check next year
        if marker_date < today:
            try:
                marker_date = date(today.year + 1, marker["month"], marker["day"])
            except ValueError:
                continue
        days_until = (marker_date - today).days
        if 0 <= days_until <= lookahead_days:
            upcoming.append({
                **marker,
                "date": marker_date,
                "days_until": days_until,
            })
    upcoming.sort(key=lambda x: x["days_until"])
    return upcoming


def _generate_suggestions_rule_based(
    today: date,
    recent_categories: list[str],
    recent_countries: list[str],
) -> list[dict]:
    """Generate content suggestions using rule-based logic (fallback when no API key)."""
    import random
    suggestions = []
    season = SEASON_NAMES.get(today.month, "")

    # 1. Seasonal suggestions based on upcoming deadlines
    upcoming = _get_upcoming_deadlines(today, lookahead_days=45)
    for deadline in upcoming[:2]:
        days_until = deadline["days_until"]
        dl_type = deadline["type"]
        country = deadline.get("country")
        country_name = COUNTRY_NAMES.get(country, "") if country else ""

        if dl_type == "bewerbungsfrist":
            title = f"Bewerbungsfrist {country_name} naht!"
            desc = (
                f"Nur noch {days_until} Tage bis zur Bewerbungsfrist "
                f"fuer {country_name}. Jetzt einen Reminder-Post erstellen!"
            )
            category = "fristen_cta"
            reason = f"Bewerbungsfrist {deadline['label']} am {deadline['date'].strftime('%d.%m.%Y')} – {days_until} Tage verbleibend"
        elif dl_type == "abflugzeit":
            title = f"Abflug-Countdown: Bald geht's los!"
            desc = (
                f"In {days_until} Tagen fliegen die TREFF-Schueler Richtung {country_name} ab. "
                f"Perfekt fuer einen emotionalen Abschiedspost oder Packliste!"
            )
            category = "tipps_tricks"
            reason = f"{deadline['label']} am {deadline['date'].strftime('%d.%m.%Y')} – motivierender Content"
        elif dl_type == "schuljahresbeginn":
            title = f"Schulstart {country_name} – Neue Abenteuer!"
            desc = (
                f"Das Schuljahr in {country_name} beginnt bald. "
                f"Teile Erfahrungsberichte oder Tipps fuer den ersten Schultag!"
            )
            category = "erfahrungsberichte"
            reason = f"{deadline['label']} – perfekter Zeitpunkt fuer Schulstart-Content"
        elif dl_type == "rueckkehr":
            title = f"Willkommen zurueck! Rueckkehr-Season"
            desc = (
                f"Die Austauschschueler kommen bald zurueck. "
                f"Zeit fuer Willkommens-Posts und Erfahrungsberichte!"
            )
            category = "erfahrungsberichte"
            reason = f"{deadline['label']} am {deadline['date'].strftime('%d.%m.%Y')}"
        elif dl_type == "stipendium":
            title = "Stipendien-Bewerbung: Jetzt informieren!"
            desc = (
                "Die Stipendien-Bewerbungsfrist naht. "
                "Erstelle einen Post ueber TREFF-Stipendien und Teilstipendien."
            )
            category = "fristen_cta"
            country = None
            reason = f"Stipendien-Frist am {deadline['date'].strftime('%d.%m.%Y')}"
        elif dl_type == "messe":
            title = f"{deadline['label']} – TREFF vor Ort!"
            desc = (
                f"Die JuBi Messe steht an! "
                f"Erstelle einen Ankuendigungs-Post und lade Interessenten ein."
            )
            category = "fristen_cta"
            country = None
            reason = f"Messe-Termin am {deadline['date'].strftime('%d.%m.%Y')}"
        else:
            continue

        suggestions.append({
            "suggestion_type": "seasonal",
            "title": title,
            "description": desc,
            "suggested_category": category,
            "suggested_country": country,
            "suggested_date": (today + timedelta(days=min(days_until - 7, 3) if days_until > 10 else 1)).isoformat(),
            "reason": reason,
        })

    # 2. Country rotation: suggest underrepresented countries
    country_counts = {}
    for c in ALL_COUNTRIES:
        country_counts[c] = recent_countries.count(c)
    least_used = sorted(ALL_COUNTRIES, key=lambda c: country_counts[c])
    for country in least_used[:1]:
        country_name = COUNTRY_NAMES.get(country, country)
        suggestions.append({
            "suggestion_type": "country_rotation",
            "title": f"{country_name}-Spotlight: Zeige die Vielfalt!",
            "description": (
                f"In letzter Zeit gab es wenig Content ueber {country_name}. "
                f"Ein Laender-Spotlight oder Fakten-Post waere perfekt!"
            ),
            "suggested_category": "laender_spotlight",
            "suggested_country": country,
            "suggested_date": (today + timedelta(days=2)).isoformat(),
            "reason": f"{country_name} ist unterrepraesentiert in deinen letzten Posts",
        })

    # 3. Category balance: suggest underrepresented categories
    cat_counts = {}
    for c in ALL_CATEGORIES:
        cat_counts[c] = recent_categories.count(c)
    least_used_cat = sorted(ALL_CATEGORIES, key=lambda c: cat_counts[c])
    for cat in least_used_cat[:1]:
        cat_name = CATEGORY_DISPLAY.get(cat, cat)
        random_country = random.choice(ALL_COUNTRIES)
        suggestions.append({
            "suggestion_type": "category_balance",
            "title": f"Mehr {cat_name}-Content erstellen",
            "description": (
                f"Die Kategorie '{cat_name}' wurde in letzter Zeit selten genutzt. "
                f"Abwechslung im Content-Mix sorgt fuer besseres Engagement!"
            ),
            "suggested_category": cat,
            "suggested_country": random_country,
            "suggested_date": (today + timedelta(days=3)).isoformat(),
            "reason": f"Kategorie '{cat_name}' braucht mehr Beitraege fuer eine ausgewogene Content-Strategie",
        })

    # 4. Seasonal / general suggestion based on time of year
    season_suggestions = {
        "Winter": {
            "title": "Wintertraeume: Highschool im Schnee",
            "desc": "Zeige winterliche Highschool-Szenen und motiviere zur Bewerbung fuers naechste Jahr!",
            "category": "foto_posts",
        },
        "Fruehling": {
            "title": "Fruehlings-Aufbruch: Neues Schuljahr planen",
            "desc": "Perfekte Zeit, um Bewerbungs-Tipps und Packlisten zu teilen!",
            "category": "tipps_tricks",
        },
        "Sommer": {
            "title": "Sommerfeeling: Abenteuer im Ausland",
            "desc": "Zeige das Sommer-Feeling an auslaendischen High Schools – perfekt fuer Fernweh-Content!",
            "category": "foto_posts",
        },
        "Herbst": {
            "title": "Back to School: Herbst-Motivation",
            "desc": "Schulstart-Content, Erfahrungsberichte und Bewerbungs-Erinnerungen fuer den Herbst!",
            "category": "erfahrungsberichte",
        },
    }
    season_data = season_suggestions.get(season, season_suggestions["Fruehling"])
    suggestions.append({
        "suggestion_type": "seasonal",
        "title": season_data["title"],
        "description": season_data["desc"],
        "suggested_category": season_data["category"],
        "suggested_country": random.choice(ALL_COUNTRIES),
        "suggested_date": (today + timedelta(days=4)).isoformat(),
        "reason": f"Saisonaler Content-Vorschlag fuer {season}",
    })

    return suggestions[:5]  # Max 5 suggestions


async def _generate_suggestions_with_gemini(
    api_key: str,
    today: date,
    season: str,
    upcoming_deadlines: list[dict],
    recent_categories: list[str],
    recent_countries: list[str],
) -> list[dict] | None:
    """Generate content suggestions using Gemini 2.5 Flash.

    Returns a list of suggestion dicts or None if generation fails.
    """
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        # Build deadlines context
        deadlines_text = ""
        for dl in upcoming_deadlines[:6]:
            deadlines_text += (
                f"- {dl['label']} am {dl['date'].strftime('%d.%m.%Y')} "
                f"(in {dl['days_until']} Tagen)\n"
            )
        if not deadlines_text:
            deadlines_text = "Keine unmittelbar bevorstehenden Fristen.\n"

        # Build recent content context
        recent_cats_str = ", ".join(recent_categories[:10]) if recent_categories else "Keine bisherigen Posts"
        recent_countries_str = ", ".join(recent_countries[:10]) if recent_countries else "Keine Laender-Posts"

        system_prompt = """Du bist der Content-Strategie-Assistent fuer TREFF Sprachreisen, einen deutschen Anbieter von Highschool-Aufenthalten im Ausland (USA, Kanada, Australien, Neuseeland, Irland).

Deine Aufgabe ist es, 3-5 konkrete Content-Vorschlaege fuer Social Media (Instagram & TikTok) zu generieren. Jeder Vorschlag soll:
- Zum aktuellen Datum und zur Jahreszeit passen
- Bevorstehende TREFF-Fristen und Events beruecksichtigen
- Die Vielfalt im Content-Mix foerdern (verschiedene Laender und Kategorien)
- Auf Deutsch sein und zum TREFF-Markenton passen (jugendlich aber serioees)

Verfuegbare Kategorien: laender_spotlight, erfahrungsberichte, infografiken, fristen_cta, tipps_tricks, faq, foto_posts
Verfuegbare Laender: usa, canada, australia, newzealand, ireland

Vorschlagstypen:
- "seasonal": Saisonale/zeitbezogene Vorschlaege (Fristen, Jahreszeit)
- "country_rotation": Vorschlaege fuer unterrepraesentierte Laender
- "category_balance": Vorschlaege fuer unterrepraesentierte Kategorien
- "gap_fill": Vorschlaege zum Fuellen von Content-Luecken"""

        content_prompt = f"""Generiere 3-5 Content-Vorschlaege fuer TREFF Sprachreisen.

AKTUELLES DATUM: {today.strftime('%d.%m.%Y')} ({today.strftime('%A')})
JAHRESZEIT: {season}

BEVORSTEHENDE TREFF-FRISTEN UND EVENTS:
{deadlines_text}

LETZTE POST-KATEGORIEN (der letzten 20 Posts):
{recent_cats_str}

LETZTE POST-LAENDER (der letzten 20 Posts):
{recent_countries_str}

Antworte ausschliesslich im folgenden JSON-Format (kein Markdown, keine Erklaerungen):
{{
  "suggestions": [
    {{
      "suggestion_type": "seasonal|country_rotation|category_balance|gap_fill",
      "title": "Kurzer, praegnanter Titel (max 80 Zeichen)",
      "description": "Beschreibung des Vorschlags mit konkreten Ideen (1-2 Saetze)",
      "suggested_category": "laender_spotlight|erfahrungsberichte|infografiken|fristen_cta|tipps_tricks|faq|foto_posts",
      "suggested_country": "usa|canada|australia|newzealand|ireland|null",
      "suggested_date": "YYYY-MM-DD",
      "reason": "Begruendung warum jetzt (Bezug auf Fristen, Jahreszeit oder Content-Mix)"
    }}
  ]
}}"""

        logger.info("Generating content suggestions with Gemini 2.5 Flash...")

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=content_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                temperature=0.9,
                max_output_tokens=4096,
            ),
        )

        response_text = response.text.strip()

        # Handle potential markdown code fences
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            response_text = "\n".join(lines)

        result = json.loads(response_text)

        if not isinstance(result, dict) or "suggestions" not in result:
            logger.warning("Gemini suggestions response missing 'suggestions' key")
            return None

        suggestions = result["suggestions"]
        if not isinstance(suggestions, list) or len(suggestions) == 0:
            logger.warning("Gemini returned empty suggestions list")
            return None

        # Validate and normalize each suggestion
        valid_suggestions = []
        for s in suggestions[:5]:
            if not isinstance(s, dict):
                continue
            if not s.get("title"):
                continue

            # Normalize fields
            stype = s.get("suggestion_type", "seasonal")
            if stype not in ("seasonal", "country_rotation", "category_balance", "gap_fill"):
                stype = "seasonal"

            cat = s.get("suggested_category", "laender_spotlight")
            if cat not in ALL_CATEGORIES:
                cat = "laender_spotlight"

            country = s.get("suggested_country")
            if country and country not in ALL_COUNTRIES:
                country = None
            # Handle string "null" from JSON
            if country == "null" or country == "":
                country = None

            # Parse date
            suggested_date = None
            date_str = s.get("suggested_date")
            if date_str:
                try:
                    suggested_date = date_str
                except Exception:
                    suggested_date = (today + timedelta(days=2)).isoformat()
            else:
                suggested_date = (today + timedelta(days=2)).isoformat()

            valid_suggestions.append({
                "suggestion_type": stype,
                "title": s["title"][:120],
                "description": (s.get("description") or "")[:500],
                "suggested_category": cat,
                "suggested_country": country,
                "suggested_date": suggested_date,
                "reason": (s.get("reason") or "")[:300],
            })

        if valid_suggestions:
            logger.info(f"Gemini generated {len(valid_suggestions)} content suggestions")
            return valid_suggestions

        return None

    except Exception as e:
        logger.warning(f"Gemini content suggestion generation failed: {e}")
        return None


@router.post("/suggest-content")
async def suggest_content(
    request: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Generate AI-powered content suggestions based on season, TREFF calendar, and posting history.

    Uses Gemini 2.5 Flash when API key available, with intelligent rule-based fallback.

    Returns 3-5 content suggestions saved to the database, visible on the Dashboard.
    """
    today = date.today()
    season = SEASON_NAMES.get(today.month, "Fruehling")

    # Get recent posts for context (last 20)
    recent_result = await db.execute(
        select(Post.category, Post.country)
        .where(Post.user_id == user_id)
        .order_by(Post.created_at.desc())
        .limit(20)
    )
    recent_posts = recent_result.all()
    recent_categories = [r[0] for r in recent_posts if r[0]]
    recent_countries = [r[1] for r in recent_posts if r[1]]

    # Get upcoming deadlines
    upcoming_deadlines = _get_upcoming_deadlines(today, lookahead_days=60)

    # Try Gemini first, fall back to rule-based
    api_key = await _get_gemini_api_key(user_id, db)
    source = "rule_based"
    suggestion_dicts = None

    if api_key:
        suggestion_dicts = await _generate_suggestions_with_gemini(
            api_key=api_key,
            today=today,
            season=season,
            upcoming_deadlines=upcoming_deadlines,
            recent_categories=recent_categories,
            recent_countries=recent_countries,
        )
        if suggestion_dicts:
            source = "gemini"

    # Fallback to rule-based suggestions
    if not suggestion_dicts:
        suggestion_dicts = _generate_suggestions_rule_based(
            today=today,
            recent_categories=recent_categories,
            recent_countries=recent_countries,
        )

    # Save suggestions to database
    saved_suggestions = []
    for s in suggestion_dicts:
        # Parse the suggested_date
        suggested_date_val = None
        if s.get("suggested_date"):
            try:
                suggested_date_val = date.fromisoformat(s["suggested_date"])
            except (ValueError, TypeError):
                suggested_date_val = today + timedelta(days=2)

        suggestion = ContentSuggestion(
            suggestion_type=s["suggestion_type"],
            title=s["title"],
            description=s.get("description"),
            suggested_category=s.get("suggested_category"),
            suggested_country=s.get("suggested_country"),
            suggested_date=suggested_date_val,
            reason=s.get("reason"),
            status="pending",
        )
        db.add(suggestion)
        await db.flush()
        await db.refresh(suggestion)

        saved_suggestions.append({
            "id": suggestion.id,
            "suggestion_type": suggestion.suggestion_type,
            "title": suggestion.title,
            "description": suggestion.description,
            "suggested_category": suggestion.suggested_category,
            "suggested_country": suggestion.suggested_country,
            "suggested_date": suggestion.suggested_date.isoformat() if suggestion.suggested_date else None,
            "reason": suggestion.reason,
            "status": suggestion.status,
            "created_at": suggestion.created_at.isoformat() if suggestion.created_at else None,
        })

    await db.commit()

    return {
        "status": "success",
        "source": source,
        "suggestions": saved_suggestions,
        "count": len(saved_suggestions),
        "message": f"{len(saved_suggestions)} Content-Vorschlaege generiert!",
    }


def _generate_weekly_plan_rule_based(
    today: date,
    recent_categories: list[str],
    recent_countries: list[str],
    recent_platforms: list[str],
    posts_per_week: int = 3,
) -> list[dict]:
    """Generate a rule-based weekly content plan as fallback when no API key is available.

    Creates a balanced content plan with varied countries, categories, platforms,
    and sensible posting times.
    """
    import random

    # Determine week days (Mon-Sun from next Monday)
    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    next_monday = today + timedelta(days=days_until_monday)

    # Optimal posting times for German teenagers (target audience)
    optimal_times = ["18:00", "19:00", "17:30", "20:00", "12:00"]

    # Platforms to rotate
    platforms = ["instagram_feed", "instagram_stories", "tiktok", "instagram_feed", "instagram_reels"]

    # Determine which countries/categories are underrepresented
    country_counts = {c: recent_countries.count(c) for c in ALL_COUNTRIES}
    sorted_countries = sorted(ALL_COUNTRIES, key=lambda c: country_counts.get(c, 0))

    cat_counts = {c: recent_categories.count(c) for c in ALL_CATEGORIES}
    sorted_categories = sorted(ALL_CATEGORIES, key=lambda c: cat_counts.get(c, 0))

    # Spread posts across the week (prefer Tue, Thu, Sat for 3 posts; more for higher counts)
    if posts_per_week <= 3:
        post_days = [1, 3, 5][:posts_per_week]  # Tue, Thu, Sat
    elif posts_per_week <= 5:
        post_days = [0, 1, 3, 4, 5][:posts_per_week]  # Mon, Tue, Thu, Fri, Sat
    else:
        post_days = list(range(min(posts_per_week, 7)))

    day_names_de = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]

    # Check upcoming deadlines for seasonal relevance
    upcoming = _get_upcoming_deadlines(today, lookahead_days=14)

    plan = []
    for i, day_offset in enumerate(post_days):
        post_date = next_monday + timedelta(days=day_offset)
        day_name = day_names_de[day_offset]

        # Pick category and country (rotate through underrepresented ones)
        category = sorted_categories[i % len(sorted_categories)]
        country = sorted_countries[i % len(sorted_countries)]
        platform = platforms[i % len(platforms)]
        time = optimal_times[i % len(optimal_times)]

        # If there's an upcoming deadline, override one post with fristen_cta
        if i == 0 and upcoming:
            dl = upcoming[0]
            category = "fristen_cta"
            country = dl.get("country") or country
            topic = f"{dl['label']} - {dl['days_until']} Tage verbleibend"
            reason = f"Bevorstehende Frist: {dl['label']} am {dl['date'].strftime('%d.%m.%Y')}"
        else:
            country_name = COUNTRY_NAMES.get(country, country)
            cat_name = CATEGORY_DISPLAY.get(category, category)

            topic_ideas = {
                "laender_spotlight": f"{country_name}-Spotlight: Highlights und Fakten",
                "erfahrungsberichte": f"Erfahrungsbericht aus {country_name}",
                "infografiken": f"Infografik: Highschool in {country_name} in Zahlen",
                "fristen_cta": f"Bewerbungsfristen fuer {country_name}",
                "tipps_tricks": f"Tipps fuer dein Auslandsjahr in {country_name}",
                "faq": f"FAQ: Haeufige Fragen zu {country_name}",
                "foto_posts": f"Foto-Impressionen aus {country_name}",
            }
            topic = topic_ideas.get(category, f"{cat_name} ueber {country_name}")
            reason = f"Abwechslung im Content-Mix: {cat_name} + {country_name} fuer ausgewogene Praesenz"

        plan.append({
            "day": day_name,
            "date": post_date.isoformat(),
            "time": time,
            "platform": platform,
            "category": category,
            "country": country,
            "topic": topic,
            "reason": reason,
        })

    return plan


async def _generate_weekly_plan_with_gemini(
    api_key: str,
    today: date,
    season: str,
    upcoming_deadlines: list[dict],
    recent_categories: list[str],
    recent_countries: list[str],
    recent_platforms: list[str],
    posts_per_week: int = 3,
) -> list[dict] | None:
    """Generate a weekly content plan using Gemini 2.5 Flash.

    Returns a list of planned post dicts, or None if generation fails.
    """
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        # Build deadlines context
        deadlines_text = ""
        for dl in upcoming_deadlines[:6]:
            deadlines_text += (
                f"- {dl['label']} am {dl['date'].strftime('%d.%m.%Y')} "
                f"(in {dl['days_until']} Tagen, Land: {COUNTRY_NAMES.get(dl.get('country', ''), 'allgemein')})\n"
            )
        if not deadlines_text:
            deadlines_text = "Keine unmittelbar bevorstehenden Fristen.\n"

        # Build recent content context
        recent_cats_str = ", ".join(recent_categories[:15]) if recent_categories else "Noch keine Posts vorhanden"
        recent_countries_str = ", ".join(recent_countries[:15]) if recent_countries else "Noch keine Laender-Posts"
        recent_platforms_str = ", ".join(recent_platforms[:10]) if recent_platforms else "Noch keine Plattform-Praeferenz"

        # Determine next week's dates
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_monday = today + timedelta(days=days_until_monday)
        next_sunday = next_monday + timedelta(days=6)

        system_prompt = """Du bist der Content-Strategie-Planer fuer TREFF Sprachreisen, einen deutschen Anbieter von Highschool-Aufenthalten im Ausland (USA, Kanada, Australien, Neuseeland, Irland).

Deine Aufgabe ist es, einen kompletten Wochenplan fuer Social Media (Instagram Feed, Instagram Stories, Instagram Reels, TikTok) zu erstellen. Der Plan soll:
- Einen optimalen Content-Mix bieten (verschiedene Laender und Kategorien abwechseln)
- Die Posting-Zeiten auf die Zielgruppe (deutsche Teenager 14-18 Jahre) optimieren: beste Zeiten sind 17:00-20:00 Uhr unter der Woche, 11:00-14:00 am Wochenende
- Bevorstehende TREFF-Fristen und Events beruecksichtigen
- Plattformen sinnvoll verteilen (nicht alles auf einer Plattform)
- NICHT mehrmals dasselbe Land oder dieselbe Kategorie direkt hintereinander

TREFF Sprachreisen:
- Gegruendet 1984 in Eningen u.A., Deutschland
- Highschool-Aufenthalte in: USA (ab 13.800 EUR), Kanada (ab 15.200 EUR), Australien (ab 18.900 EUR), Neuseeland (ab 19.500 EUR), Irland (ab 14.500 EUR)
- Ca. 200 Teilnehmer pro Jahr
- Zielgruppe: Schueler 14-18 + deren Eltern

Verfuegbare Kategorien: laender_spotlight, erfahrungsberichte, infografiken, fristen_cta, tipps_tricks, faq, foto_posts
Verfuegbare Laender: usa, canada, australia, newzealand, ireland
Verfuegbare Plattformen: instagram_feed, instagram_stories, instagram_reels, tiktok"""

        content_prompt = f"""Erstelle einen Wochenplan mit genau {posts_per_week} Posts fuer TREFF Sprachreisen.

PLANUNGSZEITRAUM: {next_monday.strftime('%d.%m.%Y')} (Montag) bis {next_sunday.strftime('%d.%m.%Y')} (Sonntag)
AKTUELLES DATUM: {today.strftime('%d.%m.%Y')} ({today.strftime('%A')})
JAHRESZEIT: {season}

BEVORSTEHENDE TREFF-FRISTEN UND EVENTS:
{deadlines_text}

LETZTE POST-KATEGORIEN (der letzten 20 Posts):
{recent_cats_str}

LETZTE POST-LAENDER (der letzten 20 Posts):
{recent_countries_str}

LETZTE POST-PLATTFORMEN:
{recent_platforms_str}

WICHTIGE REGELN:
- Verteile die {posts_per_week} Posts sinnvoll ueber die Woche (nicht alle an einem Tag)
- Vermeide es, dasselbe Land mehrmals direkt hintereinander zu planen
- Achte auf einen ausgewogenen Content-Mix (verschiedene Kategorien)
- Wenn eine Frist bevorsteht, plane einen fristen_cta Post ein
- Optimale Posting-Zeiten: Werktags 17:00-20:00, Wochenende 11:00-14:00
- Jeder Post braucht ein konkretes Topic (nicht nur die Kategorie)
- Alle Texte auf Deutsch

Antworte ausschliesslich im folgenden JSON-Format (kein Markdown, keine Erklaerungen):
{{
  "weekly_plan": [
    {{
      "day": "Montag|Dienstag|Mittwoch|Donnerstag|Freitag|Samstag|Sonntag",
      "date": "YYYY-MM-DD",
      "time": "HH:MM",
      "platform": "instagram_feed|instagram_stories|instagram_reels|tiktok",
      "category": "laender_spotlight|erfahrungsberichte|infografiken|fristen_cta|tipps_tricks|faq|foto_posts",
      "country": "usa|canada|australia|newzealand|ireland",
      "topic": "Konkretes Thema fuer den Post (1 Satz)",
      "reason": "Begruendung warum dieser Post an diesem Tag sinnvoll ist"
    }}
  ]
}}"""

        logger.info("Generating weekly plan with Gemini 2.5 Flash (%d posts)...", posts_per_week)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=content_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                temperature=0.8,
                max_output_tokens=4096,
            ),
        )

        response_text = response.text.strip()

        # Handle potential markdown code fences
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            response_text = "\n".join(lines)

        result = json.loads(response_text)

        if not isinstance(result, dict) or "weekly_plan" not in result:
            logger.warning("Gemini weekly plan response missing 'weekly_plan' key")
            return None

        plan = result["weekly_plan"]
        if not isinstance(plan, list) or len(plan) == 0:
            logger.warning("Gemini returned empty weekly plan")
            return None

        # Validate and normalize
        day_names = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
        valid_platforms = ["instagram_feed", "instagram_stories", "instagram_reels", "tiktok"]

        valid_entries = []
        for entry in plan[:posts_per_week]:
            if not isinstance(entry, dict):
                continue

            # Validate day
            day = entry.get("day", "Montag")
            if day not in day_names:
                day = "Montag"

            # Validate and parse date
            entry_date = entry.get("date", "")
            try:
                parsed_date = date.fromisoformat(entry_date)
                entry_date = parsed_date.isoformat()
            except (ValueError, TypeError):
                # Calculate date from day name
                day_idx = day_names.index(day)
                entry_date = (next_monday + timedelta(days=day_idx)).isoformat()

            # Validate time
            time_str = entry.get("time", "18:00")
            try:
                h, m = time_str.split(":")
                if not (0 <= int(h) <= 23 and 0 <= int(m) <= 59):
                    time_str = "18:00"
            except (ValueError, AttributeError):
                time_str = "18:00"

            # Validate platform
            platform = entry.get("platform", "instagram_feed")
            if platform not in valid_platforms:
                platform = "instagram_feed"

            # Validate category
            category = entry.get("category", "laender_spotlight")
            if category not in ALL_CATEGORIES:
                category = "laender_spotlight"

            # Validate country
            country = entry.get("country")
            if country and country not in ALL_COUNTRIES:
                country = "usa"
            if country == "null" or country == "" or country is None:
                country = "usa"

            valid_entries.append({
                "day": day,
                "date": entry_date,
                "time": time_str,
                "platform": platform,
                "category": category,
                "country": country,
                "topic": (entry.get("topic") or "")[:200],
                "reason": (entry.get("reason") or "")[:300],
            })

        if valid_entries:
            logger.info("Gemini generated weekly plan with %d posts", len(valid_entries))
            return valid_entries

        return None

    except Exception as e:
        logger.warning("Gemini weekly plan generation failed: %s", e)
        return None


@router.post("/suggest-weekly-plan")
async def suggest_weekly_plan(
    request: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Generate a complete weekly content plan using Gemini 2.5 Flash.

    Creates a balanced plan with 3-5 posts including optimal posting times,
    content mix (countries, categories), and platform distribution.

    Uses Gemini 2.5 Flash when API key is available, with rule-based fallback.

    Expects (all optional):
    - posts_per_week (int): Number of posts to plan (default: 3, min: 2, max: 7)

    Returns:
    - status: "success"
    - source: "gemini" or "rule_based"
    - weekly_plan: list of planned posts with day, date, time, platform, category, country, topic, reason
    - suggestions_saved: number of suggestions saved to the database
    - message: status message
    """
    today = date.today()
    season = SEASON_NAMES.get(today.month, "Fruehling")

    # Parse posts_per_week from request (clamp to 2-7)
    posts_per_week = request.get("posts_per_week", 3)
    try:
        posts_per_week = int(posts_per_week)
    except (TypeError, ValueError):
        posts_per_week = 3
    posts_per_week = max(2, min(7, posts_per_week))

    # Get recent posts for context (last 20)
    recent_result = await db.execute(
        select(Post.category, Post.country, Post.platform)
        .where(Post.user_id == user_id)
        .order_by(Post.created_at.desc())
        .limit(20)
    )
    recent_posts = recent_result.all()
    recent_categories = [r[0] for r in recent_posts if r[0]]
    recent_countries = [r[1] for r in recent_posts if r[1]]
    recent_platforms = [r[2] for r in recent_posts if r[2]]

    # Get upcoming deadlines
    upcoming_deadlines = _get_upcoming_deadlines(today, lookahead_days=30)

    # Try Gemini first, fall back to rule-based
    api_key = await _get_gemini_api_key(user_id, db)
    source = "rule_based"
    plan = None

    if api_key:
        plan = await _generate_weekly_plan_with_gemini(
            api_key=api_key,
            today=today,
            season=season,
            upcoming_deadlines=upcoming_deadlines,
            recent_categories=recent_categories,
            recent_countries=recent_countries,
            recent_platforms=recent_platforms,
            posts_per_week=posts_per_week,
        )
        if plan:
            source = "gemini"

    # Fallback to rule-based plan
    if not plan:
        plan = _generate_weekly_plan_rule_based(
            today=today,
            recent_categories=recent_categories,
            recent_countries=recent_countries,
            recent_platforms=recent_platforms,
            posts_per_week=posts_per_week,
        )

    # Validate content mix: check for too many duplicate countries
    if plan and len(plan) >= 3:
        countries_in_plan = [p["country"] for p in plan]
        from collections import Counter
        country_counter = Counter(countries_in_plan)
        # If any country appears more than 2 times, flag it
        has_good_mix = all(count <= 2 for count in country_counter.values())
        if not has_good_mix:
            logger.warning("Weekly plan has unbalanced country distribution: %s", country_counter)

    # Save each plan entry as a content suggestion to the database
    saved_count = 0
    for entry in plan:
        suggested_date_val = None
        if entry.get("date"):
            try:
                suggested_date_val = date.fromisoformat(entry["date"])
            except (ValueError, TypeError):
                suggested_date_val = today + timedelta(days=2)

        suggestion = ContentSuggestion(
            suggestion_type="weekly_plan",
            title=f"{entry.get('day', '')} {entry.get('time', '')} - {entry.get('topic', '')}"[:200],
            description=(
                f"Plattform: {entry.get('platform', '')} | "
                f"Kategorie: {CATEGORY_DISPLAY.get(entry.get('category', ''), entry.get('category', ''))} | "
                f"Land: {COUNTRY_NAMES.get(entry.get('country', ''), entry.get('country', ''))}\n"
                f"{entry.get('reason', '')}"
            )[:500],
            suggested_category=entry.get("category"),
            suggested_country=entry.get("country"),
            suggested_date=suggested_date_val,
            reason=entry.get("reason"),
            status="pending",
        )
        db.add(suggestion)
        saved_count += 1

    await db.commit()

    return {
        "status": "success",
        "source": source,
        "weekly_plan": plan,
        "suggestions_saved": saved_count,
        "posts_per_week": posts_per_week,
        "week_start": (today + timedelta(days=((7 - today.weekday()) % 7) or 7)).isoformat(),
        "message": f"Wochenplan mit {len(plan)} Posts generiert! ({source})",
    }
