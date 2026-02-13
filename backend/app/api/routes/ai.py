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
from app.models.humor_format import HumorFormat
from app.models.hook import Hook
from app.models.student import Student
from app.models.hashtag_set import HashtagSet

router = APIRouter()
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# Emoji-Regelwerk pro Ton (Emoji rules per tone)
# ═══════════════════════════════════════════════════════════════════════

EMOJI_RULES = {
    "jugendlich": {
        "count_range": (3, 6),
        "style": "begeisternd, aufrufend, jugendlich",
        "preferred_emojis": ["🔥", "✨", "🎉", "💪", "🙌", "😍", "🤩", "💯", "🚀", "🌍", "✈️", "🏫"],
        "country_emojis": {
            "usa": ["🇺🇸", "🏈", "🎓", "🗽", "🌉"],
            "canada": ["🇨🇦", "🍁", "🏔️", "🏒", "🐻"],
            "australia": ["🇦🇺", "🏄", "🐨", "🌊", "☀️"],
            "newzealand": ["🇳🇿", "🐑", "🏔️", "🌿", "🧗"],
            "ireland": ["🇮🇪", "☘️", "🏰", "🌧️", "🍀"],
        },
        "description": "Mehr Emojis, begeisternd, Feuer/Raketen/Sterne",
    },
    "serioess": {
        "count_range": (1, 3),
        "style": "professionell, zurueckhaltend",
        "preferred_emojis": ["📌", "📋", "✅", "📅", "🎓", "🌐", "📊", "🔑"],
        "country_emojis": {
            "usa": ["🇺🇸"], "canada": ["🇨🇦"], "australia": ["🇦🇺"],
            "newzealand": ["🇳🇿"], "ireland": ["🇮🇪"],
        },
        "description": "Weniger Emojis, professionell, Haekchen/Kalender",
    },
    "witzig": {
        "count_range": (4, 8),
        "style": "humorvoll, uebertrieben, ironisch",
        "preferred_emojis": ["😂", "🤣", "😅", "💀", "🙈", "😎", "🤡", "💅", "👀", "📢"],
        "country_emojis": {
            "usa": ["🇺🇸", "🍔", "🏈", "🗽"],
            "canada": ["🇨🇦", "🍁", "🦫", "🏒"],
            "australia": ["🇦🇺", "🦘", "🕷️", "🏄"],
            "newzealand": ["🇳🇿", "🐑", "🧝", "🌋"],
            "ireland": ["🇮🇪", "☘️", "🍺", "🌈"],
        },
        "description": "Viele Emojis, Lach-Emojis, uebertrieben",
    },
    "emotional": {
        "count_range": (3, 5),
        "style": "gefuehlvoll, herzlich, nostalgisch",
        "preferred_emojis": ["❤️", "🥺", "😢", "🤗", "💕", "🫶", "✨", "💫", "🌅", "🙏"],
        "country_emojis": {
            "usa": ["🇺🇸", "🌅", "🏠"], "canada": ["🇨🇦", "🏔️", "❄️"],
            "australia": ["🇦🇺", "🌊", "🌅"], "newzealand": ["🇳🇿", "🌿", "🌄"],
            "ireland": ["🇮🇪", "🏰", "🌧️"],
        },
        "description": "Herz-Emojis, emotionale Gesichter, Sonnenuntergang",
    },
    "motivierend": {
        "count_range": (3, 5),
        "style": "aufbauend, energetisch, inspirierend",
        "preferred_emojis": ["💪", "🔥", "🚀", "⭐", "🏆", "🎯", "✨", "👊", "🌟", "💥"],
        "country_emojis": {
            "usa": ["🇺🇸", "🗽", "🎓"], "canada": ["🇨🇦", "🏔️", "🍁"],
            "australia": ["🇦🇺", "🌊", "☀️"], "newzealand": ["🇳🇿", "🏔️", "🌿"],
            "ireland": ["🇮🇪", "☘️", "🏰"],
        },
        "description": "Power-Emojis, Raketen, Sterne, Feuer",
    },
    "informativ": {
        "count_range": (1, 3),
        "style": "sachlich, uebersichtlich",
        "preferred_emojis": ["📌", "📊", "💡", "ℹ️", "📋", "✅", "📎", "🔍"],
        "country_emojis": {
            "usa": ["🇺🇸"], "canada": ["🇨🇦"], "australia": ["🇦🇺"],
            "newzealand": ["🇳🇿"], "ireland": ["🇮🇪"],
        },
        "description": "Wenige, sachliche Emojis, Info-Icons",
    },
    "behind-the-scenes": {
        "count_range": (2, 4),
        "style": "authentisch, locker",
        "preferred_emojis": ["👀", "📸", "🎬", "🎥", "😊", "✌️", "🤫", "💬"],
        "country_emojis": {
            "usa": ["🇺🇸"], "canada": ["🇨🇦"], "australia": ["🇦🇺"],
            "newzealand": ["🇳🇿"], "ireland": ["🇮🇪"],
        },
        "description": "Behind-the-scenes Emojis, Kamera, authentisch",
    },
    "storytelling": {
        "count_range": (2, 4),
        "style": "erzaehlerisch, atmosphaerisch",
        "preferred_emojis": ["📖", "✨", "🌅", "🗺️", "💭", "🌍", "⏰", "🔮"],
        "country_emojis": {
            "usa": ["🇺🇸", "🗽", "🌉"], "canada": ["🇨🇦", "🍁", "🏔️"],
            "australia": ["🇦🇺", "🌊", "🐨"], "newzealand": ["🇳🇿", "🌿", "🏔️"],
            "ireland": ["🇮🇪", "☘️", "🏰"],
        },
        "description": "Story-Emojis, Buch, Globus, Sterne",
    },
    "provokant": {
        "count_range": (2, 5),
        "style": "mutig, kontrovers, scroll-stopping",
        "preferred_emojis": ["⚡", "🔥", "💣", "🤔", "👀", "📢", "💯", "🫣"],
        "country_emojis": {
            "usa": ["🇺🇸"], "canada": ["🇨🇦"], "australia": ["🇦🇺"],
            "newzealand": ["🇳🇿"], "ireland": ["🇮🇪"],
        },
        "description": "Provokante Emojis, Blitz, Feuer, Lautsprecher",
    },
    "wholesome": {
        "count_range": (3, 6),
        "style": "herzlich, warm, gemuetlich",
        "preferred_emojis": ["🥰", "🤗", "💛", "☀️", "🌻", "🏡", "👨‍👩‍👧‍👦", "🫶", "😊", "🌈"],
        "country_emojis": {
            "usa": ["🇺🇸", "🏠", "🍎"], "canada": ["🇨🇦", "🍁", "🐻"],
            "australia": ["🇦🇺", "🐨", "🌅"], "newzealand": ["🇳🇿", "🐑", "🌿"],
            "ireland": ["🇮🇪", "☘️", "🌈"],
        },
        "description": "Herz-Emojis, Sonnenblumen, Familie, warm",
    },
}

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
    - student_id (int, optional): If provided, load the student's personality_preset
      and use it to customize the AI generation tone and style.

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
        student_id = request.get("student_id")

        if slide_count < 1:
            slide_count = 1
        if slide_count > 10:
            slide_count = 10

        # Look up student personality preset if student_id is provided
        personality_preset = None
        if student_id:
            result_q = await db.execute(
                select(Student).where(
                    Student.id == student_id, Student.user_id == user_id
                )
            )
            student = result_q.scalar_one_or_none()
            if student and student.personality_preset:
                try:
                    personality_preset = json.loads(student.personality_preset)
                    # Inject the student name into the preset for third-person perspective
                    if personality_preset and "student_name" not in personality_preset:
                        personality_preset["student_name"] = student.name
                    logger.info(
                        "Loaded personality preset for student %s (id=%d): tone=%s, humor_level=%s",
                        student.name, student.id,
                        personality_preset.get("tone", "N/A"),
                        personality_preset.get("humor_level", "N/A"),
                    )
                except (json.JSONDecodeError, TypeError):
                    logger.warning("Invalid personality_preset JSON for student %d", student_id)

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
            personality_preset=personality_preset,
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


# Platform-to-aspect-ratio mapping for automatic ratio selection
PLATFORM_ASPECT_RATIOS = {
    "instagram_feed": "1:1",
    "instagram_story": "9:16",
    "instagram_stories": "9:16",
    "instagram_reels": "9:16",
    "tiktok": "9:16",
    "youtube": "16:9",
}

# Platform-to-dimension mapping for placeholder image generation
PLATFORM_DIMENSIONS = {
    "instagram_feed": (1024, 1024),
    "instagram_story": (1024, 1820),
    "instagram_stories": (1024, 1820),
    "instagram_reels": (1024, 1820),
    "tiktok": (1024, 1820),
    "youtube": (1920, 1080),
}


@router.post("/generate-image")
async def generate_image(
    request: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Generate image via AI (Nano Banana Pro / Gemini API or local fallback).

    Expects:
    - prompt (str): Image description / prompt
    - platform (str, optional): Target platform for automatic aspect ratio.
      Supported: instagram_feed (1:1), instagram_story (9:16), instagram_stories (9:16),
      instagram_reels (9:16), tiktok (9:16), youtube (16:9).
    - aspect_ratio (str, optional): Manual aspect ratio override. Takes precedence
      over platform if both are provided. (e.g. '1:1', '9:16', '16:9', '3:4', '4:3')
    - width (int, optional): Image width in pixels (default: based on platform or 1024)
    - height (int, optional): Image height in pixels (default: based on platform or 1024)
    - image_size (str, optional): Output resolution for Nano Banana Pro
      ('1K', '2K', '4K'). Default: '2K'.
    - category (str, optional): Asset category for library
    - country (str, optional): Country tag for the image

    Returns:
    - status: "success"
    - image_url: URL to access the generated image
    - asset: Full asset object stored in the library
    - source: "gemini" or "local_generated"
    - aspect_ratio: The aspect ratio used for generation
    - platform: The platform used (if provided)
    """
    # Rate limit check (raises 429 if exceeded)
    ai_rate_limiter.check_rate_limit(user_id, "generate-image")

    prompt = request.get("prompt", "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt darf nicht leer sein.")

    if len(prompt) > 500:
        raise HTTPException(status_code=400, detail="Prompt darf maximal 500 Zeichen lang sein.")

    platform = request.get("platform")  # e.g. "instagram_feed", "tiktok"
    aspect_ratio = request.get("aspect_ratio")  # e.g. "1:1", "9:16", "16:9"
    image_size = request.get("image_size")  # e.g. "1K", "2K", "4K"
    category = request.get("category", "ai_generated")
    country = request.get("country")

    # Determine aspect ratio: explicit aspect_ratio > platform mapping > default
    if not aspect_ratio and platform and platform in PLATFORM_ASPECT_RATIOS:
        aspect_ratio = PLATFORM_ASPECT_RATIOS[platform]
        logger.info(f"Auto-selected aspect_ratio={aspect_ratio} for platform={platform}")

    # Determine dimensions based on platform or explicit values
    if platform and platform in PLATFORM_DIMENSIONS:
        default_w, default_h = PLATFORM_DIMENSIONS[platform]
    else:
        default_w, default_h = 1024, 1024

    req_width = min(max(request.get("width", default_w), 256), 4096)
    req_height = min(max(request.get("height", default_h), 256), 4096)

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
            "aspect_ratio": aspect_ratio or "1:1",
            "platform": platform,
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


# ═══════════════════════════════════════════════════════════════════════
# Humor Format endpoints
# ═══════════════════════════════════════════════════════════════════════

@router.get("/humor-formats")
async def list_humor_formats(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List all available humor/meme formats with their templates and examples.

    Returns a list of humor formats that can be used with the generate-humor endpoint.
    """
    result = await db.execute(select(HumorFormat).order_by(HumorFormat.id))
    formats = result.scalars().all()

    return {
        "humor_formats": [
            {
                "id": fmt.id,
                "name": fmt.name,
                "description": fmt.description,
                "template_structure": json.loads(fmt.template_structure) if fmt.template_structure else {},
                "example_text": json.loads(fmt.example_text) if fmt.example_text else {},
                "platform_fit": fmt.platform_fit,
                "icon": fmt.icon,
            }
            for fmt in formats
        ],
        "total": len(formats),
    }


@router.get("/humor-formats/{format_id}")
async def get_humor_format(
    format_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a single humor format by ID."""
    result = await db.execute(select(HumorFormat).where(HumorFormat.id == format_id))
    fmt = result.scalar_one_or_none()
    if not fmt:
        raise HTTPException(status_code=404, detail="Humor format not found")

    return {
        "id": fmt.id,
        "name": fmt.name,
        "description": fmt.description,
        "template_structure": json.loads(fmt.template_structure) if fmt.template_structure else {},
        "example_text": json.loads(fmt.example_text) if fmt.example_text else {},
        "platform_fit": fmt.platform_fit,
        "icon": fmt.icon,
    }


def _generate_humor_with_gemini(
    api_key: str,
    format_name: str,
    format_description: str,
    template_structure: dict,
    example_text: dict,
    topic: str,
    country: str | None = None,
    tone: str = "jugendlich",
) -> dict | None:
    """Generate humor content using Gemini 2.5 Flash for a specific humor format.

    Returns structured humor content or None if generation fails.
    """
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        country_name = {
            "usa": "USA", "canada": "Kanada", "australia": "Australien",
            "newzealand": "Neuseeland", "ireland": "Irland"
        }.get(country, country or "allgemein")

        country_info = ""
        if country:
            country_data = {
                "usa": "Classic + Select Programme, ab 13.800 EUR, Highlights: Football, Prom, Yellow School Bus, Gastfamilien",
                "canada": "Englisch + Franzoesisch, ab 15.200 EUR, Highlights: Hockey, Poutine, Rocky Mountains, Multikulti",
                "australia": "ab 19.800 EUR, Highlights: Surfen, Schuluniformen, Koalas, Great Barrier Reef, relaxte Kultur",
                "newzealand": "ab 17.900 EUR, Highlights: Maori-Kultur, Schafe, Herr der Ringe, Haka, atemberaubende Natur",
                "ireland": "ab 14.500 EUR, Highlights: Freundliche Menschen, Pub Culture, gruene Landschaften, Geschichte",
            }
            country_info = f"\nLand-Details: {country_data.get(country, '')}"

        tone_instruction = (
            "Verwende Du-Anrede, 3-5 Emojis, begeisternd und lustig, Sprache wie ein cooler aelterer Freund."
            if tone == "jugendlich"
            else "Verwende Sie-Anrede, max 2-3 Emojis, humorvoll aber professionell, betone Sicherheit und Qualitaet."
        )

        system_prompt = f"""Du bist der Social-Media-Content-Creator fuer TREFF Sprachreisen (seit 1984).
Deine Aufgabe: Generiere humorvolle/unterhaltsame Inhalte fuer Instagram und TikTok.

MARKENRICHTLINIEN:
- Firma: TREFF Sprachreisen, gegruendet 1984, Eningen u.A.
- Zielgruppe: Deutsche Schueler (14-18) und deren Eltern
- Ton: {tone_instruction}
- Laender: USA, Kanada, Australien, Neuseeland, Irland
- Ziel: Engagement steigern, Markenbekanntheit erhoehen, Humor + Information verbinden

WICHTIG:
- Alle Texte auf DEUTSCH
- Humor soll relatable sein fuer Austauschschueler
- Nie respektlos gegenueber Gastlaendern oder Kulturen
- TREFF immer positiv darstellen, aber nicht zu werblich
- Hashtags IMMER mit #TREFFSprachreisen beginnen
"""

        content_prompt = f"""Generiere humorvollen Content im Format "{format_name}".

FORMAT-BESCHREIBUNG: {format_description}

TEMPLATE-STRUKTUR: {json.dumps(template_structure, ensure_ascii=False)}

BEISPIEL (als Referenz fuer Stil und Struktur): {json.dumps(example_text, ensure_ascii=False)}

THEMA: {topic}
LAND: {country_name}{country_info}

Generiere neuen, kreativen Content der dem Format und Beispiel folgt aber NICHT kopiert.
Der Content soll viral-tauglich sein und zum Kommentieren/Teilen anregen.

Antworte als JSON mit GENAU diesen Feldern:
- "format_name": "{format_name}"
- "topic": das Thema
- "content": ein Objekt mit den Format-spezifischen Feldern (gleiche Struktur wie das Beispiel)
- "caption": Instagram/TikTok Caption (2-3 Saetze, emotional, mit Emojis, Call-to-Action)
- "hashtags": Liste von 5-8 relevanten Hashtags (erstes muss #TREFFSprachreisen sein)
- "slides": eine Liste mit mindestens 1 Slide-Objekt, jedes mit: headline, subheadline, body_text, cta_text

NUR valides JSON zurueckgeben, kein Markdown, keine Erklaerung."""

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

        if not isinstance(result, dict):
            logger.warning("Gemini humor response is not a dict")
            return None

        # Ensure required fields
        result.setdefault("format_name", format_name)
        result.setdefault("topic", topic)
        result.setdefault("content", {})
        result.setdefault("caption", "")
        result.setdefault("hashtags", ["#TREFFSprachreisen"])

        # Ensure slides array exists
        if "slides" not in result or not isinstance(result.get("slides"), list):
            # Build slides from content fields
            content = result.get("content", {})
            slide = {
                "slide_index": 0,
                "headline": content.get("title", content.get("pov_title", content.get("situation", format_name))),
                "subheadline": content.get("reality_text", content.get("scene_text", content.get("fact", ""))),
                "body_text": content.get("expectation_text", content.get("punchline", content.get("conclusion", ""))),
                "cta_text": content.get("reassurance", content.get("cta", content.get("verdict", "Mehr auf treff-sprachreisen.de!"))),
                "bullet_points": content.get("things_list", content.get("items", content.get("bingo_items", []))),
            }
            result["slides"] = [slide]
        else:
            # Ensure all slides have required fields
            for i, slide in enumerate(result["slides"]):
                slide.setdefault("slide_index", i)
                slide.setdefault("headline", "")
                slide.setdefault("subheadline", "")
                slide.setdefault("body_text", "")
                slide.setdefault("cta_text", "")
                slide.setdefault("bullet_points", [])

        result["source"] = "gemini"
        logger.info("Gemini humor generation succeeded for format=%s, topic=%s", format_name, topic)
        return result

    except json.JSONDecodeError as e:
        logger.warning("Failed to parse Gemini humor JSON response: %s", e)
        return None
    except ImportError:
        logger.warning("google-genai package not installed")
        return None
    except Exception as e:
        logger.warning("Gemini humor generation failed: %s", e)
        return None


def _generate_humor_rule_based(
    format_name: str,
    template_structure: dict,
    example_text: dict,
    topic: str,
    country: str | None = None,
) -> dict:
    """Generate humor content using the example text as a template (rule-based fallback).

    Returns the example text with minor customizations based on topic and country.
    """
    import copy
    content = copy.deepcopy(example_text)

    country_name = {
        "usa": "USA", "canada": "Kanada", "australia": "Australien",
        "newzealand": "Neuseeland", "ireland": "Irland"
    }.get(country, "")

    country_flag = {
        "usa": "🇺🇸", "canada": "🇨🇦", "australia": "🇦🇺",
        "newzealand": "🇳🇿", "ireland": "🇮🇪"
    }.get(country, "🌍")

    # Build a slide from the example content
    headline = content.get("title", content.get("pov_title", content.get("situation", content.get("myth", format_name))))
    subheadline = content.get("reality_text", content.get("scene_text", content.get("fact", "")))
    body_text = content.get("expectation_text", content.get("punchline", content.get("conclusion", content.get("reassurance", ""))))
    cta_text = content.get("verdict", content.get("cta", content.get("fun_fact", "Mehr auf treff-sprachreisen.de!")))

    # For list-based formats, join items into body_text
    list_items = content.get("things_list", content.get("items", content.get("bingo_items", content.get("clues", []))))
    if list_items and isinstance(list_items, list):
        if isinstance(list_items[0], dict):
            body_text = "\n".join([f"{item.get('level', '')}: {item.get('text', '')}" for item in list_items])
        else:
            body_text = "\n".join(list_items)

    # Rankings special handling
    rankings = content.get("rankings", [])
    if rankings and isinstance(rankings, list) and isinstance(rankings[0], dict):
        body_text = "\n".join([f"{r.get('level', '').upper()}: {r.get('text', '')}" for r in rankings])

    slide = {
        "slide_index": 0,
        "headline": headline if headline else f"{format_name}: {topic}",
        "subheadline": subheadline if subheadline else f"{country_flag} {country_name}" if country_name else topic,
        "body_text": body_text if body_text else f"Humor-Content zum Thema: {topic}",
        "cta_text": cta_text if cta_text else "Mehr auf treff-sprachreisen.de!",
        "bullet_points": list_items if isinstance(list_items, list) else [],
    }

    caption = content.get("caption", f"{format_name}: {topic} {country_flag} #TREFFSprachreisen")
    hashtags = content.get("hashtags", ["#TREFFSprachreisen", "#Auslandsjahr", f"#{format_name.replace(' ', '')}"])

    return {
        "format_name": format_name,
        "topic": topic,
        "content": content,
        "caption": caption,
        "hashtags": hashtags,
        "slides": [slide],
        "source": "rule_based",
    }


@router.post("/generate-humor")
async def generate_humor(
    request: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Generate humor/meme content for a specific humor format.

    Uses Gemini 2.5 Flash when an API key is available, with rule-based fallback.

    Expects:
    - format_id (int) OR format_type (str): Which humor format to use
    - topic (str): Topic or subject for the humor content
    - country (str, optional): Target country
    - tone (str, optional): jugendlich or serioess (default: jugendlich)

    Returns structured humor content with text, caption, and hashtags.
    """
    # Rate limit check
    ai_rate_limiter.check_rate_limit(user_id, "generate-humor")

    try:
        format_id = request.get("format_id")
        format_type = request.get("format_type")
        topic = request.get("topic", "Auslandsjahr")
        country = request.get("country")
        tone = request.get("tone", "jugendlich")

        # Look up the humor format
        humor_format = None
        if format_id:
            result = await db.execute(select(HumorFormat).where(HumorFormat.id == format_id))
            humor_format = result.scalar_one_or_none()
        elif format_type:
            result = await db.execute(select(HumorFormat).where(HumorFormat.name == format_type))
            humor_format = result.scalar_one_or_none()

        if not humor_format:
            raise HTTPException(status_code=404, detail="Humor format not found. Use GET /api/ai/humor-formats to see available formats.")

        template_structure = json.loads(humor_format.template_structure) if humor_format.template_structure else {}
        example_text = json.loads(humor_format.example_text) if humor_format.example_text else {}

        # Try Gemini first
        api_key = await _get_gemini_api_key(user_id, db)
        result = None

        if api_key:
            result = _generate_humor_with_gemini(
                api_key=api_key,
                format_name=humor_format.name,
                format_description=humor_format.description,
                template_structure=template_structure,
                example_text=example_text,
                topic=topic,
                country=country,
                tone=tone,
            )

        # Fallback to rule-based
        if not result:
            result = _generate_humor_rule_based(
                format_name=humor_format.name,
                template_structure=template_structure,
                example_text=example_text,
                topic=topic,
                country=country,
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Humor generation failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Humor generation failed: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════
# Hook / Attention-Grabber Generation endpoints
# ═══════════════════════════════════════════════════════════════════════

HOOK_TYPES = {
    "frage": {
        "label": "Frage",
        "description": "Provokante oder neugierig machende Frage",
        "icon": "❓",
        "examples": [
            "Wusstest du, dass 87% aller Austauschschueler sagen, es war die beste Entscheidung ihres Lebens?",
            "Was wuerdest du tun, wenn du ploetzlich 10.000 km von zuhause entfernt aufwachst?",
            "Hast du dich jemals gefragt, wie es sich anfuehlt, in einer amerikanischen High School zu sitzen?",
        ],
    },
    "statistik": {
        "label": "Statistik",
        "description": "Ueberraschende Zahl oder Statistik",
        "icon": "📊",
        "examples": [
            "87% aller Austauschschueler sagen: Es war die beste Entscheidung meines Lebens.",
            "Nur 3% aller deutschen Schueler machen ein Auslandsjahr – gehoerst du bald dazu?",
            "10.000+ Schueler hat TREFF seit 1984 ins Ausland geschickt.",
        ],
    },
    "emotion": {
        "label": "Emotion",
        "description": "Emotionales Statement oder Gefuehlsbeschreibung",
        "icon": "🥺",
        "examples": [
            "Der Moment, in dem du realisierst, dass du deine Gastfamilie mehr vermisst als du dachtest...",
            "Dieses Gefuehl, wenn du zum ersten Mal alleine am Flughafen stehst – und weisst, dein Abenteuer beginnt jetzt.",
            "Es gibt diesen einen Moment, der alles veraendert. Fuer mich war es der erste Schultag in Kanada.",
        ],
    },
    "provokation": {
        "label": "Provokation",
        "description": "Mutiges Statement oder Unpopular Opinion",
        "icon": "⚡",
        "examples": [
            "Unpopular Opinion: Ein Auslandsjahr bringt dir mehr als jedes Abitur-Zeugnis.",
            "Sorry, aber: Wer nie im Ausland war, verpasst die wichtigste Lektion des Lebens.",
            "Hot Take: Die beste Schule ist nicht in Deutschland – sie ist 10.000 km entfernt.",
        ],
    },
    "story_opener": {
        "label": "Story-Opener",
        "description": "Erzaehlerischer Einstieg der neugierig macht",
        "icon": "📖",
        "examples": [
            "Es war 3 Uhr morgens in Vancouver, als mein Telefon klingelte...",
            "Ich stand am Flughafen mit zwei Koffern und null Plan – und es war der beste Tag meines Lebens.",
            "Tag 1 in meiner Gastfamilie: Die Mutter stellte mir ein Gericht vor, das ich noch nie gesehen hatte...",
        ],
    },
}


def _generate_hooks_rule_based(
    topic: str,
    country: str | None,
    tone: str,
    platform: str,
    count: int,
) -> list[dict]:
    """Generate hook variants using rule-based templates (fallback)."""
    import random

    country_name = {
        "usa": "USA", "canada": "Kanada", "australia": "Australien",
        "newzealand": "Neuseeland", "ireland": "Irland"
    }.get(country, "")

    hooks = []
    hook_type_keys = list(HOOK_TYPES.keys())

    for i in range(count):
        hook_type = hook_type_keys[i % len(hook_type_keys)]
        hook_data = HOOK_TYPES[hook_type]

        example = random.choice(hook_data["examples"])
        if country_name:
            replacements = {
                "Kanada": country_name,
                "Vancouver": {
                    "usa": "New York", "canada": "Vancouver", "australia": "Sydney",
                    "newzealand": "Auckland", "ireland": "Dublin",
                }.get(country, "Vancouver"),
                "amerikanischen": {
                    "usa": "amerikanischen", "canada": "kanadischen",
                    "australia": "australischen", "newzealand": "neuseelaendischen",
                    "ireland": "irischen",
                }.get(country, "auslaendischen"),
            }
            for old, new in replacements.items():
                if isinstance(new, str):
                    example = example.replace(old, new)

        hooks.append({
            "hook_text": example,
            "hook_type": hook_type,
            "hook_type_label": hook_data["label"],
            "hook_type_icon": hook_data["icon"],
        })

    return hooks


def _generate_hooks_with_gemini(
    api_key: str,
    topic: str,
    country: str | None,
    tone: str,
    platform: str,
    count: int,
) -> list[dict] | None:
    """Generate hook variants using Gemini 2.5 Flash."""
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        country_name = {
            "usa": "USA", "canada": "Kanada", "australia": "Australien",
            "newzealand": "Neuseeland", "ireland": "Irland"
        }.get(country, country or "allgemein")

        tone_instruction = (
            "Verwende Du-Anrede, begeisternd, 1-2 Emojis pro Hook."
            if tone in ("jugendlich", "witzig", "motivierend", "wholesome")
            else "Verwende Sie-Anrede, serioees aber ansprechend, max 1 Emoji."
        )

        platform_instruction = (
            "Die Hooks sollen als Text-Overlay in Videos funktionieren (kurz, knackig, visuell)."
            if platform in ("tiktok", "instagram_story", "instagram_reels")
            else "Die Hooks sollen als erste Zeile eines Instagram-Feed-Posts funktionieren."
        )

        system_prompt = f"""Du bist ein Experte fuer Social-Media-Hooks und Attention-Grabber fuer TREFF Sprachreisen, einen deutschen Anbieter von Highschool-Aufenthalten im Ausland (USA, Kanada, Australien, Neuseeland, Irland).

Deine Aufgabe: Generiere {count} verschiedene Hooks/Aufhaenger fuer den Beginn eines Social-Media-Posts. Die ersten 1-3 Sekunden entscheiden, ob jemand weiterliest oder weiterscrollt.

TREFF Sprachreisen:
- Seit 1984, Eningen u.A., Deutschland
- ~200 Teilnehmer pro Jahr, Zielgruppe: Schueler 14-18 + Eltern
- Preise: USA ab 13.800 EUR, Kanada ab 15.200 EUR, Australien ab 18.900 EUR, Neuseeland ab 19.500 EUR, Irland ab 14.500 EUR

{tone_instruction}
{platform_instruction}

Alle Texte auf Deutsch!"""

        content_prompt = f"""Generiere genau {count} verschiedene Hooks/Attention-Grabber fuer einen TREFF Sprachreisen Post.

THEMA: {topic}
LAND: {country_name}
TONALITAET: {tone}
PLATTFORM: {platform}

Jeder Hook soll einem anderen Typ entsprechen:
1. "frage" - Provokante oder neugierig machende Frage
2. "statistik" - Ueberraschende Zahl oder Statistik
3. "emotion" - Emotionales Statement
4. "provokation" - Mutiges Statement / Unpopular Opinion
5. "story_opener" - Erzaehlerischer Einstieg

Regeln:
- Jeder Hook max 150 Zeichen
- Hooks sollen zum Stoppen beim Scrollen zwingen (Scroll-Stopper)
- Jeder Hook soll einzigartig und kreativ sein
- Hooks muessen zum Thema und Land passen

Antworte ausschliesslich im folgenden JSON-Format:
{{
  "hooks": [
    {{
      "hook_text": "Der Hook-Text",
      "hook_type": "frage|statistik|emotion|provokation|story_opener"
    }}
  ]
}}"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=content_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                temperature=0.95,
                max_output_tokens=2048,
            ),
        )

        response_text = response.text.strip()

        if response_text.startswith("```"):
            lines = response_text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            response_text = "\n".join(lines)

        result = json.loads(response_text)

        if not isinstance(result, dict) or "hooks" not in result:
            logger.warning("Gemini hooks response missing 'hooks' key")
            return None

        hooks_raw = result["hooks"]
        if not isinstance(hooks_raw, list) or len(hooks_raw) == 0:
            logger.warning("Gemini returned empty hooks list")
            return None

        valid_hook_types = set(HOOK_TYPES.keys())
        hooks = []
        for h in hooks_raw[:count]:
            if not isinstance(h, dict) or not h.get("hook_text"):
                continue
            hook_type = h.get("hook_type", "frage")
            if hook_type not in valid_hook_types:
                hook_type = "frage"
            hook_data = HOOK_TYPES[hook_type]
            hooks.append({
                "hook_text": h["hook_text"][:200],
                "hook_type": hook_type,
                "hook_type_label": hook_data["label"],
                "hook_type_icon": hook_data["icon"],
            })

        if hooks:
            logger.info("Gemini generated %d hooks for topic=%s", len(hooks), topic)
            return hooks

        return None

    except Exception as e:
        logger.warning("Gemini hook generation failed: %s", e)
        return None


@router.post("/generate-hooks")
async def generate_hooks(
    request: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Generate multiple hook/attention-grabber variants for a post.

    Expects:
    - topic (str): Topic or subject for the hooks
    - tone (str, optional): jugendlich, serioess, etc. (default: jugendlich)
    - platform (str, optional): instagram_feed, tiktok, etc. (default: instagram_feed)
    - country (str, optional): Target country
    - count (int, optional): Number of hooks to generate (default: 5, max: 8)

    Returns:
    - hooks: list of hook objects with hook_text, hook_type, hook_type_label, hook_type_icon
    - source: "gemini" or "rule_based"
    - hook_types: reference list of all available hook types
    """
    ai_rate_limiter.check_rate_limit(user_id, "generate-hooks")

    topic = request.get("topic", "").strip() or "Auslandsjahr"
    tone = request.get("tone", "jugendlich")
    platform = request.get("platform", "instagram_feed")
    country = request.get("country")
    count = request.get("count", 5)

    try:
        count = int(count)
    except (TypeError, ValueError):
        count = 5
    count = max(1, min(8, count))

    api_key = await _get_gemini_api_key(user_id, db)
    source = "rule_based"
    hooks = None

    if api_key:
        hooks = _generate_hooks_with_gemini(
            api_key=api_key, topic=topic, country=country,
            tone=tone, platform=platform, count=count,
        )
        if hooks:
            source = "gemini"

    if not hooks:
        hooks = _generate_hooks_rule_based(
            topic=topic, country=country, tone=tone,
            platform=platform, count=count,
        )

    for h in hooks:
        hook_record = Hook(
            user_id=user_id, hook_text=h["hook_text"],
            hook_type=h["hook_type"], topic=topic, country=country,
            tone=tone, platform=platform, selected=0, source=source,
        )
        db.add(hook_record)

    await db.flush()

    return {
        "status": "success",
        "hooks": hooks,
        "source": source,
        "count": len(hooks),
        "hook_types": {
            k: {"label": v["label"], "description": v["description"], "icon": v["icon"]}
            for k, v in HOOK_TYPES.items()
        },
        "message": f"{len(hooks)} Hook-Varianten generiert!",
    }


@router.post("/save-hook-selection")
async def save_hook_selection(
    request: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Save which hook was selected by the user for a post.

    Expects:
    - hook_text (str): The selected hook text
    - hook_type (str): The type of hook (frage, statistik, etc.)
    - post_id (int, optional): Associated post ID
    - topic (str, optional): Topic context
    - country (str, optional): Country context

    Returns:
    - status: "success"
    - hook_id: ID of the saved hook record
    """
    hook_text = request.get("hook_text", "").strip()
    hook_type = request.get("hook_type", "frage")
    post_id = request.get("post_id")
    topic = request.get("topic")
    country = request.get("country")

    if not hook_text:
        raise HTTPException(status_code=400, detail="hook_text is required")

    if hook_type not in HOOK_TYPES:
        hook_type = "frage"

    hook = Hook(
        user_id=user_id, post_id=post_id, hook_text=hook_text,
        hook_type=hook_type, topic=topic, country=country,
        selected=1, source="user_selected",
    )
    db.add(hook)
    await db.flush()
    await db.refresh(hook)

    return {
        "status": "success",
        "hook_id": hook.id,
        "message": "Hook-Auswahl gespeichert!",
    }


# ═══════════════════════════════════════════════════════════════════════
# Hashtag Suggestion Engine
# ═══════════════════════════════════════════════════════════════════════

def _suggest_hashtags_rule_based(
    topic: str,
    country: str | None,
    platform: str,
    category: str | None,
    existing_sets: list[dict],
) -> dict:
    """Suggest hashtags using rule-based logic from existing hashtag sets."""
    import random

    suggested = []
    reasons = []

    # Always start with TREFF brand hashtag
    suggested.append("#TREFFSprachreisen")

    # Find matching sets from existing data
    country_sets = [s for s in existing_sets if s.get("country") == country]
    category_sets = [s for s in existing_sets if s.get("category") == category]
    general_sets = [s for s in existing_sets if s.get("category") == "allgemein"]

    # Add from country-specific sets
    for s in sorted(country_sets, key=lambda x: x.get("performance_score", 0), reverse=True)[:2]:
        tags = s.get("hashtags", [])
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except (json.JSONDecodeError, TypeError):
                tags = []
        for tag in tags:
            if tag not in suggested:
                suggested.append(tag)
        reasons.append(f"Aus Set '{s['name']}' (Score: {s.get('performance_score', 0)})")

    # Add from category-specific sets
    for s in sorted(category_sets, key=lambda x: x.get("performance_score", 0), reverse=True)[:1]:
        tags = s.get("hashtags", [])
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except (json.JSONDecodeError, TypeError):
                tags = []
        for tag in tags:
            if tag not in suggested:
                suggested.append(tag)

    # If we still have too few, add from general sets
    if len(suggested) < 8:
        for s in general_sets:
            tags = s.get("hashtags", [])
            if isinstance(tags, str):
                try:
                    tags = json.loads(tags)
                except (json.JSONDecodeError, TypeError):
                    tags = []
            for tag in tags:
                if tag not in suggested:
                    suggested.append(tag)
                if len(suggested) >= 12:
                    break

    # Topic-based hashtag
    if topic:
        topic_tag = "#" + "".join(word.capitalize() for word in topic.split()[:3] if word.isalpha())
        if topic_tag not in suggested and len(topic_tag) > 2:
            suggested.append(topic_tag)

    # Limit to 8-12 hashtags
    suggested = suggested[:12]

    return {
        "hashtags": suggested,
        "hashtag_string": " ".join(suggested),
        "count": len(suggested),
        "reasons": reasons if reasons else ["Basierend auf vordefinierten Hashtag-Sets"],
    }


def _suggest_hashtags_with_gemini(
    api_key: str,
    topic: str,
    country: str | None,
    platform: str,
    category: str | None,
    tone: str,
) -> dict | None:
    """Suggest hashtags using Gemini AI for more intelligent, context-aware suggestions."""
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        country_name = COUNTRY_NAMES.get(country, country or "allgemein")

        system_prompt = """Du bist ein Social-Media-Hashtag-Stratege fuer TREFF Sprachreisen, einen deutschen Anbieter von Highschool-Aufenthalten (USA, Kanada, Australien, Neuseeland, Irland).

Deine Aufgabe: Generiere eine optimale Hashtag-Kombination fuer maximale Reichweite und Engagement.

REGELN:
- Erstes Hashtag MUSS immer #TREFFSprachreisen sein
- Mix aus deutsch und englisch (Zielgruppe: Deutsche Teenager + Eltern)
- Mix aus high-volume (>100k) und niche (<10k) Hashtags
- Max 8-12 Hashtags (nicht zu viele, nicht zu wenige)
- Keine Leerzeichen in Hashtags, CamelCase fuer Lesbarkeit
- Alle Hashtags mit # beginnen
- Relevanz zum Thema, Land und Plattform"""

        content_prompt = f"""Generiere optimale Hashtags fuer diesen TREFF Sprachreisen Post:

THEMA: {topic}
LAND: {country_name}
PLATTFORM: {platform}
KATEGORIE: {category or 'allgemein'}
TONALITAET: {tone}

Antworte als JSON:
{{
  "hashtags": ["#TREFFSprachreisen", "#Hashtag2", ...],
  "reasons": ["Warum diese Kombination gut ist (1-2 Saetze)"]
}}"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=content_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                temperature=0.7,
                max_output_tokens=1024,
            ),
        )

        response_text = response.text.strip()
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            response_text = "\n".join(lines)

        result = json.loads(response_text)

        if not isinstance(result, dict) or "hashtags" not in result:
            return None

        hashtags = result["hashtags"]
        if not isinstance(hashtags, list) or len(hashtags) == 0:
            return None

        # Ensure #TREFFSprachreisen is first
        cleaned = []
        for tag in hashtags:
            tag = tag.strip()
            if not tag.startswith("#"):
                tag = f"#{tag}"
            if tag not in cleaned:
                cleaned.append(tag)

        if "#TREFFSprachreisen" not in cleaned:
            cleaned.insert(0, "#TREFFSprachreisen")
        elif cleaned[0] != "#TREFFSprachreisen":
            cleaned.remove("#TREFFSprachreisen")
            cleaned.insert(0, "#TREFFSprachreisen")

        cleaned = cleaned[:12]

        return {
            "hashtags": cleaned,
            "hashtag_string": " ".join(cleaned),
            "count": len(cleaned),
            "reasons": result.get("reasons", ["KI-optimierte Hashtag-Kombination"]),
        }

    except Exception as e:
        logger.warning("Gemini hashtag suggestion failed: %s", e)
        return None


@router.post("/suggest-hashtags")
async def suggest_hashtags(
    request: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Suggest optimized hashtags based on topic, country, and platform.

    Uses AI (Gemini) when available, falls back to rule-based suggestions
    from predefined hashtag sets.

    Expects:
    - topic (str): Post topic
    - country (str, optional): Target country (usa, canada, australia, newzealand, ireland)
    - platform (str, optional): Target platform (default: instagram_feed)
    - category (str, optional): Post category
    - tone (str, optional): Tone of voice (default: jugendlich)

    Returns:
    - hashtags: list of hashtag strings
    - hashtag_string: space-separated hashtag string ready for pasting
    - count: number of hashtags
    - source: "gemini" or "rule_based"
    - emoji_suggestions: recommended emojis based on tone and country
    """
    ai_rate_limiter.check_rate_limit(user_id, "suggest-hashtags")

    topic = request.get("topic", "").strip() or "Auslandsjahr"
    country = request.get("country")
    platform = request.get("platform", "instagram_feed")
    category = request.get("category")
    tone = request.get("tone", "jugendlich")

    # Load existing hashtag sets for rule-based fallback
    from sqlalchemy import or_
    sets_result = await db.execute(
        select(HashtagSet).where(
            or_(
                HashtagSet.user_id == user_id,
                HashtagSet.user_id.is_(None),
            )
        ).order_by(HashtagSet.performance_score.desc())
    )
    existing_sets = []
    for hs in sets_result.scalars().all():
        try:
            hashtags = json.loads(hs.hashtags) if isinstance(hs.hashtags, str) else hs.hashtags
        except (json.JSONDecodeError, TypeError):
            hashtags = []
        existing_sets.append({
            "name": hs.name,
            "hashtags": hashtags,
            "category": hs.category,
            "country": hs.country,
            "performance_score": hs.performance_score,
        })

    # Try Gemini first
    api_key = await _get_gemini_api_key(user_id, db)
    source = "rule_based"
    result = None

    if api_key:
        result = _suggest_hashtags_with_gemini(
            api_key=api_key,
            topic=topic,
            country=country,
            platform=platform,
            category=category,
            tone=tone,
        )
        if result:
            source = "gemini"

    if not result:
        result = _suggest_hashtags_rule_based(
            topic=topic,
            country=country,
            platform=platform,
            category=category,
            existing_sets=existing_sets,
        )

    # Get emoji suggestions based on tone and country
    emoji_data = _get_emoji_suggestions(tone, country)

    return {
        "status": "success",
        "source": source,
        **result,
        "emoji_suggestions": emoji_data,
        "message": f"{result['count']} Hashtags vorgeschlagen!",
    }


# ═══════════════════════════════════════════════════════════════════════
# Emoji Rules Endpoint
# ═══════════════════════════════════════════════════════════════════════

def _get_emoji_suggestions(tone: str, country: str | None = None) -> dict:
    """Get emoji suggestions based on tone and country."""
    import random

    rules = EMOJI_RULES.get(tone, EMOJI_RULES["jugendlich"])

    # Build emoji pool
    emoji_pool = list(rules["preferred_emojis"])

    # Add country-specific emojis
    country_emojis = []
    if country and country in rules.get("country_emojis", {}):
        country_emojis = rules["country_emojis"][country]
        emoji_pool = country_emojis + emoji_pool

    # Select recommended count
    min_count, max_count = rules["count_range"]
    recommended_count = min(max_count, len(emoji_pool))

    # Pick a balanced selection
    selected = []
    if country_emojis:
        selected.extend(country_emojis[:2])

    remaining = [e for e in emoji_pool if e not in selected]
    random.shuffle(remaining)
    while len(selected) < recommended_count and remaining:
        selected.append(remaining.pop(0))

    return {
        "tone": tone,
        "recommended_emojis": selected[:max_count],
        "all_emojis": emoji_pool,
        "country_emojis": country_emojis,
        "count_range": {"min": min_count, "max": max_count},
        "style_description": rules["description"],
    }


@router.get("/emoji-rules")
async def get_emoji_rules(
    tone: str = "jugendlich",
    country: str | None = None,
    user_id: int = Depends(get_current_user_id),
):
    """Get emoji rules and suggestions for a given tone and country.

    Returns recommended emojis, count range, and style guidelines.
    """
    if tone not in EMOJI_RULES:
        tone = "jugendlich"

    emoji_data = _get_emoji_suggestions(tone, country)

    return {
        "status": "success",
        "emoji_rules": emoji_data,
        "available_tones": list(EMOJI_RULES.keys()),
    }


# ═══════════════════════════════════════════════════════════════════════
# Interactive Story Elements AI Generation
# ═══════════════════════════════════════════════════════════════════════

INTERACTIVE_ELEMENT_TYPES = {
    "poll": {
        "label": "Umfrage",
        "description": "Ja/Nein oder A/B Umfrage",
        "option_count": 2,
    },
    "quiz": {
        "label": "Quiz",
        "description": "Multiple-Choice Quiz mit richtiger Antwort",
        "option_count": 4,
    },
    "slider": {
        "label": "Emoji-Slider",
        "description": "Bewertungs-Slider mit Emoji",
        "option_count": 0,
    },
    "question": {
        "label": "Fragen-Sticker",
        "description": "Offene Frage an die Community",
        "option_count": 0,
    },
}


def _generate_interactive_rule_based(
    element_type: str, topic: str, country: str | None = None
) -> dict:
    """Generate interactive element content using rule-based approach (fallback)."""
    country_name = {
        "usa": "USA",
        "canada": "Kanada",
        "australia": "Australien",
        "newzealand": "Neuseeland",
        "ireland": "Irland",
    }.get(country, "Ausland")

    country_flag = {
        "usa": "🇺🇸",
        "canada": "🇨🇦",
        "australia": "🇦🇺",
        "newzealand": "🇳🇿",
        "ireland": "🇮🇪",
    }.get(country, "🌍")

    if element_type == "poll":
        templates = [
            {
                "question_text": f"Wuerdest du ein Highschool-Jahr in {country_name} {country_flag} machen?",
                "options": ["Ja, sofort! 🙌", "Nein, lieber woanders"],
            },
            {
                "question_text": f"Was ist dir beim Auslandsjahr wichtiger?",
                "options": ["Neue Freunde finden 👫", "Sprache perfekt lernen 📚"],
            },
            {
                "question_text": f"{country_flag} {country_name}: Wuerdest du lieber in der Stadt oder auf dem Land leben?",
                "options": ["Stadt - viel Action! 🏙️", "Land - Natur pur! 🌲"],
            },
        ]
        import random
        chosen = random.choice(templates)
        return {
            "element_type": "poll",
            "question_text": chosen["question_text"],
            "options": chosen["options"],
            "correct_answer": None,
            "emoji": None,
            "source": "rule_based",
        }

    elif element_type == "quiz":
        templates = [
            {
                "question_text": f"Wie viele Schueler gehen auf eine typische US-Highschool?",
                "options": ["500", "1.500", "3.000", "5.000"],
                "correct_answer": 1,
            },
            {
                "question_text": f"Wie lange dauert ein Highschool-Jahr in {country_name}?",
                "options": ["6 Monate", "10 Monate", "12 Monate", "15 Monate"],
                "correct_answer": 1,
            },
            {
                "question_text": f"Seit wann organisiert TREFF Sprachreisen Auslandsaufenthalte?",
                "options": ["1990", "1984", "2000", "1975"],
                "correct_answer": 1,
            },
            {
                "question_text": f"Welches Schulfach gibt es in {country_name}, aber nicht in Deutschland?",
                "options": ["Yearbook", "Physik", "Mathematik", "Englisch"],
                "correct_answer": 0,
            },
        ]
        import random
        chosen = random.choice(templates)
        return {
            "element_type": "quiz",
            "question_text": chosen["question_text"],
            "options": chosen["options"],
            "correct_answer": chosen["correct_answer"],
            "emoji": None,
            "source": "rule_based",
        }

    elif element_type == "slider":
        templates = [
            {
                "question_text": f"Wie sehr freust du dich auf dein Auslandsjahr in {country_name}? {country_flag}",
                "emoji": "🔥",
            },
            {
                "question_text": "Wie krass wuerde ein Highschool-Jahr dein Leben veraendern?",
                "emoji": "🤯",
            },
            {
                "question_text": f"Wie sehr liebst du {country_name}?",
                "emoji": "❤️",
            },
        ]
        import random
        chosen = random.choice(templates)
        return {
            "element_type": "slider",
            "question_text": chosen["question_text"],
            "options": None,
            "correct_answer": None,
            "emoji": chosen["emoji"],
            "source": "rule_based",
        }

    else:  # question
        templates = [
            {
                "question_text": f"Was wuerdest du in {country_name} {country_flag} als Erstes machen?",
            },
            {
                "question_text": "Welche Frage hast du zum Auslandsjahr? Frag uns! 💬",
            },
            {
                "question_text": f"Was ist dein groesster Traum fuer dein Jahr in {country_name}?",
            },
        ]
        import random
        chosen = random.choice(templates)
        return {
            "element_type": "question",
            "question_text": chosen["question_text"],
            "options": None,
            "correct_answer": None,
            "emoji": None,
            "source": "rule_based",
        }


async def _generate_interactive_with_gemini(
    element_type: str,
    topic: str,
    country: str | None,
    api_key: str,
) -> dict | None:
    """Generate interactive Story element content using Gemini 2.5 Flash."""
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        country_name = {
            "usa": "USA",
            "canada": "Kanada",
            "australia": "Australien",
            "newzealand": "Neuseeland",
            "ireland": "Irland",
        }.get(country, "Ausland")

        type_instructions = {
            "poll": 'Erstelle eine Instagram-Umfrage mit genau 2 Antwortmoeglichkeiten. Format: {"question_text": "...", "options": ["Option A", "Option B"], "correct_answer": null, "emoji": null}',
            "quiz": 'Erstelle ein Instagram-Quiz mit genau 4 Antwortmoeglichkeiten und einer korrekten Antwort. Format: {"question_text": "...", "options": ["A", "B", "C", "D"], "correct_answer": 0, "emoji": null} (correct_answer ist der Index 0-3)',
            "slider": 'Erstelle einen Instagram Emoji-Slider. Format: {"question_text": "...", "options": null, "correct_answer": null, "emoji": "🔥"} (waehle ein passendes Emoji)',
            "question": 'Erstelle einen Instagram Fragen-Sticker. Format: {"question_text": "...", "options": null, "correct_answer": null, "emoji": null}',
        }

        system_prompt = f"""Du bist ein Social-Media-Experte fuer TREFF Sprachreisen, einen deutschen Anbieter von Highschool-Aufenthalten im Ausland (USA, Kanada, Australien, Neuseeland, Irland).

Zielgruppe: Deutsche Schueler (14-18 Jahre) und deren Eltern.
Tonfall: Jugendlich aber serioess - locker, nahbar, mit 1-2 passenden Emojis.
Sprache: DEUTSCH

{type_instructions.get(element_type, type_instructions["poll"])}

Wichtig:
- Die Frage muss zum Thema "{topic}" und zum Land "{country_name}" passen
- Verwende jugendliche, ansprechende Sprache
- Bei Quiz: Die richtige Antwort muss faktisch korrekt sein
- Bei Poll: Beide Optionen muessen gleichwertig attraktiv sein
- Bei Slider: Waehle ein Emoji das zur Frage passt
- Bei Frage: Die Frage soll Engagement/Antworten foerdern

NUR valides JSON zurueckgeben, kein Markdown, keine Erklaerung."""

        content_prompt = f"Erstelle ein interaktives Instagram-Story-Element vom Typ '{element_type}' zum Thema '{topic}' fuer das Land '{country_name}'."

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=content_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                temperature=0.9,
                max_output_tokens=1024,
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

        if not isinstance(result, dict):
            logger.warning("Gemini interactive element response is not a dict")
            return None

        # Ensure required fields
        result.setdefault("question_text", f"Frage zu {topic}")
        result["element_type"] = element_type
        result["source"] = "gemini"

        # Validate type-specific fields
        if element_type in ("poll", "quiz"):
            if not isinstance(result.get("options"), list) or len(result.get("options", [])) < 2:
                logger.warning("Gemini interactive element missing valid options")
                return None

        if element_type == "quiz":
            if result.get("correct_answer") is None:
                result["correct_answer"] = 0

        logger.info(
            "Gemini interactive element generation succeeded for type=%s, topic=%s",
            element_type,
            topic,
        )
        return result

    except json.JSONDecodeError as e:
        logger.warning("Failed to parse Gemini interactive element JSON: %s", e)
        return None
    except ImportError:
        logger.warning("google-genai package not installed")
        return None
    except Exception as e:
        logger.warning("Gemini interactive element generation failed: %s", e)
        return None


@router.post("/generate-interactive")
async def generate_interactive(
    request: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Generate interactive Story element content (poll, quiz, slider, question).

    Uses Gemini 2.5 Flash when available, with rule-based fallback.

    Expects:
    - element_type (str): poll, quiz, slider, or question
    - topic (str): Topic for the interactive element
    - country (str, optional): Target country

    Returns interactive element content with question, options, etc.
    """
    ai_rate_limiter.check_rate_limit(user_id, "generate-interactive")

    element_type = request.get("element_type", "poll")
    topic = request.get("topic", "Highschool-Aufenthalt")
    country = request.get("country")

    if element_type not in INTERACTIVE_ELEMENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid element_type. Must be one of: {', '.join(INTERACTIVE_ELEMENT_TYPES.keys())}",
        )

    # Try Gemini first
    api_key = await _get_gemini_api_key(user_id, db)
    result = None

    if api_key:
        result = await _generate_interactive_with_gemini(
            element_type=element_type,
            topic=topic,
            country=country,
            api_key=api_key,
        )

    # Fallback to rule-based
    if not result:
        result = _generate_interactive_rule_based(
            element_type=element_type,
            topic=topic,
            country=country,
        )

    return {
        "status": "success",
        "element": result,
        "available_types": {
            k: {"label": v["label"], "description": v["description"]}
            for k, v in INTERACTIVE_ELEMENT_TYPES.items()
        },
    }


# ═══════════════════════════════════════════════════════════════════════
# Engagement-Boost Vorschlaege (AI-powered engagement improvement suggestions)
# ═══════════════════════════════════════════════════════════════════════

def _build_engagement_boost_system_prompt() -> str:
    """Build the system prompt for engagement boost analysis."""
    return """Du bist ein erfahrener Social-Media-Experte und Engagement-Analyst fuer TREFF Sprachreisen,
einen deutschen Anbieter von Highschool-Aufenthalten im Ausland (USA, Kanada, Australien, Neuseeland, Irland).

Deine Aufgabe: Analysiere einen Social-Media-Post-Entwurf und gib konkrete, umsetzbare Vorschlaege,
wie das Engagement (Likes, Kommentare, Shares, Saves) erhoeht werden kann.

Analysiere diese Aspekte:
1. Hook-Staerke: Ist der erste Satz/die Headline aufmerksamkeitsstark genug?
2. CTA-Vorhandensein: Gibt es einen klaren Call-to-Action? Ist er stark genug?
3. Textlaenge: Ist die Caption zu lang/zu kurz fuer die Plattform?
4. Hashtag-Qualitaet: Sind die Hashtags relevant, vielfaeltig, nicht zu viele/wenige?
5. Posting-Zeit: Ist die geplante Posting-Zeit optimal fuer die Zielgruppe (deutsche Teenager 14-18)?
6. Format-Wahl: Ist das gewaehlte Format (Feed Post, Story, Reel) das richtige fuer diesen Inhalt?
7. Emotionale Ansprache: Spricht der Post die Zielgruppe emotional an?
8. Interaktionsanreize: Gibt es Elemente, die zur Interaktion einladen (Fragen, Umfragen, etc.)?

Fuer jeden Vorschlag gib an:
- priority: "high", "medium", oder "low"
- category: Eine der Kategorien (hook, cta, length, hashtags, timing, format, emotion, interaction)
- suggestion: Der konkrete Verbesserungsvorschlag auf Deutsch (2-3 Saetze)
- estimated_boost: Geschaetzte Engagement-Verbesserung als Prozent-String (z.B. "+15%", "+5%", "+25%")
- action_text: Ein kurzer Aktionstext fuer den "Anwenden" Button (z.B. "Hook umschreiben", "CTA hinzufuegen")

WICHTIG:
- Alle Texte auf Deutsch
- Konkret und umsetzbar, nicht vage
- Maximal 6 Vorschlaege, mindestens 2
- Sortiert nach Priority (high zuerst)
- Geschaetzte Boosts realistisch (nicht ueber +30%)

Antworte NUR als JSON-Array von Vorschlaegen. Kein zusaetzlicher Text."""


def _build_engagement_boost_content_prompt(
    post_content: dict,
    platform: str,
    post_format: str,
    posting_time: str | None = None,
) -> str:
    """Build the content prompt with the actual post data to analyze."""
    # Extract post content details
    slides = post_content.get("slides", [])
    caption_instagram = post_content.get("caption_instagram", "")
    caption_tiktok = post_content.get("caption_tiktok", "")
    hashtags_instagram = post_content.get("hashtags_instagram", "")
    hashtags_tiktok = post_content.get("hashtags_tiktok", "")
    cta_text = post_content.get("cta_text", "")
    category = post_content.get("category", "")
    country = post_content.get("country", "")
    tone = post_content.get("tone", "")

    # Build slide content summary
    slide_texts = []
    for i, slide in enumerate(slides):
        parts = []
        if slide.get("headline"):
            parts.append(f"Headline: {slide['headline']}")
        if slide.get("subheadline"):
            parts.append(f"Subheadline: {slide['subheadline']}")
        if slide.get("body_text"):
            parts.append(f"Body: {slide['body_text']}")
        if slide.get("cta_text"):
            parts.append(f"CTA: {slide['cta_text']}")
        slide_texts.append(f"Slide {i+1}: " + " | ".join(parts))

    slides_summary = "\n".join(slide_texts) if slide_texts else "Keine Slides vorhanden"

    # Pick the right caption for the platform
    caption = caption_instagram if "instagram" in platform else caption_tiktok
    hashtags = hashtags_instagram if "instagram" in platform else hashtags_tiktok

    prompt = f"""Analysiere diesen Social-Media-Post-Entwurf fuer TREFF Sprachreisen und gib Engagement-Boost-Vorschlaege:

PLATTFORM: {platform}
FORMAT: {post_format}
KATEGORIE: {category}
LAND: {country or 'Nicht angegeben'}
TON: {tone or 'Nicht angegeben'}
GEPLANTE POSTING-ZEIT: {posting_time or 'Nicht angegeben'}

SLIDE-INHALTE:
{slides_summary}

CAPTION:
{caption or 'Keine Caption vorhanden'}

HASHTAGS:
{hashtags or 'Keine Hashtags vorhanden'}

CTA:
{cta_text or 'Kein CTA vorhanden'}

ANZAHL SLIDES: {len(slides)}

Gib 2-6 konkrete Verbesserungsvorschlaege als JSON-Array zurueck, sortiert nach Priority (high zuerst).
Jeder Vorschlag hat: priority, category, suggestion, estimated_boost, action_text."""

    return prompt


async def _generate_engagement_boost_with_gemini(
    post_content: dict,
    platform: str,
    post_format: str,
    posting_time: str | None,
    api_key: str,
) -> list[dict] | None:
    """Generate engagement boost suggestions using Gemini 2.5 Flash."""
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        system_prompt = _build_engagement_boost_system_prompt()
        content_prompt = _build_engagement_boost_content_prompt(
            post_content, platform, post_format, posting_time
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=content_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                temperature=0.7,
                max_output_tokens=2048,
            ),
        )

        if not response.text:
            logger.warning("Empty response from Gemini for engagement boost")
            return None

        suggestions = json.loads(response.text)

        # Validate structure
        if not isinstance(suggestions, list):
            logger.warning("Gemini engagement boost response is not a list")
            return None

        valid_priorities = {"high", "medium", "low"}
        valid_categories = {"hook", "cta", "length", "hashtags", "timing", "format", "emotion", "interaction"}

        validated = []
        for s in suggestions[:6]:  # Max 6 suggestions
            if not isinstance(s, dict):
                continue
            suggestion = {
                "priority": s.get("priority", "medium") if s.get("priority") in valid_priorities else "medium",
                "category": s.get("category", "interaction") if s.get("category") in valid_categories else "interaction",
                "suggestion": str(s.get("suggestion", ""))[:500],
                "estimated_boost": str(s.get("estimated_boost", "+5%"))[:10],
                "action_text": str(s.get("action_text", "Anwenden"))[:50],
            }
            if suggestion["suggestion"]:
                validated.append(suggestion)

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        validated.sort(key=lambda x: priority_order.get(x["priority"], 1))

        return validated if validated else None

    except Exception as e:
        logger.warning(f"Gemini engagement boost generation failed: {e}")
        return None


def _generate_engagement_boost_rule_based(
    post_content: dict,
    platform: str,
    post_format: str,
    posting_time: str | None = None,
) -> list[dict]:
    """Generate rule-based engagement boost suggestions as fallback."""
    suggestions = []

    slides = post_content.get("slides", [])
    caption_instagram = post_content.get("caption_instagram", "")
    caption_tiktok = post_content.get("caption_tiktok", "")
    hashtags_instagram = post_content.get("hashtags_instagram", "")
    hashtags_tiktok = post_content.get("hashtags_tiktok", "")
    cta_text = post_content.get("cta_text", "")

    caption = caption_instagram if "instagram" in platform else caption_tiktok
    hashtags = hashtags_instagram if "instagram" in platform else hashtags_tiktok

    # Check hook strength
    if slides:
        headline = slides[0].get("headline", "")
        if len(headline) < 15:
            suggestions.append({
                "priority": "high",
                "category": "hook",
                "suggestion": "Die Headline ist sehr kurz. Ein laengerer, emotionalerer Hook wie eine Frage oder ein ueberraschendes Fakt erzeugt mehr Aufmerksamkeit und stoppt den Scroll-Daumen.",
                "estimated_boost": "+20%",
                "action_text": "Hook verstaerken",
            })
        elif "?" not in headline and "!" not in headline:
            suggestions.append({
                "priority": "medium",
                "category": "hook",
                "suggestion": "Nutze eine Frage oder einen Ausruf in der Headline, um Neugier zu wecken. Fragen erhoehen die Kommentarrate um bis zu 150%.",
                "estimated_boost": "+15%",
                "action_text": "Frage einbauen",
            })

    # Check CTA
    if not cta_text and not any(s.get("cta_text") for s in slides):
        suggestions.append({
            "priority": "high",
            "category": "cta",
            "suggestion": "Es fehlt ein Call-to-Action. Fuege z.B. 'Link in Bio fuer mehr Infos!', 'Speichere diesen Post!' oder 'Markiere jemanden, der das braucht!' hinzu.",
            "estimated_boost": "+25%",
            "action_text": "CTA hinzufuegen",
        })

    # Check caption length
    if caption:
        caption_len = len(caption)
        if "instagram" in platform:
            if caption_len < 100:
                suggestions.append({
                    "priority": "medium",
                    "category": "length",
                    "suggestion": "Die Caption ist recht kurz. Instagram belohnt laengere Captions (150-300 Zeichen), da sie die Verweildauer erhoehen und dem Algorithmus signalisieren, dass der Content wertvoll ist.",
                    "estimated_boost": "+10%",
                    "action_text": "Caption erweitern",
                })
            elif caption_len > 500:
                suggestions.append({
                    "priority": "low",
                    "category": "length",
                    "suggestion": "Die Caption ist sehr lang. Kuerze sie auf die wichtigsten Punkte und verschiebe Details in die Kommentare oder die Story.",
                    "estimated_boost": "+5%",
                    "action_text": "Caption kuerzen",
                })
        elif "tiktok" in platform:
            if caption_len > 200:
                suggestions.append({
                    "priority": "medium",
                    "category": "length",
                    "suggestion": "TikTok-Captions sollten kurz und knackig sein (unter 150 Zeichen). Der Fokus liegt auf dem Video, nicht auf der Beschreibung.",
                    "estimated_boost": "+10%",
                    "action_text": "Caption kuerzen",
                })
    else:
        suggestions.append({
            "priority": "high",
            "category": "length",
            "suggestion": "Es fehlt eine Caption. Eine gute Caption mit Storytelling-Elementen und einem Call-to-Action ist essentiell fuer Engagement.",
            "estimated_boost": "+20%",
            "action_text": "Caption schreiben",
        })

    # Check hashtags
    if hashtags:
        hashtag_count = hashtags.count("#")
        if "instagram" in platform:
            if hashtag_count < 5:
                suggestions.append({
                    "priority": "medium",
                    "category": "hashtags",
                    "suggestion": f"Nur {hashtag_count} Hashtags. Fuer optimale Reichweite nutze 10-15 relevante Hashtags. Mische populaere (#Auslandsjahr, #HighSchool) mit Nischen-Hashtags (#TREFFSprachreisen).",
                    "estimated_boost": "+15%",
                    "action_text": "Hashtags ergaenzen",
                })
            elif hashtag_count > 25:
                suggestions.append({
                    "priority": "low",
                    "category": "hashtags",
                    "suggestion": f"{hashtag_count} Hashtags sind zu viele. Instagram empfiehlt 3-5 hochrelevante Hashtags fuer maximale Reichweite.",
                    "estimated_boost": "+5%",
                    "action_text": "Hashtags reduzieren",
                })
    else:
        suggestions.append({
            "priority": "high",
            "category": "hashtags",
            "suggestion": "Keine Hashtags vorhanden! Hashtags sind essentiell fuer die Auffindbarkeit. Fuege mindestens 5-10 relevante Hashtags hinzu.",
            "estimated_boost": "+25%",
            "action_text": "Hashtags hinzufuegen",
        })

    # Check posting time
    if posting_time:
        try:
            hour = int(posting_time.split(":")[0])
            if hour < 7 or hour > 21:
                suggestions.append({
                    "priority": "medium",
                    "category": "timing",
                    "suggestion": f"Posting um {posting_time} Uhr ist suboptimal. Die beste Posting-Zeit fuer deutsche Teenager ist 17-19 Uhr (nach der Schule) oder 12-13 Uhr (Mittagspause).",
                    "estimated_boost": "+15%",
                    "action_text": "Zeit anpassen",
                })
            elif 9 <= hour <= 14:
                suggestions.append({
                    "priority": "low",
                    "category": "timing",
                    "suggestion": f"Posting um {posting_time} Uhr erreicht eure Zielgruppe waehrend der Schulzeit. Teste alternativ 17-19 Uhr fuer hoehere Engagement-Raten.",
                    "estimated_boost": "+10%",
                    "action_text": "Abendzeit testen",
                })
        except (ValueError, IndexError):
            pass

    # Check format
    if post_format == "instagram_feed" and slides and len(slides) == 1:
        suggestions.append({
            "priority": "medium",
            "category": "format",
            "suggestion": "Carousel-Posts (mehrere Slides) erhalten auf Instagram bis zu 3x mehr Engagement als einzelne Bilder. Erweitere den Post um 3-5 Slides mit verschiedenen Aspekten des Themas.",
            "estimated_boost": "+20%",
            "action_text": "Carousel erstellen",
        })
    elif post_format == "instagram_feed" and slides and len(slides) > 8:
        suggestions.append({
            "priority": "low",
            "category": "format",
            "suggestion": f"{len(slides)} Slides koennen ueberfordernd wirken. Die optimale Carousel-Laenge liegt bei 5-7 Slides. Fasse die wichtigsten Punkte zusammen.",
            "estimated_boost": "+5%",
            "action_text": "Slides reduzieren",
        })

    # Check interaction elements
    has_question = any(
        "?" in (s.get("headline", "") + s.get("body_text", ""))
        for s in slides
    )
    if not has_question and caption and "?" not in caption:
        suggestions.append({
            "priority": "medium",
            "category": "interaction",
            "suggestion": "Fuege eine Frage am Ende der Caption hinzu, z.B. 'In welches Land wuerdest du gehen?' oder 'Wer war schon im Ausland?'. Fragen erhoehen die Kommentarrate signifikant.",
            "estimated_boost": "+15%",
            "action_text": "Frage hinzufuegen",
        })

    # Ensure at least 2 suggestions
    if len(suggestions) < 2:
        suggestions.append({
            "priority": "low",
            "category": "emotion",
            "suggestion": "Erwaehne persoenliche Erfahrungen oder Zitate von ehemaligen Teilnehmern. Authentischer Content erzeugt mehr emotionale Resonanz und wird haeufiger geteilt.",
            "estimated_boost": "+10%",
            "action_text": "Story einbauen",
        })
    if len(suggestions) < 2:
        suggestions.append({
            "priority": "low",
            "category": "interaction",
            "suggestion": "Fuege 'Speichere diesen Post fuer spaeter!' in die Caption ein. Save-Aufrufe erhoehen die Reichweite, da Instagram Saves als starkes Engagement-Signal wertet.",
            "estimated_boost": "+10%",
            "action_text": "Save-Aufruf hinzufuegen",
        })

    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    suggestions.sort(key=lambda x: priority_order.get(x["priority"], 1))

    return suggestions[:6]


@router.post("/engagement-boost")
async def engagement_boost(
    request: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Analyze a post draft and return engagement improvement suggestions.

    Uses Gemini 2.5 Flash for AI-powered analysis when available,
    with comprehensive rule-based fallback.

    Expects:
    - post_content (dict): Post data with slides, captions, hashtags, cta_text, category, country, tone
    - platform (str): Target platform (instagram_feed, instagram_story, tiktok)
    - format (str): Post format (same as platform or specific format)
    - posting_time (str, optional): Planned posting time (HH:MM)

    Returns list of engagement boost suggestions with priority, category,
    suggestion text, estimated boost percentage, and action text.
    """
    ai_rate_limiter.check_rate_limit(user_id, "engagement-boost")

    post_content = request.get("post_content", {})
    platform = request.get("platform", "instagram_feed")
    post_format = request.get("format", platform)
    posting_time = request.get("posting_time")

    if not post_content:
        raise HTTPException(
            status_code=400,
            detail="post_content is required. Provide slides, captions, hashtags, etc."
        )

    # Try Gemini first
    api_key = await _get_gemini_api_key(user_id, db)
    suggestions = None
    source = "rule_based"

    if api_key:
        suggestions = await _generate_engagement_boost_with_gemini(
            post_content=post_content,
            platform=platform,
            post_format=post_format,
            posting_time=posting_time,
            api_key=api_key,
        )
        if suggestions:
            source = "gemini"

    # Fallback to rule-based
    if not suggestions:
        suggestions = _generate_engagement_boost_rule_based(
            post_content=post_content,
            platform=platform,
            post_format=post_format,
            posting_time=posting_time,
        )

    return {
        "status": "success",
        "suggestions": suggestions,
        "count": len(suggestions),
        "source": source,
        "platform": platform,
        "format": post_format,
    }
