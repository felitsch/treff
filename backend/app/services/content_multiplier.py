"""
Content Multiplier Service - Generate derivative content formats from a source post.

Takes one post and creates adapted versions for different platforms/formats:
- Instagram Feed → Instagram Story version
- Instagram Feed → TikTok adaptation
- Any post → Carousel version
- Story → Feed version

Each derivative adapts:
- Caption length and style for the target platform
- Hashtag strategy per platform
- CTA adaptation
- Format-specific optimizations
"""

import asyncio
import json
import logging
import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.post import Post

logger = logging.getLogger(__name__)

# Platform-specific adaptation rules
PLATFORM_RULES = {
    "instagram_feed": {
        "max_caption_length": 2200,
        "optimal_caption_length": 300,
        "hashtag_count": (15, 25),
        "supports_links": False,
        "caption_style": "Ausfuehrlicher, storytelling-orientiert, mit Absaetzen und Emojis",
        "category_default": "schueler_spotlight",
    },
    "instagram_story": {
        "max_caption_length": 200,
        "optimal_caption_length": 80,
        "hashtag_count": (3, 5),
        "supports_links": True,
        "caption_style": "Kurz, direkt, mit Sticker-Aufforderung (Umfrage, Frage, Slider)",
        "category_default": "behind_the_scenes",
    },
    "tiktok": {
        "max_caption_length": 300,
        "optimal_caption_length": 150,
        "hashtag_count": (4, 8),
        "supports_links": False,
        "caption_style": "Knackig, trend-bewusst, mit Hook am Anfang, Gen-Z-kompatibel aber serioees",
        "category_default": "fun_facts",
    },
    "carousel": {
        "max_caption_length": 2200,
        "optimal_caption_length": 400,
        "hashtag_count": (15, 25),
        "supports_links": False,
        "caption_style": "Slide-by-slide Erklaerung, nummeriert, educational",
        "category_default": "laender_spotlight",
    },
}


async def multiply_content(
    source_post: Post,
    target_formats: list[str],
    user_id: int,
    db: AsyncSession,
) -> list[dict]:
    """Generate derivative posts from a source post.

    Args:
        source_post: The original Post object to multiply
        target_formats: List of target platform/format strings
        user_id: The user who owns the posts
        db: Database session

    Returns:
        List of dicts with new post info: {post_id, platform, title, status}
    """
    derivatives = []
    group_id = source_post.linked_post_group_id or str(uuid.uuid4())

    for target_format in target_formats:
        # Skip if same as source
        if target_format == source_post.platform:
            continue

        if target_format not in PLATFORM_RULES:
            logger.warning(f"Unknown target format: {target_format}, skipping")
            continue

        try:
            derivative = await _create_derivative(
                source_post=source_post,
                target_format=target_format,
                user_id=user_id,
                group_id=group_id,
                db=db,
            )
            derivatives.append(derivative)
        except Exception as e:
            logger.error(f"Failed to create {target_format} derivative: {e}")

    # Update source post group ID if it was new
    if source_post.linked_post_group_id != group_id:
        source_post.linked_post_group_id = group_id
        db.add(source_post)

    return derivatives


async def _create_derivative(
    source_post: Post,
    target_format: str,
    user_id: int,
    group_id: str,
    db: AsyncSession,
) -> dict:
    """Create a single derivative post adapted for the target format."""
    rules = PLATFORM_RULES[target_format]

    # Try AI-powered adaptation first
    if settings.GEMINI_API_KEY:
        try:
            adapted = await _adapt_with_ai(source_post, target_format, rules)
        except Exception as e:
            logger.warning(f"AI adaptation failed for {target_format}: {e}")
            adapted = _adapt_rule_based(source_post, target_format, rules)
    else:
        adapted = _adapt_rule_based(source_post, target_format, rules)

    # Determine the right platform string
    platform = target_format if target_format != "carousel" else "instagram_feed"

    # Create the derivative post
    new_post = Post(
        user_id=user_id,
        template_id=source_post.template_id,
        category=adapted.get("category", source_post.category),
        country=source_post.country,
        platform=platform,
        status="draft",
        title=adapted.get("title", f"{source_post.title or 'Post'} ({target_format})"),
        slide_data=source_post.slide_data,
        caption_instagram=adapted.get("caption_instagram"),
        caption_tiktok=adapted.get("caption_tiktok"),
        hashtags_instagram=adapted.get("hashtags_instagram", source_post.hashtags_instagram),
        hashtags_tiktok=adapted.get("hashtags_tiktok", source_post.hashtags_tiktok),
        cta_text=adapted.get("cta_text", source_post.cta_text),
        custom_colors=source_post.custom_colors,
        custom_fonts=source_post.custom_fonts,
        tone=source_post.tone,
        student_id=source_post.student_id,
        story_arc_id=source_post.story_arc_id,
        episode_number=source_post.episode_number,
        linked_post_group_id=group_id,
    )

    db.add(new_post)
    await db.flush()  # Get the ID

    return {
        "post_id": new_post.id,
        "platform": target_format,
        "title": new_post.title,
        "status": "draft",
    }


async def _adapt_with_ai(
    source_post: Post,
    target_format: str,
    rules: dict,
) -> dict:
    """Use Gemini to adapt content for the target platform (runs sync call in thread pool)."""
    loop = asyncio.get_event_loop()
    return await asyncio.wait_for(
        loop.run_in_executor(
            None,
            _adapt_with_ai_sync,
            source_post,
            target_format,
            rules,
        ),
        timeout=30.0,
    )


def _adapt_with_ai_sync(
    source_post: Post,
    target_format: str,
    rules: dict,
) -> dict:
    """Synchronous Gemini call for content adaptation (runs in thread pool)."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    source_caption = source_post.caption_instagram or source_post.caption_tiktok or ""
    source_hashtags = source_post.hashtags_instagram or source_post.hashtags_tiktok or ""

    prompt = f"""Du bist ein Social-Media-Experte fuer TREFF Sprachreisen (Highschool-Aufenthalte im Ausland).

Adaptiere diesen Social-Media-Post fuer das Format: {target_format}

ORIGINAL-POST:
- Plattform: {source_post.platform}
- Titel: {source_post.title or 'Kein Titel'}
- Kategorie: {source_post.category}
- Land: {source_post.country or 'Nicht angegeben'}
- Caption: {source_caption[:500]}
- Hashtags: {source_hashtags[:200]}
- CTA: {source_post.cta_text or 'Kein CTA'}
- Ton: {source_post.tone}

ZIELFORMAT-REGELN:
- Max Caption: {rules['max_caption_length']} Zeichen
- Optimale Laenge: {rules['optimal_caption_length']} Zeichen
- Hashtag-Anzahl: {rules['hashtag_count'][0]}-{rules['hashtag_count'][1]}
- Stil: {rules['caption_style']}

Antworte NUR mit einem JSON-Objekt (kein Markdown):
{{
  "title": "Adaptierter Titel fuer {target_format}",
  "caption_instagram": "Adaptierte Instagram Caption (oder null fuer TikTok-only)",
  "caption_tiktok": "Adaptierte TikTok Caption (oder null fuer Instagram-only)",
  "hashtags_instagram": "Adaptierte Instagram Hashtags als String",
  "hashtags_tiktok": "Adaptierte TikTok Hashtags als String",
  "cta_text": "Angepasster CTA (max 25 Zeichen)",
  "category": "{source_post.category}"
}}"""

    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-05-20",
        contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
    )

    text = response.text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    return json.loads(text)


def _adapt_rule_based(
    source_post: Post,
    target_format: str,
    rules: dict,
) -> dict:
    """Rule-based fallback for content adaptation."""
    source_caption = source_post.caption_instagram or source_post.caption_tiktok or ""
    max_len = rules["optimal_caption_length"]

    # Truncate caption for shorter formats
    if len(source_caption) > max_len:
        adapted_caption = source_caption[:max_len - 3].rsplit(" ", 1)[0] + "..."
    else:
        adapted_caption = source_caption

    # Adapt hashtags count
    source_tags = source_post.hashtags_instagram or source_post.hashtags_tiktok or ""
    tag_list = [t.strip() for t in source_tags.split("#") if t.strip()]
    min_tags, max_tags = rules["hashtag_count"]
    adapted_tags = tag_list[:max_tags]
    adapted_tags_str = " ".join(f"#{t}" for t in adapted_tags) if adapted_tags else source_tags

    # Create adapted title
    format_label = {
        "instagram_feed": "Feed",
        "instagram_story": "Story",
        "tiktok": "TikTok",
        "carousel": "Carousel",
    }.get(target_format, target_format)

    title = f"{source_post.title or 'Post'} - {format_label}-Version"

    result = {
        "title": title,
        "category": source_post.category,
        "cta_text": source_post.cta_text,
        "hashtags_instagram": adapted_tags_str if target_format != "tiktok" else None,
        "hashtags_tiktok": adapted_tags_str if target_format in ("tiktok",) else None,
    }

    # Set the right caption field
    if target_format == "tiktok":
        result["caption_tiktok"] = adapted_caption
        result["caption_instagram"] = None
    else:
        result["caption_instagram"] = adapted_caption
        result["caption_tiktok"] = None

    return result
