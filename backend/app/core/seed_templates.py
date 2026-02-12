"""Seed default templates for all 9 post categories."""

import json
import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.template import Template

logger = logging.getLogger(__name__)

# TREFF Brand colors
TREFF_BLUE = "#3B7AB1"
TREFF_YELLOW = "#FDD000"
TREFF_DARK = "#1A1A2E"
TREFF_LIGHT = "#F5F5F5"

DEFAULT_COLORS = json.dumps({
    "primary": TREFF_BLUE,
    "secondary": TREFF_YELLOW,
    "accent": "#FFFFFF",
    "background": TREFF_DARK
})

DEFAULT_FONTS = json.dumps({
    "heading_font": "Montserrat",
    "body_font": "Inter"
})

# Country-specific color themes
COUNTRY_THEMES = {
    "usa": {"primary": "#B22234", "secondary": "#3C3B6E", "accent": "#FFFFFF"},
    "canada": {"primary": "#FF0000", "secondary": "#FFFFFF", "accent": "#FF0000"},
    "australia": {"primary": "#00843D", "secondary": "#FFCD00", "accent": "#012169"},
    "newzealand": {"primary": "#00247D", "secondary": "#CC142B", "accent": "#FFFFFF"},
    "ireland": {"primary": "#169B62", "secondary": "#FF883E", "accent": "#FFFFFF"},
}


def _make_html(category: str, platform: str, variant: str = "default") -> str:
    """Generate HTML template content for a given category and platform."""
    # Dimensions based on platform
    dims = {
        "feed_square": {"w": 1080, "h": 1080},
        "feed_portrait": {"w": 1080, "h": 1350},
        "story": {"w": 1080, "h": 1920},
        "tiktok": {"w": 1080, "h": 1920},
    }
    d = dims.get(platform, dims["feed_square"])

    return f"""<div class="template-wrapper" style="width:{d['w']}px;height:{d['h']}px;position:relative;overflow:hidden;">
  <div class="template-bg" style="position:absolute;inset:0;background:var(--bg-color, {TREFF_DARK});"></div>
  <div class="template-content" style="position:relative;z-index:1;display:flex;flex-direction:column;height:100%;padding:60px;">
    <div class="template-header" style="margin-bottom:auto;">
      <div class="template-logo" style="width:120px;height:40px;background:{TREFF_BLUE};border-radius:8px;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:14px;">TREFF</div>
    </div>
    <div class="template-body" style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:20px;">
      <h1 class="template-headline" style="font-size:48px;font-weight:800;color:var(--primary-color, {TREFF_BLUE});line-height:1.1;">{{{{headline}}}}</h1>
      <h2 class="template-subheadline" style="font-size:24px;font-weight:600;color:var(--secondary-color, {TREFF_YELLOW});line-height:1.3;">{{{{subheadline}}}}</h2>
      <p class="template-body-text" style="font-size:20px;color:#E5E7EB;line-height:1.5;">{{{{body_text}}}}</p>
    </div>
    <div class="template-footer" style="margin-top:auto;display:flex;justify-content:space-between;align-items:center;">
      <span class="template-cta" style="background:{TREFF_YELLOW};color:{TREFF_DARK};padding:12px 24px;border-radius:8px;font-weight:700;font-size:16px;">{{{{cta_text}}}}</span>
      <span style="color:#9CA3AF;font-size:14px;">@treff_sprachreisen</span>
    </div>
  </div>
</div>"""


def _make_css(category: str) -> str:
    """Generate CSS for template."""
    return f"""
.template-wrapper {{
  font-family: 'Montserrat', 'Inter', sans-serif;
  box-sizing: border-box;
}}
.template-wrapper * {{
  box-sizing: border-box;
}}
.template-headline {{
  text-shadow: 0 2px 4px rgba(0,0,0,0.3);
}}
.template-cta {{
  text-transform: uppercase;
  letter-spacing: 0.5px;
}}
"""


# Define all default templates
DEFAULT_TEMPLATES = [
    # --- LAENDER-SPOTLIGHT ---
    {
        "name": "Laender-Spotlight Feed",
        "category": "laender_spotlight",
        "platform_format": "feed_square",
        "slide_count": 5,
        "placeholder_fields": json.dumps(["headline", "subheadline", "body_text", "cta_text", "image"]),
        "is_default": True,
        "is_country_themed": False,
    },
    {
        "name": "Laender-Spotlight Story",
        "category": "laender_spotlight",
        "platform_format": "story",
        "slide_count": 5,
        "placeholder_fields": json.dumps(["headline", "subheadline", "body_text", "cta_text", "image"]),
        "is_default": True,
        "is_country_themed": False,
    },
    # --- ERFAHRUNGSBERICHTE ---
    {
        "name": "Erfahrungsbericht Quote",
        "category": "erfahrungsberichte",
        "platform_format": "feed_square",
        "slide_count": 1,
        "placeholder_fields": json.dumps(["quote_text", "quote_author", "headline", "image"]),
        "is_default": True,
        "is_country_themed": False,
    },
    {
        "name": "Erfahrungsbericht Carousel",
        "category": "erfahrungsberichte",
        "platform_format": "feed_portrait",
        "slide_count": 5,
        "placeholder_fields": json.dumps(["headline", "subheadline", "body_text", "quote_text", "quote_author", "image"]),
        "is_default": True,
        "is_country_themed": False,
    },
    # --- INFOGRAFIKEN ---
    {
        "name": "Infografik Vergleich",
        "category": "infografiken",
        "platform_format": "feed_square",
        "slide_count": 1,
        "placeholder_fields": json.dumps(["headline", "subheadline", "body_text", "bullet_points"]),
        "is_default": True,
        "is_country_themed": False,
    },
    {
        "name": "Infografik Carousel",
        "category": "infografiken",
        "platform_format": "feed_portrait",
        "slide_count": 5,
        "placeholder_fields": json.dumps(["headline", "subheadline", "body_text", "bullet_points", "image"]),
        "is_default": True,
        "is_country_themed": False,
    },
    # --- FRISTEN/CTA ---
    {
        "name": "Fristen & CTA Bold",
        "category": "fristen_cta",
        "platform_format": "feed_square",
        "slide_count": 1,
        "placeholder_fields": json.dumps(["headline", "subheadline", "cta_text"]),
        "is_default": True,
        "is_country_themed": False,
    },
    {
        "name": "Fristen & CTA Story",
        "category": "fristen_cta",
        "platform_format": "story",
        "slide_count": 1,
        "placeholder_fields": json.dumps(["headline", "subheadline", "cta_text"]),
        "is_default": True,
        "is_country_themed": False,
    },
    # --- TIPPS & TRICKS ---
    {
        "name": "Tipps & Tricks Carousel",
        "category": "tipps_tricks",
        "platform_format": "feed_square",
        "slide_count": 5,
        "placeholder_fields": json.dumps(["headline", "subheadline", "body_text", "bullet_points", "cta_text"]),
        "is_default": True,
        "is_country_themed": False,
    },
    {
        "name": "Tipps & Tricks Story",
        "category": "tipps_tricks",
        "platform_format": "story",
        "slide_count": 5,
        "placeholder_fields": json.dumps(["headline", "body_text", "cta_text"]),
        "is_default": True,
        "is_country_themed": False,
    },
    # --- FAQ ---
    {
        "name": "FAQ Carousel",
        "category": "faq",
        "platform_format": "feed_square",
        "slide_count": 5,
        "placeholder_fields": json.dumps(["headline", "subheadline", "body_text", "cta_text"]),
        "is_default": True,
        "is_country_themed": False,
    },
    {
        "name": "FAQ Story",
        "category": "faq",
        "platform_format": "story",
        "slide_count": 3,
        "placeholder_fields": json.dumps(["headline", "body_text", "cta_text"]),
        "is_default": True,
        "is_country_themed": False,
    },
    # --- FOTO-POSTS ---
    {
        "name": "Foto-Post mit Overlay",
        "category": "foto_posts",
        "platform_format": "feed_square",
        "slide_count": 1,
        "placeholder_fields": json.dumps(["headline", "image", "cta_text"]),
        "is_default": True,
        "is_country_themed": False,
    },
    {
        "name": "Foto-Post Portrait",
        "category": "foto_posts",
        "platform_format": "feed_portrait",
        "slide_count": 1,
        "placeholder_fields": json.dumps(["headline", "subheadline", "image", "cta_text"]),
        "is_default": True,
        "is_country_themed": False,
    },
    # --- REEL/TIKTOK THUMBNAILS ---
    {
        "name": "Reel Thumbnail Bold",
        "category": "reel_tiktok_thumbnails",
        "platform_format": "story",
        "slide_count": 1,
        "placeholder_fields": json.dumps(["headline", "subheadline", "image"]),
        "is_default": True,
        "is_country_themed": False,
    },
    {
        "name": "TikTok Thumbnail Hook",
        "category": "reel_tiktok_thumbnails",
        "platform_format": "tiktok",
        "slide_count": 1,
        "placeholder_fields": json.dumps(["headline", "image"]),
        "is_default": True,
        "is_country_themed": False,
    },
    # --- STORY-POSTS ---
    {
        "name": "Story Poll",
        "category": "story_posts",
        "platform_format": "story",
        "slide_count": 1,
        "placeholder_fields": json.dumps(["headline", "body_text", "cta_text"]),
        "is_default": True,
        "is_country_themed": False,
    },
    {
        "name": "Story Countdown",
        "category": "story_posts",
        "platform_format": "story",
        "slide_count": 1,
        "placeholder_fields": json.dumps(["headline", "subheadline", "cta_text"]),
        "is_default": True,
        "is_country_themed": False,
    },
    # --- COUNTRY-THEMED TEMPLATES ---
    {
        "name": "USA Highschool Spotlight",
        "category": "laender_spotlight",
        "platform_format": "feed_square",
        "slide_count": 5,
        "placeholder_fields": json.dumps(["headline", "subheadline", "body_text", "cta_text", "image"]),
        "is_default": True,
        "is_country_themed": True,
        "country": "usa",
    },
    {
        "name": "Kanada Abenteuer",
        "category": "laender_spotlight",
        "platform_format": "feed_square",
        "slide_count": 5,
        "placeholder_fields": json.dumps(["headline", "subheadline", "body_text", "cta_text", "image"]),
        "is_default": True,
        "is_country_themed": True,
        "country": "canada",
    },
    {
        "name": "Australien Down Under",
        "category": "laender_spotlight",
        "platform_format": "feed_portrait",
        "slide_count": 5,
        "placeholder_fields": json.dumps(["headline", "subheadline", "body_text", "cta_text", "image"]),
        "is_default": True,
        "is_country_themed": True,
        "country": "australia",
    },
]


async def seed_default_templates(db: AsyncSession) -> int:
    """Seed default templates if none exist. Returns count of templates created."""
    # Check if default templates already exist
    result = await db.execute(
        select(func.count()).select_from(Template).where(Template.is_default == True)
    )
    existing_count = result.scalar()

    if existing_count > 0:
        logger.info(f"Found {existing_count} default templates, skipping seed.")
        return 0

    logger.info("No default templates found. Seeding...")
    created = 0

    for tpl_data in DEFAULT_TEMPLATES:
        category = tpl_data["category"]
        platform = tpl_data["platform_format"]

        # Generate HTML and CSS
        html_content = _make_html(category, platform)
        css_content = _make_css(category)

        # Get country-specific colors if applicable
        country = tpl_data.get("country")
        if country and country in COUNTRY_THEMES:
            colors = json.dumps({
                **COUNTRY_THEMES[country],
                "background": TREFF_DARK
            })
        else:
            colors = DEFAULT_COLORS

        template = Template(
            name=tpl_data["name"],
            category=tpl_data["category"],
            platform_format=tpl_data["platform_format"],
            slide_count=tpl_data["slide_count"],
            html_content=html_content,
            css_content=css_content,
            default_colors=colors,
            default_fonts=DEFAULT_FONTS,
            placeholder_fields=tpl_data["placeholder_fields"],
            thumbnail_url=None,
            is_default=True,
            is_country_themed=tpl_data.get("is_country_themed", False),
            country=tpl_data.get("country"),
            version=1,
            parent_template_id=None,
        )
        db.add(template)
        created += 1

    await db.commit()
    logger.info(f"Seeded {created} default templates across all categories.")
    return created
