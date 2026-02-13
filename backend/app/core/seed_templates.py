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


def _make_story_teaser_html(variant: str) -> str:
    """Generate HTML for story-teaser feed templates with Story-Frame mockup and arrow icons."""
    d = {"w": 1080, "h": 1080}  # Feed square for teaser posts

    # Different headlines based on variant
    variant_labels = {
        "neue_serie": "NEUE SERIE",
        "fortsetzung": "FORTSETZUNG",
        "finale": "FINALE EPISODE",
    }
    badge_label = variant_labels.get(variant, "STORIES")

    return f"""<div class="template-wrapper story-teaser" style="width:{d['w']}px;height:{d['h']}px;position:relative;overflow:hidden;">
  <div class="template-bg" style="position:absolute;inset:0;background:linear-gradient(135deg, {TREFF_DARK} 0%, #2A2A4E 60%, {TREFF_BLUE} 100%);"></div>
  <div class="template-content" style="position:relative;z-index:1;display:flex;flex-direction:column;height:100%;padding:60px;">
    <div class="template-header" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:30px;">
      <div class="template-logo" style="width:120px;height:40px;background:{TREFF_BLUE};border-radius:8px;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:14px;">TREFF</div>
      <div class="stories-badge" style="background:linear-gradient(45deg, #F58529, #DD2A7B, #8134AF, #515BD4);padding:8px 20px;border-radius:20px;color:#fff;font-weight:800;font-size:14px;letter-spacing:1px;">{badge_label}</div>
    </div>
    <div class="template-body" style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:24px;">
      <div class="story-frame-mockup" style="width:280px;height:380px;border-radius:20px;border:4px solid;border-image:linear-gradient(45deg, #F58529, #DD2A7B, #8134AF) 1;background:rgba(255,255,255,0.05);display:flex;flex-direction:column;align-items:center;justify-content:center;padding:20px;position:relative;">
        <div style="width:60px;height:60px;border-radius:50%;background:rgba(255,255,255,0.15);margin-bottom:12px;display:flex;align-items:center;justify-content:center;font-size:28px;">{{{{student_photo}}}}</div>
        <div style="color:#fff;font-weight:700;font-size:16px;text-align:center;">{{{{student_name}}}}</div>
        <div style="color:{TREFF_YELLOW};font-size:13px;margin-top:4px;text-align:center;">{{{{episode_preview}}}}</div>
      </div>
      <h1 class="template-headline" style="font-size:42px;font-weight:800;color:#FFFFFF;line-height:1.1;text-align:center;">{{{{arc_title}}}}</h1>
      <div class="arrow-cta" style="display:flex;align-items:center;gap:12px;margin-top:8px;">
        <span style="color:{TREFF_YELLOW};font-size:22px;font-weight:700;">{{{{cta_text}}}}</span>
        <span class="arrow-icon" style="font-size:32px;color:{TREFF_YELLOW};animation:bounce 1s infinite;">&#10145;</span>
      </div>
    </div>
    <div class="template-footer" style="margin-top:auto;text-align:center;">
      <span style="color:#9CA3AF;font-size:14px;">@treff_sprachreisen</span>
    </div>
  </div>
</div>"""


def _make_story_teaser_css() -> str:
    """Generate CSS for story-teaser templates with arrow animation."""
    return """
.template-wrapper.story-teaser {
  font-family: 'Montserrat', 'Inter', sans-serif;
  box-sizing: border-box;
}
.template-wrapper.story-teaser * {
  box-sizing: border-box;
}
.template-headline {
  text-shadow: 0 2px 8px rgba(0,0,0,0.5);
}
.stories-badge {
  text-transform: uppercase;
  letter-spacing: 1.5px;
}
.story-frame-mockup {
  box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}
.arrow-icon {
  display: inline-block;
}
@keyframes bounce {
  0%, 100% { transform: translateX(0); }
  50% { transform: translateX(8px); }
}
"""


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
    # --- STORY-TEASER (Feed posts pointing to Story series) ---
    {
        "name": "Story-Teaser: Neue Serie startet!",
        "category": "story_teaser",
        "platform_format": "feed_square",
        "slide_count": 1,
        "placeholder_fields": json.dumps(["arc_title", "episode_preview", "student_name", "student_photo", "cta_text"]),
        "is_default": True,
        "is_country_themed": False,
        "_story_teaser_variant": "neue_serie",
    },
    {
        "name": "Story-Teaser: Fortsetzung in Stories!",
        "category": "story_teaser",
        "platform_format": "feed_square",
        "slide_count": 1,
        "placeholder_fields": json.dumps(["arc_title", "episode_preview", "student_name", "student_photo", "cta_text"]),
        "is_default": True,
        "is_country_themed": False,
        "_story_teaser_variant": "fortsetzung",
    },
    {
        "name": "Story-Teaser: Finale Episode heute!",
        "category": "story_teaser",
        "platform_format": "feed_square",
        "slide_count": 1,
        "placeholder_fields": json.dumps(["arc_title", "episode_preview", "student_name", "student_photo", "cta_text"]),
        "is_default": True,
        "is_country_themed": False,
        "_story_teaser_variant": "finale",
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

        # Generate HTML and CSS - use special templates for story_teaser
        if category == "story_teaser":
            variant = tpl_data.get("_story_teaser_variant", "neue_serie")
            html_content = _make_story_teaser_html(variant)
            css_content = _make_story_teaser_css()
        else:
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


async def seed_story_teaser_templates(db: AsyncSession) -> int:
    """Seed story-teaser templates if they don't exist yet.

    This is a separate function to handle adding story-teaser templates
    to existing installations that already have other default templates.
    """
    # Check if story-teaser templates already exist
    result = await db.execute(
        select(func.count()).select_from(Template).where(
            Template.is_default == True,
            Template.category == "story_teaser",
        )
    )
    existing_count = result.scalar()

    if existing_count > 0:
        logger.info(f"Found {existing_count} story-teaser templates, skipping seed.")
        return 0

    logger.info("No story-teaser templates found. Seeding...")
    created = 0

    story_teaser_templates = [t for t in DEFAULT_TEMPLATES if t.get("category") == "story_teaser"]

    for tpl_data in story_teaser_templates:
        variant = tpl_data.get("_story_teaser_variant", "neue_serie")
        html_content = _make_story_teaser_html(variant)
        css_content = _make_story_teaser_css()

        template = Template(
            name=tpl_data["name"],
            category="story_teaser",
            platform_format=tpl_data["platform_format"],
            slide_count=tpl_data["slide_count"],
            html_content=html_content,
            css_content=css_content,
            default_colors=DEFAULT_COLORS,
            default_fonts=DEFAULT_FONTS,
            placeholder_fields=tpl_data["placeholder_fields"],
            thumbnail_url=None,
            is_default=True,
            is_country_themed=False,
            country=None,
            version=1,
            parent_template_id=None,
        )
        db.add(template)
        created += 1

    await db.commit()
    logger.info(f"Seeded {created} story-teaser templates.")
    return created
