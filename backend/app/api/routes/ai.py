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
from app.models.story_arc import StoryArc
from app.models.story_episode import StoryEpisode
from app.models.recurring_format import RecurringFormat

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
from app.core.paths import get_upload_dir
ASSETS_UPLOAD_DIR = get_upload_dir("assets")


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
    Returns PNG bytes or None (caller falls back to local placeholder).
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
            aspect_ratio=aspect_ratio,
            image_size=image_size,
        )

        logger.info(
            f"Trying Nano Banana Pro (gemini-3-pro-image-preview) with "
            f"aspect_ratio={aspect_ratio}, image_size={image_size}"
        )

        response = client.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
                image_config=image_config,
            ),
        )

        # Extract image bytes from response parts
        if response.candidates:
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.data:
                    logger.info("Nano Banana Pro image generation succeeded")
                    return part.inline_data.data

        logger.warning("Nano Banana Pro returned no image")
        return None

    except Exception as e:
        logger.warning(f"Nano Banana Pro (gemini-3-pro-image-preview) failed: {e}")
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


@router.post("/adapt-for-platform")
async def adapt_text_for_platform(
    request: dict,
    user_id: int = Depends(get_current_user_id),
):
    """Adapt existing text content for a different platform.

    Takes text that was written for one platform and adapts it for another.
    For example: Instagram Feed caption -> Instagram Story caption -> TikTok caption.

    Body:
    - original_text: str - The original text to adapt
    - source_platform: str - Platform the text was written for
    - target_platform: str - Platform to adapt the text for
    - category: str (optional) - Content category for context
    - tone: str (optional) - Tone to maintain
    """
    original_text = request.get("original_text", "")
    source_platform = request.get("source_platform", "instagram_feed")
    target_platform = request.get("target_platform", "tiktok")
    category = request.get("category", "")
    tone = request.get("tone", "jugendlich")

    if not original_text:
        raise HTTPException(status_code=400, detail="original_text is required")

    platform_guidelines = {
        "instagram_feed": "Instagram Feed: Laengere Captions (bis 2200 Zeichen), Hashtags am Ende, informativ/storytelling, Call-to-Action",
        "instagram_story": "Instagram Story: Kurz und knackig (max 100 Zeichen), CTA mit Swipe-Up/Link, 1-2 Emojis, Frage oder Poll zum Interagieren",
        "tiktok": "TikTok: Hook-fokussiert (erste 3 Sekunden entscheidend), kurz (max 150 Zeichen), trendige Sprache, Hashtags inline, weniger Emojis",
    }

    source_desc = platform_guidelines.get(source_platform, source_platform)
    target_desc = platform_guidelines.get(target_platform, target_platform)

    try:
        from app.core.text_generator import generate_text_with_gemini
        prompt = f"""Du bist ein Social-Media-Experte fuer TREFF Sprachreisen (Highschool-Aufenthalte im Ausland).

AUFGABE: Adaptiere den folgenden Text von {source_platform} fuer {target_platform}.

ORIGINALTEXT ({source_platform}):
{original_text}

ZIELPLATTFORM-REGELN ({target_platform}):
{target_desc}

TONALITAET: {tone}
{"KATEGORIE: " + category if category else ""}

WICHTIG:
- Behalte die Kernaussage bei
- Passe Laenge, Stil und Format an die Zielplattform an
- Alle Texte auf Deutsch
- Gib NUR den adaptierten Text zurueck, keine Erklaerung"""

        result = await generate_text_with_gemini(
            prompt=prompt,
            platform=target_platform,
            tone=tone,
        )

        adapted_text = ""
        if isinstance(result, dict):
            adapted_text = result.get("caption", result.get("text", str(result)))
        else:
            adapted_text = str(result)

        return {
            "adapted_text": adapted_text.strip(),
            "source_platform": source_platform,
            "target_platform": target_platform,
        }
    except Exception as e:
        # Fallback: simple rule-based adaptation
        adapted = original_text
        if target_platform == "instagram_story":
            # Shorten for stories
            sentences = original_text.split('. ')
            adapted = '. '.join(sentences[:2]) + ('...' if len(sentences) > 2 else '')
            if len(adapted) > 120:
                adapted = adapted[:117] + '...'
        elif target_platform == "tiktok":
            # Hook-focused for TikTok
            sentences = original_text.split('. ')
            adapted = sentences[0] + (' ' + sentences[1] if len(sentences) > 1 else '')
            if len(adapted) > 150:
                adapted = adapted[:147] + '...'

        return {
            "adapted_text": adapted.strip(),
            "source_platform": source_platform,
            "target_platform": target_platform,
            "fallback": True,
        }


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
        from app.core.paths import save_and_encode

        unique_filename = f"ai_{uuid.uuid4().hex[:12]}.png"
        file_path = ASSETS_UPLOAD_DIR / unique_filename

        b64 = save_and_encode(image_bytes, file_path)

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
            file_data=b64,
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

    # Optimal posting times for German teenagers (from social content strategy)
    # Weekday best times: 17:00-20:00, Weekend best times: 11:00-14:00
    optimal_times_weekday = ["17:00", "18:00", "19:00", "20:00", "17:30"]
    optimal_times_weekend = ["11:00", "12:00", "13:00", "14:00", "11:30"]

    # Platforms to rotate (balanced mix per social content strategy)
    platforms = ["instagram_feed", "instagram_stories", "tiktok", "instagram_feed", "instagram_reels", "instagram_stories", "tiktok"]

    # Recurring content slot themes from social strategy (for enriching topic suggestions)
    recurring_slots = {
        0: {"theme": "Motivation Monday", "preferred_category": "tipps_tricks"},
        1: {"theme": "Tipps Tuesday", "preferred_category": "tipps_tricks"},
        3: {"theme": "Throwback Thursday", "preferred_category": "erfahrungsberichte"},
        4: {"theme": "Freitags-Reel", "preferred_platform": "instagram_reels"},
        5: {"theme": "Samstags-Story-Serie", "preferred_platform": "instagram_stories"},
    }

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

    # Hook formula templates from social content strategy for topic enrichment
    hook_templates = {
        "laender_spotlight": [
            "Was ich gerne VOR meinem Aufenthalt in {country} gewusst haette...",
            "{country}: 5 Dinge die dich ueberraschen werden",
            "So sieht ein Schultag in {country} WIRKLICH aus",
        ],
        "erfahrungsberichte": [
            "Mein emotionalstes Erlebnis in {country}",
            "POV: Dein erster Tag an einer High School in {country}",
            "Erwartung vs. Realitaet: Mein Auslandsjahr in {country}",
        ],
        "infografiken": [
            "{country} in Zahlen: Die wichtigsten Fakten",
            "USA vs. Kanada: Der ehrliche Vergleich",
            "Was kostet ein Auslandsjahr? Alle Zahlen auf einen Blick",
        ],
        "fristen_cta": [
            "Nur noch wenige Plaetze fuer {country}!",
            "Bewerbungsschluss naht! Jetzt noch Platz sichern",
            "LETZTE CHANCE: {country} Plaetze fast ausgebucht!",
        ],
        "tipps_tricks": [
            "5 Tipps, die ich vor meinem Auslandsjahr gebraucht haette",
            "Packliste: Diese Dinge haetten wir gern vorher gewusst",
            "So bereitest du dich optimal vor",
        ],
        "faq": [
            "Die 3 haeufigsten Fragen zum Auslandsjahr - ehrlich beantwortet",
            "MYTHOS: Ein Auslandsjahr ist nur was fuer Reiche. Die Wahrheit...",
            "Deine Eltern haben Fragen? Wir haben Antworten",
        ],
        "foto_posts": [
            "Impressionen aus {country} - echte Momente, echte Erlebnisse",
            "So sieht Highschool in {country} wirklich aus",
            "TREFF-Schueler unterwegs in {country}",
        ],
    }

    plan = []
    for i, day_offset in enumerate(post_days):
        post_date = next_monday + timedelta(days=day_offset)
        day_name = day_names_de[day_offset]
        is_weekend = day_offset >= 5  # Saturday=5, Sunday=6

        # Pick category and country (rotate through underrepresented ones)
        category = sorted_categories[i % len(sorted_categories)]
        country = sorted_countries[i % len(sorted_countries)]
        platform = platforms[i % len(platforms)]

        # Use weekday/weekend optimal times from social content strategy
        if is_weekend:
            time = optimal_times_weekend[i % len(optimal_times_weekend)]
        else:
            time = optimal_times_weekday[i % len(optimal_times_weekday)]

        # Apply recurring content slot preferences from social strategy
        slot = recurring_slots.get(day_offset)
        if slot:
            if "preferred_category" in slot and slot["preferred_category"] in ALL_CATEGORIES:
                category = slot["preferred_category"]
            if "preferred_platform" in slot:
                platform = slot["preferred_platform"]

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

            # Use hook-formula-inspired topic ideas from social content strategy
            cat_hooks = hook_templates.get(category, [])
            if cat_hooks:
                hook = random.choice(cat_hooks).replace("{country}", country_name)
                topic = hook
            else:
                topic = f"{cat_name} ueber {country_name}"

            # Add recurring slot theme to reason if applicable
            slot_info = recurring_slots.get(day_offset)
            if slot_info:
                reason = f"{slot_info['theme']}: {cat_name} + {country_name} (Social-Content-Strategie)"
            else:
                reason = f"Content-Mix: {cat_name} + {country_name} fuer ausgewogene Praesenz"

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

Deine Aufgabe ist es, einen kompletten Wochenplan fuer Social Media zu erstellen. Der Plan basiert auf der TREFF Social-Content-Strategie:

PLATTFORM-SPEZIFISCHE REGELN:
- Instagram Feed: 3-5 Posts/Woche, beste Zeiten Werktags 17-20 Uhr, Wochenende 11-14 Uhr
- Instagram Stories: Taeglich, beste Zeiten 07:30, 12:00, 17:30, 20:00
- Instagram Reels: 2-3/Woche, beste Zeiten Werktags 18-20 Uhr, Wochenende 11-15 Uhr
- TikTok: 1-2x taeglich, beste Zeiten Werktags 16-21 Uhr, Wochenende 10-19 Uhr

WOECHENTLICHE CONTENT-SLOTS (Empfehlung):
- Montag: Motivation Monday (motivierender Content)
- Dienstag: Tipps Tuesday (praktische Tipps oder FAQ)
- Donnerstag: Throwback Thursday (Alumni-Fotos/-Geschichten)
- Freitag: Freitags-Reel (unterhaltsames Reel: Cultural Shock, Erwartung vs. Realitaet)
- Samstag: Samstags-Story-Serie (Story mit Umfragen und Quiz)

HOOK-FORMELN (die erste Zeile/die ersten Sekunden MUESSEN fesseln):
- Wissensluecke: "Was ich gerne VOR meinem Auslandsjahr gewusst haette..."
- Vergleich: "USA vs. Kanada: Welches Land passt zu dir?"
- Mythos-Entlarvung: "MYTHOS: Ein Auslandsjahr ist nur was fuer Reiche."
- POV: "POV: Dein erster Tag an einer amerikanischen High School"
- Erwartung vs. Realitaet: "Erwartung: US High Schools sind wie in den Filmen..."

CONTENT-MIX REGELN:
- Mindestens 3 verschiedene Kategorien pro Woche
- Mindestens 2 verschiedene Laender pro Woche
- Mindestens 2 verschiedene Plattformen pro Woche
- Nicht dasselbe Land an aufeinanderfolgenden Tagen
- Nicht dieselbe Kategorie an aufeinanderfolgenden Tagen
- Fristen-Post einplanen wenn Deadline innerhalb von 14 Tagen

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
# Series-Aware Weekly Content Planner (Feature #204)
# ═══════════════════════════════════════════════════════════════════════

RECURRING_FORMATS = [
    {"day": "Montag", "day_idx": 0, "label": "Motivation Monday", "category": "tipps_tricks", "icon": "💪"},
    {"day": "Dienstag", "day_idx": 1, "label": "Story/Serie Episoden-Tag", "category": "erfahrungsberichte", "icon": "📖"},
    {"day": "Mittwoch", "day_idx": 2, "label": "Laender-Spotlight", "category": "laender_spotlight", "icon": "🌍"},
    {"day": "Donnerstag", "day_idx": 3, "label": "Throwback Thursday", "category": "foto_posts", "icon": "📸"},
    {"day": "Freitag", "day_idx": 4, "label": "Freitags-Fail / Fun Facts", "category": "faq", "icon": "😂"},
    {"day": "Samstag", "day_idx": 5, "label": "Behind-the-Scenes", "category": "erfahrungsberichte", "icon": "🎬"},
    {"day": "Sonntag", "day_idx": 6, "label": "Teaser fuer naechste Woche", "category": "tipps_tricks", "icon": "👀"},
]


@router.post("/weekly-planner")
async def weekly_planner(
    request: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Series-aware AI weekly content planner.

    Generates a complete week plan considering:
    - Active story arcs (next episode scheduling)
    - Recurring formats (Motivation Monday, Freitags-Fail, etc.)
    - Seasonal events (TREFF deadlines)
    - Country balance
    - Posting frequency goals

    Expects:
    - week_start (str, optional): ISO date for the Monday of the target week. Defaults to next Monday.
    - posts_per_week (int, optional): Target posts (2-7, default 5)
    - include_recurring (bool, optional): Include recurring format suggestions (default true)
    - include_series (bool, optional): Include story arc episodes (default true)

    Returns the weekly plan as an array of day slots (Mo-So) with suggested posts.
    """
    today = date.today()
    season = SEASON_NAMES.get(today.month, "Fruehling")

    # Parse week_start
    week_start_str = request.get("week_start")
    if week_start_str:
        try:
            week_start = date.fromisoformat(week_start_str)
            # Snap to Monday
            week_start = week_start - timedelta(days=week_start.weekday())
        except (ValueError, TypeError):
            week_start = None

    if not week_start_str or week_start is None:
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        week_start = today + timedelta(days=days_until_monday)

    week_end = week_start + timedelta(days=6)

    # Parse options
    posts_per_week = max(2, min(7, int(request.get("posts_per_week", 5))))
    include_recurring = request.get("include_recurring", True)
    include_series = request.get("include_series", True)

    # Fetch active story arcs
    active_arcs = []
    if include_series:
        arcs_result = await db.execute(
            select(StoryArc).where(
                StoryArc.user_id == user_id,
                StoryArc.status == "active",
            )
        )
        arcs = arcs_result.scalars().all()
        for arc in arcs:
            # Find current episode number (last scheduled episode)
            last_ep_result = await db.execute(
                select(func.max(Post.episode_number)).where(
                    Post.user_id == user_id,
                    Post.story_arc_id == arc.id,
                )
            )
            last_ep = last_ep_result.scalar() or 0
            next_ep = last_ep + 1
            if next_ep <= (arc.planned_episodes or 999):
                active_arcs.append({
                    "id": arc.id,
                    "title": arc.title,
                    "country": arc.country,
                    "tone": arc.tone,
                    "student_id": arc.student_id,
                    "planned_episodes": arc.planned_episodes,
                    "next_episode": next_ep,
                })

    # Fetch recent posts for context
    recent_result = await db.execute(
        select(Post.category, Post.country, Post.platform)
        .where(Post.user_id == user_id)
        .order_by(Post.created_at.desc())
        .limit(20)
    )
    recent_posts = recent_result.all()
    recent_categories = [r[0] for r in recent_posts if r[0]]
    recent_countries = [r[1] for r in recent_posts if r[1]]

    # Fetch existing posts for target week (to avoid double-scheduling)
    from datetime import datetime as dt
    existing_result = await db.execute(
        select(Post).where(
            Post.user_id == user_id,
            Post.scheduled_date.isnot(None),
            Post.scheduled_date >= dt(week_start.year, week_start.month, week_start.day),
            Post.scheduled_date <= dt(week_end.year, week_end.month, week_end.day, 23, 59, 59),
        )
    )
    existing_posts = existing_result.scalars().all()
    existing_dates = set()
    for ep in existing_posts:
        if ep.scheduled_date:
            existing_dates.add(ep.scheduled_date.strftime("%Y-%m-%d"))

    # Get upcoming deadlines
    upcoming_deadlines = _get_upcoming_deadlines(today, lookahead_days=30)

    # Build the weekly plan
    day_names = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
    optimal_times_weekday = ["17:30", "18:00", "19:00", "18:30", "17:00"]
    optimal_times_weekend = ["11:00", "12:00", "13:00"]

    # Build 7 day slots
    day_slots = []
    for i in range(7):
        slot_date = week_start + timedelta(days=i)
        is_weekend = i >= 5
        day_slots.append({
            "day": day_names[i],
            "day_index": i,
            "date": slot_date.isoformat(),
            "is_weekend": is_weekend,
            "existing_posts": [
                {
                    "id": p.id,
                    "title": p.title,
                    "category": p.category,
                    "platform": p.platform,
                    "country": p.country,
                }
                for p in existing_posts
                if p.scheduled_date and p.scheduled_date.strftime("%Y-%m-%d") == slot_date.isoformat()
            ],
            "suggestions": [],
        })

    # Assign posts to days
    assigned_count = 0

    # 1) Insert story arc episodes first (they have priority)
    if include_series and active_arcs:
        # Assign episodes to Tuesday (story day) or next available
        preferred_arc_day = 1  # Dienstag
        for arc in active_arcs:
            if assigned_count >= posts_per_week:
                break
            # Find best day for this episode
            target_day = preferred_arc_day
            for offset in [0, 2, 4, 1, 3, 5, 6]:  # Try preferred, then others
                candidate = (preferred_arc_day + offset) % 7
                slot = day_slots[candidate]
                if not slot["suggestions"] and not slot["existing_posts"]:
                    target_day = candidate
                    break

            slot = day_slots[target_day]
            time_str = optimal_times_weekend[0] if slot["is_weekend"] else optimal_times_weekday[0]
            country_name = COUNTRY_NAMES.get(arc["country"], arc["country"] or "")

            slot["suggestions"].append({
                "type": "series_episode",
                "category": "erfahrungsberichte",
                "country": arc["country"] or "usa",
                "platform": "instagram_stories",
                "time": time_str,
                "topic": f"Story-Arc: {arc['title']} - Episode {arc['next_episode']}",
                "reason": f"Naechste Episode der laufenden Serie '{arc['title']}' ({country_name})",
                "icon": "📖",
                "story_arc_id": arc["id"],
                "episode_number": arc["next_episode"],
                "is_recurring": False,
                "is_series": True,
            })
            assigned_count += 1
            preferred_arc_day += 2  # Space out multiple arcs

    # 2) Insert recurring formats (from database)
    DAY_NAME_TO_IDX = {
        "Montag": 0, "Dienstag": 1, "Mittwoch": 2, "Donnerstag": 3,
        "Freitag": 4, "Samstag": 5, "Sonntag": 6,
    }
    db_recurring_formats = []
    if include_recurring:
        from sqlalchemy import or_ as sql_or
        rf_result = await db.execute(
            select(RecurringFormat).where(
                RecurringFormat.is_active == True,
                sql_or(
                    RecurringFormat.user_id == None,
                    RecurringFormat.user_id == user_id,
                ),
            )
        )
        db_recurring_formats = rf_result.scalars().all()

        for fmt in db_recurring_formats:
            if assigned_count >= posts_per_week:
                break
            day_idx = DAY_NAME_TO_IDX.get(fmt.preferred_day, None)
            if day_idx is None:
                continue
            slot = day_slots[day_idx]
            if slot["suggestions"] or slot["existing_posts"]:
                continue  # Already has content

            time_str = fmt.preferred_time or (optimal_times_weekend[day_idx - 5] if slot["is_weekend"] else optimal_times_weekday[day_idx % len(optimal_times_weekday)])

            # Pick an underrepresented country
            country_counts = {c: recent_countries.count(c) for c in ALL_COUNTRIES}
            sorted_c = sorted(ALL_COUNTRIES, key=lambda c: country_counts.get(c, 0))
            country = sorted_c[assigned_count % len(sorted_c)]
            country_name = COUNTRY_NAMES.get(country, country)

            # Override with deadline country if a deadline is coming
            reason = f"Wiederkehrendes Format: {fmt.name}"
            topic = f"{fmt.name}: {country_name}"

            fmt_category = fmt.category or "tipps_tricks"
            if fmt_category == "faq" and day_idx == 4:
                topic = f"Freitags-Fail: Lustige Anekdoten aus {country_name}"
            elif fmt_category == "tipps_tricks" and day_idx == 0:
                topic = f"Motivation Monday: Warum {country_name} dein Leben veraendert"
            elif fmt_category == "laender_spotlight" and day_idx == 2:
                topic = f"Laender-Spotlight: {country_name} - Top 5 Highlights"
            elif fmt_category == "erfahrungsberichte" and day_idx == 3:
                topic = f"Throwback Thursday: Erinnerungen an {country_name}"

            # Check for deadline override
            for dl in upcoming_deadlines:
                dl_date = dl["date"]
                if dl_date >= week_start and dl_date <= week_end:
                    if slot["date"] == dl_date.isoformat() or (not any(s.get("category") == "fristen_cta" for s in slot["suggestions"])):
                        if day_idx in [0, 2, 4]:  # Override on Mon/Wed/Fri
                            topic = f"Frist beachten: {dl['label']}"
                            reason = f"Bevorstehende Frist: {dl['label']} am {dl['date'].strftime('%d.%m.%Y')}"
                            break

            platforms = ["instagram_feed", "instagram_stories", "tiktok", "instagram_reels"]
            platform = platforms[assigned_count % len(platforms)]

            slot["suggestions"].append({
                "type": "recurring",
                "category": fmt_category,
                "country": country,
                "platform": platform,
                "time": time_str,
                "topic": topic,
                "reason": reason,
                "icon": fmt.icon or "🔄",
                "story_arc_id": None,
                "episode_number": None,
                "is_recurring": True,
                "is_series": False,
                "recurring_format_id": fmt.id,
            })
            assigned_count += 1

    # 3) Fill remaining slots with AI-balanced suggestions
    if assigned_count < posts_per_week:
        country_counts = {c: recent_countries.count(c) for c in ALL_COUNTRIES}
        sorted_countries = sorted(ALL_COUNTRIES, key=lambda c: country_counts.get(c, 0))
        cat_counts = {c: recent_categories.count(c) for c in ALL_CATEGORIES}
        sorted_cats = sorted(ALL_CATEGORIES, key=lambda c: cat_counts.get(c, 0))

        fill_idx = 0
        for slot in day_slots:
            if assigned_count >= posts_per_week:
                break
            if slot["suggestions"] or slot["existing_posts"]:
                continue

            category = sorted_cats[fill_idx % len(sorted_cats)]
            country = sorted_countries[fill_idx % len(sorted_countries)]
            country_name = COUNTRY_NAMES.get(country, country)
            cat_name = CATEGORY_DISPLAY.get(category, category)
            platforms = ["instagram_feed", "instagram_stories", "tiktok", "instagram_reels"]
            platform = platforms[fill_idx % len(platforms)]
            time_str = optimal_times_weekend[0] if slot["is_weekend"] else optimal_times_weekday[fill_idx % len(optimal_times_weekday)]

            topic_ideas = {
                "laender_spotlight": f"{country_name}-Spotlight: Highlights und Fakten",
                "erfahrungsberichte": f"Erfahrungsbericht aus {country_name}",
                "infografiken": f"Infografik: Highschool in {country_name}",
                "fristen_cta": f"Bewerbungsfristen fuer {country_name}",
                "tipps_tricks": f"Tipps fuer dein Auslandsjahr in {country_name}",
                "faq": f"FAQ: Haeufige Fragen zu {country_name}",
                "foto_posts": f"Foto-Impressionen aus {country_name}",
            }

            slot["suggestions"].append({
                "type": "balanced",
                "category": category,
                "country": country,
                "platform": platform,
                "time": time_str,
                "topic": topic_ideas.get(category, f"{cat_name}: {country_name}"),
                "reason": f"Content-Mix Optimierung: {cat_name} + {country_name}",
                "icon": "✨",
                "story_arc_id": None,
                "episode_number": None,
                "is_recurring": False,
                "is_series": False,
            })
            assigned_count += 1
            fill_idx += 1

    return {
        "status": "success",
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "day_slots": day_slots,
        "total_suggestions": assigned_count,
        "active_arcs": active_arcs,
        "posts_per_week": posts_per_week,
        "recurring_formats": [
            {
                "day": rf.preferred_day or "",
                "day_idx": DAY_NAME_TO_IDX.get(rf.preferred_day, -1),
                "label": rf.name,
                "category": rf.category or "tipps_tricks",
                "icon": rf.icon or "🔄",
                "id": rf.id,
            }
            for rf in db_recurring_formats
        ] if include_recurring else [],
        "season": season,
    }


@router.post("/weekly-planner/adopt")
async def adopt_weekly_plan(
    request: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Adopt a weekly plan: create draft posts for all selected plan items.

    Expects:
    - items: list of plan items to adopt, each with:
        - date (str): ISO date
        - time (str): HH:MM
        - category (str)
        - country (str)
        - platform (str)
        - topic (str)
        - story_arc_id (int, optional)
        - episode_number (int, optional)

    Returns the created posts.
    """
    items = request.get("items", [])
    if not items:
        raise HTTPException(status_code=400, detail="No items to adopt")

    created_posts = []
    for item in items:
        # Parse the scheduled date
        scheduled_date = None
        if item.get("date"):
            try:
                parsed = date.fromisoformat(item["date"])
                scheduled_date = datetime(parsed.year, parsed.month, parsed.day)
            except (ValueError, TypeError):
                pass

        post = Post(
            user_id=user_id,
            title=item.get("topic", "Geplanter Post")[:200],
            category=item.get("category", "laender_spotlight"),
            country=item.get("country", "usa"),
            platform=item.get("platform", "instagram_feed"),
            status="scheduled",
            scheduled_date=scheduled_date,
            scheduled_time=item.get("time", "18:00"),
            story_arc_id=item.get("story_arc_id"),
            episode_number=item.get("episode_number"),
            slide_data="[]",
            tone="jugendlich",
        )
        db.add(post)
        await db.flush()
        await db.refresh(post)
        created_posts.append({
            "id": post.id,
            "title": post.title,
            "category": post.category,
            "country": post.country,
            "platform": post.platform,
            "scheduled_date": post.scheduled_date.strftime("%Y-%m-%d") if post.scheduled_date else None,
            "scheduled_time": post.scheduled_time,
            "story_arc_id": post.story_arc_id,
            "episode_number": post.episode_number,
        })

    await db.commit()

    return {
        "status": "success",
        "created_posts": created_posts,
        "count": len(created_posts),
        "message": f"{len(created_posts)} Posts in den Kalender uebernommen!",
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


# ═══════════════════════════════════════════════════════════════════════
# Story-Arc Chapter/Episode Suggestions (Wizard)
# ═══════════════════════════════════════════════════════════════════════

# Default episode templates for a typical exchange year
TYPICAL_EXCHANGE_EPISODES = [
    {"title": "Ankunft & Erste Eindruecke", "description": "Der erste Tag im neuen Land - Flughafen, Gastfamilie, neue Umgebung"},
    {"title": "Erster Schultag", "description": "Neues Schulsystem, neue Mitschueler, erste Stunden - alles ist anders"},
    {"title": "Neue Freundschaften", "description": "Die ersten echten Kontakte und wie sich Freundschaften entwickeln"},
    {"title": "Homecoming / Schulfeier", "description": "Das erste grosse Event: Homecoming Dance, School Spirit und Traditionen"},
    {"title": "Herbst-Abenteuer", "description": "Herbstferien, Halloween, Thanksgiving-Vorbereitungen und Herbstfarben"},
    {"title": "Weihnachten in der Ferne", "description": "Weihnachten bei der Gastfamilie - Traditionen, Heimweh und neue Rituale"},
    {"title": "Halbzeit-Reflexion", "description": "Die Haelfte ist geschafft - Was hat sich veraendert? Was wurde gelernt?"},
    {"title": "Winter & Neues Semester", "description": "Neues Halbjahr, neue Kurse, Wintersport und kalte Tage"},
    {"title": "Fruehling & Aufbruch", "description": "Neue Energie, Fruehlings-Events, Spring Break Erlebnisse"},
    {"title": "Prom Night", "description": "Der grosse Abschlussball - Outfit, Date, unvergesslicher Abend"},
    {"title": "Graduation & Abschied", "description": "Abschlussfeier, letzte Tage, Abschiede von Freunden und Gastfamilie"},
    {"title": "Heimkehr & Rueckblick", "description": "Zurueck in Deutschland - Was bleibt? Was hat sich veraendert?"},
]

COUNTRY_SPECIFIC_EPISODES = {
    "usa": [
        {"title": "Football Friday Night", "description": "Das erste Friday Night Lights Erlebnis - Highschool Football hautnah"},
        {"title": "Thanksgiving mit der Gastfamilie", "description": "Turkey, Pie und Family Time - das amerikanischste aller Feste"},
        {"title": "Road Trip Adventure", "description": "Erster amerikanischer Road Trip - Highway, Diners und endlose Weite"},
    ],
    "kanada": [
        {"title": "Erster Schnee & Wintersport", "description": "Kanadas Winter erleben - Skifahren, Eishockey und Schneesturm"},
        {"title": "Thanksgiving auf Kanadisch", "description": "Kanadisches Erntedankfest im Oktober - anders als in den USA"},
        {"title": "Nature & Wildlife", "description": "Kanadas wilde Natur - Baeren, Wale und endlose Waelder"},
    ],
    "australien": [
        {"title": "Surf's Up!", "description": "Erste Surfstunde, Strandleben und die australische Outdoor-Kultur"},
        {"title": "Christmas am Strand", "description": "Weihnachten bei 35 Grad - BBQ statt Gaensebraten"},
        {"title": "Outback-Abenteuer", "description": "Rotes Land, Kängurus und die Weite des australischen Outbacks"},
    ],
    "neuseeland": [
        {"title": "Maori-Kultur erleben", "description": "Haka, Hangi und die faszinierende Kultur der Maori"},
        {"title": "Herr der Ringe Landschaften", "description": "Mittelerde in echt - atemberaubende Natur und Filmkulissen"},
        {"title": "Extremsport-Premiere", "description": "Bungee, Skydiving oder Rafting - Neuseeland ist Adrenalin pur"},
    ],
    "irland": [
        {"title": "Pub Culture & Irish Music", "description": "Traditionelle Musik, Irish Dance und die gemuetliche Pub-Atmosphaere"},
        {"title": "St. Patrick's Day", "description": "Das groesste irische Fest - Paraden, Gruen und nationale Begeisterung"},
        {"title": "Cliffs & Castles", "description": "Irlands wilde Kueste, historische Burgen und mystische Landschaften"},
    ],
}


@router.post("/suggest-arc-chapters")
async def suggest_arc_chapters(
    request: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Suggest chapter/episode structure for a new story arc.

    Request body:
    {
        "student_id": int (optional),
        "country": str (optional),
        "title": str (optional),
        "description": str (optional),
        "planned_episodes": int (default 8),
        "tone": str (default "jugendlich")
    }

    Returns:
    {
        "episodes": [{"number": 1, "title": "...", "description": "..."}],
        "source": "gemini" | "rule_based"
    }
    """
    ai_rate_limiter.check_rate_limit(user_id, "suggest-arc-chapters")

    student_id = request.get("student_id")
    country = request.get("country", "")
    title = request.get("title", "")
    description = request.get("description", "")
    planned_episodes = request.get("planned_episodes", 8)
    tone = request.get("tone", "jugendlich")

    # Clamp episodes
    planned_episodes = max(3, min(planned_episodes, 20))

    # Look up student info if provided
    student_name = None
    student_country = None
    student_start = None
    student_end = None
    if student_id:
        result = await db.execute(
            select(Student).where(Student.id == student_id, Student.user_id == user_id)
        )
        student = result.scalar_one_or_none()
        if student:
            student_name = student.name
            student_country = student.country
            student_start = student.start_date
            student_end = student.end_date
            if not country:
                country = student_country

    # Try AI generation first
    api_key = settings.GEMINI_API_KEY if hasattr(settings, "GEMINI_API_KEY") else os.environ.get("GEMINI_API_KEY", "")
    if api_key:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)

            country_names = {
                "usa": "USA", "kanada": "Kanada", "australien": "Australien",
                "neuseeland": "Neuseeland", "irland": "Irland"
            }
            country_name = country_names.get(country, country or "Ausland")

            student_context = ""
            if student_name:
                student_context = f"\nStudent: {student_name}"
                if student_start and student_end:
                    student_context += f" (Aufenthalt: {student_start.strftime('%B %Y')} bis {student_end.strftime('%B %Y')})"

            system_prompt = f"""Du bist Content-Planer fuer TREFF Sprachreisen.
Erstelle eine Kapitelstruktur fuer eine Instagram-Story-Serie ueber einen Highschool-Aufenthalt in {country_name}.
Der Ton soll {tone} sein.{student_context}

Jedes Kapitel soll:
- Einen praegnanten, emotionalen Titel haben
- Eine kurze Beschreibung (1 Satz) was in der Episode passiert
- Chronologisch zum typischen Ablauf eines Auslandsjahres passen
- Spannung aufbauen und zum Weiterlesen motivieren

Antworte NUR mit einem JSON-Array:
[{{"number": 1, "title": "...", "description": "..."}}, ...]"""

            user_prompt = f"Erstelle genau {planned_episodes} Kapitel"
            if title:
                user_prompt += f' fuer die Serie "{title}"'
            if description:
                user_prompt += f". Beschreibung: {description}"
            user_prompt += f" in {country_name}."

            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.8,
                    max_output_tokens=2000,
                ),
            )

            text = response.text.strip()
            # Extract JSON from response
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            episodes = json.loads(text)
            if isinstance(episodes, list) and len(episodes) > 0:
                # Ensure proper numbering
                for i, ep in enumerate(episodes):
                    ep["number"] = i + 1
                return {
                    "episodes": episodes[:planned_episodes],
                    "source": "gemini",
                }
        except Exception as e:
            logger.warning(f"Gemini arc chapter suggestion failed: {e}")

    # Fallback: rule-based episode suggestions
    episodes = []

    # Start with typical exchange episodes
    base_episodes = list(TYPICAL_EXCHANGE_EPISODES)

    # Insert country-specific episodes if available
    country_key = country.lower() if country else ""
    country_eps = COUNTRY_SPECIFIC_EPISODES.get(country_key, [])

    # Interleave country-specific episodes at appropriate positions
    if country_eps:
        # Insert after position 3, 5, 7
        insert_positions = [3, 5, 7]
        for i, pos in enumerate(insert_positions):
            if i < len(country_eps) and pos <= len(base_episodes):
                base_episodes.insert(pos + i, country_eps[i])

    # Select the requested number of episodes
    selected = base_episodes[:planned_episodes]

    for i, ep in enumerate(selected):
        episodes.append({
            "number": i + 1,
            "title": ep["title"],
            "description": ep["description"],
        })

    return {
        "episodes": episodes,
        "source": "rule_based",
    }


@router.post("/suggest-arc-title")
async def suggest_arc_title(
    request: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Suggest title and description for a story arc based on student and country.

    Request body:
    {
        "student_id": int (optional),
        "country": str (optional),
        "tone": str (default "jugendlich")
    }

    Returns:
    {
        "suggestions": [{"title": "...", "subtitle": "...", "description": "..."}],
        "source": "gemini" | "rule_based"
    }
    """
    ai_rate_limiter.check_rate_limit(user_id, "suggest-arc-title")

    student_id = request.get("student_id")
    country = request.get("country", "")
    tone = request.get("tone", "jugendlich")

    # Look up student
    student_name = None
    if student_id:
        result = await db.execute(
            select(Student).where(Student.id == student_id, Student.user_id == user_id)
        )
        student = result.scalar_one_or_none()
        if student:
            student_name = student.name
            if not country:
                country = student.country

    country_names = {
        "usa": "USA", "kanada": "Kanada", "australien": "Australien",
        "neuseeland": "Neuseeland", "irland": "Irland"
    }
    country_name = country_names.get(country, country or "Ausland")

    # Try AI generation
    api_key = settings.GEMINI_API_KEY if hasattr(settings, "GEMINI_API_KEY") else os.environ.get("GEMINI_API_KEY", "")
    if api_key:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)

            name_context = f" ueber {student_name}" if student_name else ""
            system_prompt = f"""Du bist Content-Planer fuer TREFF Sprachreisen.
Erstelle 3 Vorschlaege fuer den Titel einer Instagram-Story-Serie{name_context} in {country_name}.
Ton: {tone}

Jeder Vorschlag soll enthalten:
- title: Ein kurzer, einpraegsamer Serientitel (max 40 Zeichen)
- subtitle: Ein Untertitel (max 60 Zeichen)
- description: Eine kurze Beschreibung der Serie (1-2 Saetze)

Antworte NUR mit einem JSON-Array:
[{{"title": "...", "subtitle": "...", "description": "..."}}, ...]"""

            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"Erstelle 3 Titelvorschlaege fuer eine Story-Serie in {country_name}.",
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.9,
                    max_output_tokens=1000,
                ),
            )

            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            suggestions = json.loads(text)
            if isinstance(suggestions, list) and len(suggestions) > 0:
                return {
                    "suggestions": suggestions[:3],
                    "source": "gemini",
                }
        except Exception as e:
            logger.warning(f"Gemini arc title suggestion failed: {e}")

    # Fallback: rule-based title suggestions
    fallback_titles = []
    if student_name:
        fallback_titles = [
            {
                "title": f"{student_name}s {country_name}-Abenteuer",
                "subtitle": f"Ein Auslandsjahr voller Ueberraschungen",
                "description": f"Begleite {student_name} auf der Reise durch ein unvergessliches Highschool-Jahr in {country_name}.",
            },
            {
                "title": f"Mein Jahr in {country_name}",
                "subtitle": f"{student_name} erzaehlt",
                "description": f"Aus erster Hand: {student_name} teilt die Hoehen und Tiefen eines Auslandsjahres in {country_name}.",
            },
            {
                "title": f"Dear Diary: {country_name}",
                "subtitle": f"Die Geschichte von {student_name}",
                "description": f"Wie ein Tagebuch: {student_name}s persoenlichste Momente, Gedanken und Erlebnisse in {country_name}.",
            },
        ]
    else:
        fallback_titles = [
            {
                "title": f"Highschool-Leben in {country_name}",
                "subtitle": "Eine Story-Serie von TREFF",
                "description": f"Erlebe den Alltag eines deutschen Austauschschuelers in {country_name} - von der Ankunft bis zum Abschied.",
            },
            {
                "title": f"Fernweh: {country_name}",
                "subtitle": "Highschool-Abenteuer hautnah",
                "description": f"Was erlebt man wirklich bei einem Highschool-Aufenthalt in {country_name}? Diese Serie zeigt es!",
            },
            {
                "title": f"Exchange Diaries: {country_name}",
                "subtitle": "Geschichten aus dem Auslandsjahr",
                "description": f"Authentische Geschichten und Erlebnisse aus {country_name} - direkt von unseren TREFF-Teilnehmern.",
            },
        ]

    return {
        "suggestions": fallback_titles,
        "source": "rule_based",
    }


# ═══════════════════════════════════════════════════════════════════════
# Episode Text Suggestions (Rueckblick, Cliffhanger, Teaser)
# ═══════════════════════════════════════════════════════════════════════

@router.post("/suggest-episode-text")
async def suggest_episode_text(
    request: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Generate AI suggestions for episode-specific text fields.

    Given a story arc and episode number, generates:
    - previously_text: "Bisher bei [Student]..." recap of previous episodes
    - cliffhanger_text: Cliffhanger ending for the current episode
    - next_episode_hint: Teaser for what comes next

    Expects:
    - arc_id (int): Story arc ID
    - episode_number (int): Current episode number
    - field (str): Which field to generate: 'previously_text', 'cliffhanger_text', or 'next_episode_hint'
    - topic (str, optional): Current episode topic/title
    - tone (str, optional): Tone for generation (default: jugendlich)

    Returns generated text suggestion.
    """
    ai_rate_limiter.check_rate_limit(user_id, "suggest-episode-text")

    arc_id = request.get("arc_id")
    episode_number = request.get("episode_number", 1)
    field = request.get("field", "previously_text")
    topic_text = request.get("topic", "")
    tone = request.get("tone", "jugendlich")

    if not arc_id:
        raise HTTPException(status_code=400, detail="arc_id is required")

    valid_fields = {"previously_text", "cliffhanger_text", "next_episode_hint"}
    if field not in valid_fields:
        raise HTTPException(status_code=400, detail=f"field must be one of: {', '.join(sorted(valid_fields))}")

    # Load the story arc
    result = await db.execute(
        select(StoryArc).where(StoryArc.id == arc_id, StoryArc.user_id == user_id)
    )
    arc = result.scalar_one_or_none()
    if not arc:
        raise HTTPException(status_code=404, detail="Story arc not found")

    # Load previous episodes for context
    result = await db.execute(
        select(StoryEpisode)
        .where(StoryEpisode.arc_id == arc_id)
        .order_by(StoryEpisode.episode_number)
    )
    episodes = result.scalars().all()

    # Load student name if linked
    student_name = "dem Studenten"
    if arc.student_id:
        result = await db.execute(
            select(Student).where(Student.id == arc.student_id)
        )
        student = result.scalar_one_or_none()
        if student:
            student_name = student.name

    # Build context from previous episodes
    prev_episode_summaries = []
    for ep in episodes:
        if ep.episode_number < episode_number:
            summary = f"Episode {ep.episode_number}: {ep.episode_title}"
            if ep.teaser_text:
                summary += f" - {ep.teaser_text}"
            prev_episode_summaries.append(summary)

    # Try AI generation first
    api_key = await _get_gemini_api_key(user_id, db)
    suggestion = None
    source = "rule_based"

    if api_key:
        try:
            suggestion = await _generate_episode_text_ai(
                field=field,
                arc_title=arc.title,
                student_name=student_name,
                episode_number=episode_number,
                planned_episodes=arc.planned_episodes,
                prev_episodes=prev_episode_summaries,
                topic=topic_text,
                tone=tone,
                country=arc.country,
                api_key=api_key,
            )
            if suggestion:
                source = "gemini"
        except Exception as e:
            logger.warning("AI episode text generation failed, using fallback: %s", e)

    # Fallback to rule-based
    if not suggestion:
        suggestion = _generate_episode_text_fallback(
            field=field,
            arc_title=arc.title,
            student_name=student_name,
            episode_number=episode_number,
            planned_episodes=arc.planned_episodes,
            prev_episodes=prev_episode_summaries,
            topic=topic_text,
            country=arc.country,
        )

    return {
        "field": field,
        "suggestion": suggestion,
        "source": source,
        "arc_title": arc.title,
        "student_name": student_name,
        "episode_number": episode_number,
    }


async def _generate_episode_text_ai(
    field: str,
    arc_title: str,
    student_name: str,
    episode_number: int,
    planned_episodes: int,
    prev_episodes: list,
    topic: str,
    tone: str,
    country: str | None,
    api_key: str,
) -> str | None:
    """Use Gemini to generate episode-specific text."""
    try:
        from google import genai

        client = genai.Client(api_key=api_key)

        country_name = {
            "usa": "USA", "canada": "Kanada", "australia": "Australien",
            "newzealand": "Neuseeland", "ireland": "Irland",
        }.get(country or "", "")

        prev_context = ""
        if prev_episodes:
            prev_context = "\n".join(prev_episodes)
        else:
            prev_context = "(Dies ist die erste Episode - kein Rueckblick noetig)"

        field_instructions = {
            "previously_text": f"""Schreibe einen kurzen 'Bisher bei {student_name}...' Rueckblick (2-3 Saetze).
Fasse zusammen, was in den bisherigen Episoden passiert ist.
Beginne mit 'Bisher bei {student_name}...' oder 'In den letzten Episoden...'
Der Text soll Zuschauer abholen, die nicht alle Episoden gesehen haben.""",

            "cliffhanger_text": f"""Schreibe einen Cliffhanger-Text (1-2 Saetze) fuer das Ende von Episode {episode_number}.
Der Text soll Spannung erzeugen und zum Weiterschauen motivieren.
Verwende Fragen oder ueberraschende Wendungen.
Beispiel: 'Aber was {student_name} am naechsten Tag erlebt, haette niemand erwartet...'""",

            "next_episode_hint": f"""Schreibe einen kurzen Teaser (1-2 Saetze) fuer die naechste Episode.
Der Text soll neugierig machen, ohne zu viel zu verraten.
Beispiel: 'In der naechsten Episode: {student_name} entdeckt...'
Verwende Formulierungen wie 'Naechste Episode:', 'Kommt als naechstes:', 'Stay tuned:'""",
        }

        prompt = f"""Du bist ein Social-Media-Texter fuer TREFF Sprachreisen.
Schreibe fuer die Story-Serie '{arc_title}' mit {student_name}.
{f'Land: {country_name}' if country_name else ''}
Tonalitaet: {tone}
Episode: {episode_number} von {planned_episodes}
{f'Aktuelles Thema: {topic}' if topic else ''}

Bisherige Episoden:
{prev_context}

{field_instructions[field]}

Antworte NUR mit dem gewuenschten Text, ohne Anweisungen oder Erklaerungen."""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        text = response.text.strip()
        # Remove surrounding quotes if present
        if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
            text = text[1:-1]
        return text if text else None

    except Exception as e:
        logger.warning("Gemini episode text generation error: %s", e)
        return None


def _generate_episode_text_fallback(
    field: str,
    arc_title: str,
    student_name: str,
    episode_number: int,
    planned_episodes: int,
    prev_episodes: list,
    topic: str,
    country: str | None,
) -> str:
    """Rule-based fallback for episode text generation."""
    country_name = {
        "usa": "den USA", "canada": "Kanada", "australia": "Australien",
        "newzealand": "Neuseeland", "ireland": "Irland",
    }.get(country or "", "dem Ausland")

    if field == "previously_text":
        if episode_number <= 1:
            return f"Willkommen zur ersten Episode von '{arc_title}'! Begleite {student_name} auf dem Abenteuer in {country_name}."
        if len(prev_episodes) > 0:
            last_ep = prev_episodes[-1]
            return f"Bisher bei {student_name}: {last_ep.split(': ', 1)[-1] if ': ' in last_ep else last_ep}. Jetzt geht die Reise weiter!"
        return f"Bisher bei {student_name}: Die Reise in {country_name} hat begonnen und es gab schon einige unvergessliche Momente. Weiter geht's!"

    elif field == "cliffhanger_text":
        cliffhangers = [
            f"Aber was {student_name} am naechsten Tag erlebt, haette niemand erwartet...",
            f"Wird {student_name} diese Herausforderung meistern? Die Antwort kommt in der naechsten Episode!",
            f"Das war erst der Anfang - denn was dann passiert, veraendert alles...",
            f"Ob das gut geht? Findet es in der naechsten Episode heraus!",
        ]
        import random
        return random.choice(cliffhangers)

    elif field == "next_episode_hint":
        hints = [
            f"Naechste Episode: {student_name} entdeckt eine voellig neue Seite von {country_name}!",
            f"Stay tuned: In Episode {episode_number + 1} wird es richtig spannend!",
            f"Kommt als naechstes: Neue Abenteuer, neue Freundschaften und eine grosse Ueberraschung!",
            f"Naechstes Mal bei '{arc_title}': {student_name} erlebt etwas Unvergessliches.",
        ]
        import random
        return random.choice(hints)

    return ""


# ═══════════════════════════════════════════════════════════════════════
# Cliffhanger & Teaser System
# ═══════════════════════════════════════════════════════════════════════

TEASER_VARIANTS = {
    "countdown": {
        "label": "Countdown",
        "description": "Noch X Tage bis...",
        "icon": "⏳",
    },
    "question": {
        "label": "Frage",
        "description": "Was passiert wenn...?",
        "icon": "❓",
    },
    "spoiler": {
        "label": "Spoiler",
        "description": "Naechstes Mal: Der erste Schnee",
        "icon": "👀",
    },
}


@router.post("/generate-cliffhanger")
async def generate_cliffhanger(
    request: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Generate cliffhanger text and teaser variants for a story arc episode.

    Expects:
    - arc_id (int): Story arc ID (required)
    - episode_number (int): Current episode number (default: 1)
    - episode_content (str, optional): Summary/content of the current episode
    - teaser_variant (str, optional): 'countdown', 'question', or 'spoiler' (default: auto-select)
    - days_until_next (int, optional): Days until next episode (for countdown variant)

    Returns:
    - cliffhanger_text: The generated cliffhanger ending text
    - teaser_text: The teaser for the next episode
    - teaser_variant: Which variant was used
    - next_episode_info: Info about the planned next episode (if exists)
    - all_variants: All three teaser variants generated
    """
    ai_rate_limiter.check_rate_limit(user_id, "generate-cliffhanger")

    arc_id = request.get("arc_id")
    episode_number = request.get("episode_number", 1)
    episode_content = request.get("episode_content", "")
    teaser_variant = request.get("teaser_variant", "")
    days_until_next = request.get("days_until_next", 1)

    if not arc_id:
        raise HTTPException(status_code=400, detail="arc_id is required")

    # Load story arc
    result = await db.execute(
        select(StoryArc).where(StoryArc.id == arc_id, StoryArc.user_id == user_id)
    )
    arc = result.scalar_one_or_none()
    if not arc:
        raise HTTPException(status_code=404, detail="Story arc not found")

    # Load all episodes
    result = await db.execute(
        select(StoryEpisode)
        .where(StoryEpisode.arc_id == arc_id)
        .order_by(StoryEpisode.episode_number)
    )
    episodes = result.scalars().all()

    # Get student name
    student_name = "dem Studenten"
    if arc.student_id:
        result = await db.execute(
            select(Student).where(Student.id == arc.student_id)
        )
        student = result.scalar_one_or_none()
        if student:
            student_name = student.name

    # Find current and next episode
    current_episode = None
    next_episode = None
    for ep in episodes:
        if ep.episode_number == episode_number:
            current_episode = ep
        elif ep.episode_number == episode_number + 1:
            next_episode = ep

    # Build context from all episodes
    episode_context = []
    for ep in episodes:
        if ep.episode_number <= episode_number:
            summary = f"Episode {ep.episode_number}: {ep.episode_title}"
            if ep.teaser_text:
                summary += f" - {ep.teaser_text}"
            episode_context.append(summary)

    # Next episode info for linking
    next_episode_info = None
    if next_episode:
        # Find the linked post for the next episode
        next_post_info = None
        if next_episode.post_id:
            result = await db.execute(
                select(Post).where(Post.id == next_episode.post_id)
            )
            next_post = result.scalar_one_or_none()
            if next_post:
                next_post_info = {
                    "id": next_post.id,
                    "title": next_post.topic or next_post.caption_instagram or "",
                    "scheduled_date": next_post.scheduled_date.isoformat() if next_post.scheduled_date else None,
                }
        next_episode_info = {
            "episode_number": next_episode.episode_number,
            "episode_title": next_episode.episode_title,
            "teaser_text": next_episode.teaser_text,
            "status": next_episode.status,
            "post": next_post_info,
        }

    # Try AI generation
    api_key = await _get_gemini_api_key(user_id, db)
    cliffhanger_text = None
    all_variants = {}
    source = "rule_based"

    if api_key:
        try:
            cliffhanger_result = await _generate_cliffhanger_ai(
                arc_title=arc.title,
                student_name=student_name,
                episode_number=episode_number,
                planned_episodes=arc.planned_episodes,
                episode_content=episode_content,
                episode_context=episode_context,
                next_episode=next_episode,
                days_until_next=days_until_next,
                tone=arc.tone or "jugendlich",
                country=arc.country,
                api_key=api_key,
            )
            if cliffhanger_result:
                cliffhanger_text = cliffhanger_result.get("cliffhanger")
                all_variants = cliffhanger_result.get("variants", {})
                source = "gemini"
        except Exception as e:
            logger.warning("AI cliffhanger generation failed, using fallback: %s", e)

    # Fallback to rule-based
    if not cliffhanger_text:
        fallback = _generate_cliffhanger_fallback(
            arc_title=arc.title,
            student_name=student_name,
            episode_number=episode_number,
            planned_episodes=arc.planned_episodes,
            episode_content=episode_content,
            next_episode=next_episode,
            days_until_next=days_until_next,
            country=arc.country,
        )
        cliffhanger_text = fallback["cliffhanger"]
        all_variants = fallback["variants"]

    # Select the requested variant (or best one)
    selected_variant = teaser_variant if teaser_variant in all_variants else "question"
    teaser_text = all_variants.get(selected_variant, "")

    return {
        "cliffhanger_text": cliffhanger_text,
        "teaser_text": teaser_text,
        "teaser_variant": selected_variant,
        "all_variants": all_variants,
        "next_episode_info": next_episode_info,
        "source": source,
        "arc_title": arc.title,
        "student_name": student_name,
        "episode_number": episode_number,
        "is_last_episode": episode_number >= arc.planned_episodes,
    }


@router.get("/teaser-variants")
async def get_teaser_variants(
    user_id: int = Depends(get_current_user_id),
):
    """Get available teaser variant types."""
    return {"variants": TEASER_VARIANTS}


async def _generate_cliffhanger_ai(
    arc_title: str,
    student_name: str,
    episode_number: int,
    planned_episodes: int,
    episode_content: str,
    episode_context: list,
    next_episode,
    days_until_next: int,
    tone: str,
    country: str | None,
    api_key: str,
) -> dict | None:
    """Use Gemini to generate cliffhanger and teaser variants."""
    try:
        from google import genai

        client = genai.Client(api_key=api_key)

        country_name = {
            "usa": "USA", "canada": "Kanada", "australia": "Australien",
            "newzealand": "Neuseeland", "ireland": "Irland",
        }.get(country or "", "")

        context_text = "\n".join(episode_context) if episode_context else "(Erste Episode)"

        next_ep_info = ""
        if next_episode:
            next_ep_info = f"\nNaechste Episode: '{next_episode.episode_title}'"
            if next_episode.teaser_text:
                next_ep_info += f" - {next_episode.teaser_text}"

        prompt = f"""Du bist ein Social-Media-Texter fuer TREFF Sprachreisen.
Erstelle einen packenden Cliffhanger und drei Teaser-Varianten fuer Episode {episode_number} der Story-Serie '{arc_title}' mit {student_name}.
{f'Land: {country_name}' if country_name else ''}
Tonalitaet: {tone}
Episode {episode_number} von {planned_episodes}

Bisherige Episoden:
{context_text}
{f'Inhalt der aktuellen Episode: {episode_content}' if episode_content else ''}
{next_ep_info}

Erstelle:

1. CLIFFHANGER: Ein packender Cliffhanger-Text (1-2 Saetze) fuer das Ende der Episode.
   - Erzeugt Spannung und Neugier
   - Motiviert zum Weiterschauen
   - Passt zur Tonalitaet ({tone})

2. COUNTDOWN-TEASER: Ein Countdown-Teaser (1 Satz).
   - Format: "Noch {days_until_next} Tag(e)..." + spannende Andeutung

3. FRAGE-TEASER: Ein Frage-Teaser (1 Satz).
   - Format: Eine offene, spannende Frage

4. SPOILER-TEASER: Ein leichter Spoiler-Teaser (1 Satz).
   - Format: "Naechstes Mal:" + Andeutung

Antworte im JSON-Format:
{{"cliffhanger": "...", "countdown": "...", "question": "...", "spoiler": "..."}}

NUR das JSON, keine Erklaerungen."""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        text = response.text.strip()

        # Parse JSON from response
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        result = json.loads(text)

        return {
            "cliffhanger": result.get("cliffhanger", ""),
            "variants": {
                "countdown": result.get("countdown", ""),
                "question": result.get("question", ""),
                "spoiler": result.get("spoiler", ""),
            },
        }

    except Exception as e:
        logger.warning("Gemini cliffhanger generation error: %s", e)
        return None


def _generate_cliffhanger_fallback(
    arc_title: str,
    student_name: str,
    episode_number: int,
    planned_episodes: int,
    episode_content: str,
    next_episode,
    days_until_next: int,
    country: str | None,
) -> dict:
    """Rule-based fallback for cliffhanger and teaser generation."""
    import random

    country_name = {
        "usa": "den USA", "canada": "Kanada", "australia": "Australien",
        "newzealand": "Neuseeland", "ireland": "Irland",
    }.get(country or "", "dem Ausland")

    cliffhangers = [
        f"Aber was {student_name} am naechsten Tag erlebt, haette niemand erwartet...",
        f"Wird {student_name} diese Herausforderung in {country_name} meistern?",
        f"Das war erst der Anfang — denn was dann passiert, veraendert alles...",
        f"Ob das gut geht? {student_name} steht vor der groessten Entscheidung des Auslandsjahres!",
        f"Doch dann passiert etwas, das niemand kommen sah...",
        f"Was {student_name} als naechstes entdeckt, wird alles auf den Kopf stellen!",
    ]

    next_title = ""
    if next_episode and next_episode.episode_title:
        next_title = next_episode.episode_title

    days_text = f"{days_until_next} Tag" if days_until_next == 1 else f"{days_until_next} Tage"
    countdown_teasers = [
        f"Noch {days_text} bis {student_name} zum ersten Mal richtig ankommt in {country_name}!",
        f"Noch {days_text}... und dann wird alles anders fuer {student_name}!",
        f"In {days_text} geht es weiter mit {student_name} in {country_name}!",
    ]

    question_teasers = [
        f"Was passiert, wenn {student_name} sich zum ersten Mal ganz allein zurechtfinden muss?",
        f"Wird {student_name} die neue Herausforderung meistern oder scheitern?",
        f"Kann {student_name} in {country_name} ueber sich hinauswachsen?",
    ]

    spoiler_teasers = [
        f"Naechstes Mal: {student_name} entdeckt eine voellig neue Seite von {country_name}!",
        f"Naechstes Mal: Neue Freundschaften, neue Abenteuer und eine grosse Ueberraschung!",
    ]
    if next_title:
        spoiler_teasers.insert(0, f"Naechstes Mal: {next_title}")

    return {
        "cliffhanger": random.choice(cliffhangers),
        "variants": {
            "countdown": random.choice(countdown_teasers),
            "question": random.choice(question_teasers),
            "spoiler": random.choice(spoiler_teasers),
        },
    }


@router.post("/auto-cliffhanger-slide")
async def auto_generate_cliffhanger_slide(
    request: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Auto-generate a cliffhanger slide for a post that is part of a story arc.

    Expects:
    - post_id (int): The post ID to attach the cliffhanger slide to
    - teaser_variant (str, optional): 'countdown', 'question', or 'spoiler'
    - days_until_next (int, optional): Days until next episode

    Returns the generated cliffhanger data and slide info.
    """
    from app.models.post_slide import PostSlide

    post_id = request.get("post_id")
    teaser_variant = request.get("teaser_variant", "question")
    days_until_next = request.get("days_until_next", 1)

    if not post_id:
        raise HTTPException(status_code=400, detail="post_id is required")

    # Load post
    result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if not post.story_arc_id:
        raise HTTPException(status_code=400, detail="Post is not part of a story arc")

    # Generate cliffhanger
    cliffhanger_request = {
        "arc_id": post.story_arc_id,
        "episode_number": post.episode_number or 1,
        "episode_content": post.topic or post.caption_instagram or "",
        "teaser_variant": teaser_variant,
        "days_until_next": days_until_next,
    }

    cliffhanger_result = await generate_cliffhanger(cliffhanger_request, user_id, db)

    # Find last slide index
    result = await db.execute(
        select(PostSlide)
        .where(PostSlide.post_id == post_id)
        .order_by(PostSlide.slide_index.desc())
    )
    last_slide = result.scalar_one_or_none()
    next_index = (last_slide.slide_index + 1) if last_slide else 0

    # Check if a cliffhanger slide already exists
    result = await db.execute(
        select(PostSlide).where(PostSlide.post_id == post_id)
    )
    existing_slides = result.scalars().all()
    cliffhanger_slide = None
    for s in existing_slides:
        if s.custom_css_overrides:
            try:
                overrides = json.loads(s.custom_css_overrides) if isinstance(s.custom_css_overrides, str) else s.custom_css_overrides
                if overrides.get("_cliffhanger_slide"):
                    cliffhanger_slide = s
                    break
            except (json.JSONDecodeError, TypeError):
                pass

    # Build slide data
    selected_teaser = cliffhanger_result["all_variants"].get(
        cliffhanger_result["teaser_variant"], ""
    )
    slide_data = {
        "headline": "Fortsetzung folgt...",
        "body_text": cliffhanger_result["cliffhanger_text"],
        "subheadline": selected_teaser,
        "cta_text": f"Episode {(post.episode_number or 1) + 1} kommt bald!",
        "background_type": "color",
        "background_value": "#1A1A2E",
        "custom_css_overrides": json.dumps({
            "_cliffhanger_slide": True,
            "teaser_variant": cliffhanger_result["teaser_variant"],
            "all_variants": cliffhanger_result["all_variants"],
        }),
    }

    if cliffhanger_slide:
        for key, value in slide_data.items():
            setattr(cliffhanger_slide, key, value)
        await db.flush()
        await db.refresh(cliffhanger_slide)
        slide_dict = {
            "id": cliffhanger_slide.id,
            "post_id": cliffhanger_slide.post_id,
            "slide_index": cliffhanger_slide.slide_index,
            **slide_data,
        }
    else:
        new_slide = PostSlide(post_id=post_id, slide_index=next_index, **slide_data)
        db.add(new_slide)
        await db.flush()
        await db.refresh(new_slide)
        slide_dict = {
            "id": new_slide.id,
            "post_id": new_slide.post_id,
            "slide_index": new_slide.slide_index,
            **slide_data,
        }

    await db.commit()

    return {
        "cliffhanger": cliffhanger_result,
        "slide": slide_dict,
        "message": "Cliffhanger-Slide erstellt" if not cliffhanger_slide else "Cliffhanger-Slide aktualisiert",
    }


# ═══════════════════════════════════════════════════════════════════════
# Recurring Format AI Text Generation (Feature #191)
# ═══════════════════════════════════════════════════════════════════════

RECURRING_FORMAT_PROMPTS = {
    "TREFF Freitags-Fail": {
        "system": "Du bist Social-Media-Texter fuer TREFF Sprachreisen. Erstelle einen lustigen 'Freitags-Fail' Post ueber einen typischen Kulturschock-Moment eines deutschen Austauschschuelers im Ausland. Der Ton ist witzig, selbstironisch und relatable. Keine ernsthaften Probleme - nur lustige Missverstaendnisse und Alltagssituationen.",
        "example_topics": [
            "Trinkgeld-Kultur in den USA nicht verstanden",
            "Versucht, deutsches Brot zu finden",
            "Small Talk im Aufzug - totale Panik",
            "Linksverkehr in Australien/Neuseeland/Irland",
            "Falsche Handgeste in einem anderen Land",
        ],
    },
    "Motivation Monday": {
        "system": "Du bist Social-Media-Texter fuer TREFF Sprachreisen. Erstelle einen inspirierenden 'Motivation Monday' Post. Nutze einen epischen Moment, ein motivierendes Zitat oder eine Erfolgsgeschichte eines Austauschschuelers. Der Ton ist motivierend, positiv und ermutigend. Ziel: Schueler sollen sich auf ihr Auslandsjahr freuen.",
        "example_topics": [
            "Erste Freundschaft im Ausland geschlossen",
            "Rede vor der ganzen Schule gehalten",
            "Sportwettbewerb im Ausland gewonnen",
            "Beste Noten trotz Sprachbarriere",
            "Mutiger erster Tag an der neuen Schule",
        ],
    },
    "Throwback Thursday": {
        "system": "Du bist Social-Media-Texter fuer TREFF Sprachreisen. Erstelle einen nostalgischen 'Throwback Thursday' Post. Blicke zurueck auf unvergessliche Momente von Alumni-Austauschschuelern. Der Ton ist emotional, warm und erinnerungswuerdig. Zeige wie das Auslandsjahr das Leben veraendert hat.",
        "example_topics": [
            "Abschied von der Gastfamilie",
            "Erstes Weihnachten im Ausland",
            "Schulabschluss an einer amerikanischen High School",
            "Roadtrip mit neuen Freunden",
            "Wiedersehen nach Jahren mit Gastgeschwistern",
        ],
    },
    "Wusstest-du-Mittwoch": {
        "system": "Du bist Social-Media-Texter fuer TREFF Sprachreisen. Erstelle einen informativen 'Wusstest du?' Post mit einem ueberraschenden Fun Fact ueber ein Zielland (USA, Kanada, Australien, Neuseeland oder Irland). Der Ton ist informativ aber unterhaltsam. Der Fakt soll ueberraschen und zum Teilen animieren.",
        "example_topics": [
            "Neuseeland hat mehr Schafe als Menschen",
            "Kanadier entschuldigen sich per Gesetz",
            "In den USA gibt es einen Nationalen Erdnussbutter-Tag",
            "Australiens Outback ist groesser als ganz Westeuropa",
            "Irland hat keine Schlangen - dank St. Patrick",
        ],
    },
    "Sonntags-Sehnsucht": {
        "system": "Du bist Social-Media-Texter fuer TREFF Sprachreisen. Erstelle einen stimmungsvollen 'Sonntags-Sehnsucht' Post, der Fernweh weckt. Beschreibe eine schoene Szene, einen Sonnenuntergang oder einen emotionalen Moment aus dem Auslandsjahr. Der Ton ist poetisch, sehnsuchtsvoll und vertraeumt. Wecke den Wunsch, die Welt zu entdecken.",
        "example_topics": [
            "Sonnenuntergang am Grand Canyon",
            "Herbstfarben in Kanada - Indian Summer",
            "Surfen bei Sonnenaufgang in Australien",
            "Sternenhimmel ueber Neuseelands Bergen",
            "Klippen von Irland im Morgennebel",
        ],
    },
}


@router.post("/generate-recurring-format-text")
async def generate_recurring_format_text(
    request: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Generate AI text content for a specific recurring format.

    Expects:
    - format_id (int): The recurring format ID
    - topic (str, optional): Specific topic to write about
    - country (str, optional): Country focus (usa, kanada, australien, neuseeland, irland)

    Returns:
    - title (str): Post title
    - caption (str): Instagram/TikTok caption text
    - hashtags (list): Recommended hashtags
    - topic_used (str): The topic that was used
    - format_name (str): Name of the recurring format
    """
    import random

    ai_rate_limiter.check_rate_limit(user_id, "generate-recurring-format-text")

    format_id = request.get("format_id")
    topic = request.get("topic")
    country = request.get("country")

    if not format_id:
        raise HTTPException(status_code=400, detail="format_id is required")

    # Load the recurring format
    from sqlalchemy import or_
    result = await db.execute(
        select(RecurringFormat).where(
            RecurringFormat.id == format_id,
            or_(
                RecurringFormat.user_id == None,
                RecurringFormat.user_id == user_id,
            ),
        )
    )
    fmt = result.scalar_one_or_none()
    if not fmt:
        raise HTTPException(status_code=404, detail="Recurring format not found")

    # Parse hashtags
    hashtags = []
    if fmt.hashtags:
        try:
            hashtags = json.loads(fmt.hashtags)
        except (json.JSONDecodeError, TypeError):
            hashtags = []

    # Get prompt config for this format
    prompt_config = RECURRING_FORMAT_PROMPTS.get(fmt.name, {})
    system_prompt = prompt_config.get("system", f"Du bist Social-Media-Texter fuer TREFF Sprachreisen. Erstelle einen Post im Stil von '{fmt.name}'. {fmt.description}")
    example_topics = prompt_config.get("example_topics", [])

    # Choose topic
    if not topic and example_topics:
        topic = random.choice(example_topics)
    elif not topic:
        topic = f"Allgemeiner {fmt.name} Post"

    # Add country context
    country_names = {
        "usa": "USA", "kanada": "Kanada", "australien": "Australien",
        "neuseeland": "Neuseeland", "irland": "Irland"
    }
    country_label = country_names.get(country, "")
    if country_label:
        topic = f"{topic} ({country_label})"

    # Try Gemini API for AI generation
    api_key = await _get_gemini_api_key(user_id, db)

    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash-preview-05-20")

            user_prompt = f"""Erstelle einen Social Media Post zum Thema: {topic}

Format: {fmt.name}
Tonalitaet: {fmt.tone or 'jugendlich'}
{f'Land-Fokus: {country_label}' if country_label else ''}

Antworte im folgenden JSON-Format:
{{
  "title": "Kurzer, knackiger Titel (max 60 Zeichen)",
  "caption": "Instagram/TikTok Caption (150-300 Zeichen). Benutze passende Emojis. Schreibe auf Deutsch.",
  "hashtags": ["#Hashtag1", "#Hashtag2", "#Hashtag3", "#Hashtag4", "#Hashtag5"]
}}

Wichtig: Antworte NUR mit dem JSON, kein anderer Text."""

            response = model.generate_content(
                [{"role": "user", "parts": [{"text": system_prompt + "\n\n" + user_prompt}]}],
            )

            response_text = response.text.strip()
            # Try to parse JSON from response
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            result_data = json.loads(response_text)

            # Merge AI hashtags with format default hashtags
            ai_hashtags = result_data.get("hashtags", [])
            merged_hashtags = list(dict.fromkeys(ai_hashtags + hashtags))[:10]

            return {
                "title": result_data.get("title", f"{fmt.icon} {fmt.name}"),
                "caption": result_data.get("caption", ""),
                "hashtags": merged_hashtags,
                "topic_used": topic,
                "format_name": fmt.name,
                "format_icon": fmt.icon,
                "source": "gemini",
            }
        except Exception as e:
            logger.warning(f"Gemini generation failed for recurring format, falling back to rule-based: {e}")

    # Rule-based fallback
    fallback_captions = {
        "TREFF Freitags-Fail": [
            f"{fmt.icon} TREFF Freitags-Fail! {topic} - Kennst du das? Jeder Austauschschueler hat diesen Moment erlebt! Erzaehl uns deinen groessten Kulturschock in den Kommentaren!",
            f"{fmt.icon} Freitags-Fail der Woche: {topic}! Wir lachen MIT euch, nicht UEBER euch. Welcher Kulturschock hat euch am meisten ueberrascht?",
        ],
        "Motivation Monday": [
            f"{fmt.icon} Motivation Monday! {topic} - So starten wir die Woche! Dein Auslandsjahr wartet auf dich. Was ist DEIN Traum?",
            f"{fmt.icon} Happy Monday! {topic} - Jeder grosse Erfolg beginnt mit dem Mut, loszugehen. TREFF begleitet dich dabei!",
        ],
        "Throwback Thursday": [
            f"{fmt.icon} Throwback Thursday! {topic} - Manche Erinnerungen bleiben fuer immer. Teile deinen unvergesslichsten Moment mit uns!",
            f"{fmt.icon} #TBT: {topic} - Jahre spaeter und diese Erinnerung bringt uns immer noch zum Laecheln. Was vermisst IHR am meisten?",
        ],
        "Wusstest-du-Mittwoch": [
            f"{fmt.icon} Wusstest du? {topic} - Mind blown! Welchen Fun Fact ueber dein Traumland kennst DU?",
            f"{fmt.icon} Mittwochs-Wissen: {topic} - Haettest du das gewusst? Speichern und mit Freunden teilen!",
        ],
        "Sonntags-Sehnsucht": [
            f"{fmt.icon} Sonntags-Sehnsucht... {topic} - Manchmal muss man die Augen schliessen und sich an diesen Moment erinnern. Wohin zieht es DICH?",
            f"{fmt.icon} Sunday Vibes: {topic} - Diese Momente machen ein Auslandsjahr unvergesslich. Traeumst du auch davon?",
        ],
    }

    captions = fallback_captions.get(fmt.name, [
        f"{fmt.icon} {fmt.name}: {topic} - Folge TREFF Sprachreisen fuer mehr!",
    ])
    caption = random.choice(captions)

    return {
        "title": f"{fmt.icon} {fmt.name}",
        "caption": caption,
        "hashtags": hashtags,
        "topic_used": topic,
        "format_name": fmt.name,
        "format_icon": fmt.icon,
        "source": "rule_based",
    }
