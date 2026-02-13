"""Seed default video branding templates (Intro/Outro) with TREFF branding."""

import json
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.video_template import VideoTemplate


# Country-specific emoji/flag mappings for templates
COUNTRY_CONFIG = {
    "usa": {"flag": "🇺🇸", "label": "USA", "accent": "#B22234"},
    "kanada": {"flag": "🇨🇦", "label": "Kanada", "accent": "#FF0000"},
    "australien": {"flag": "🇦🇺", "label": "Australien", "accent": "#00843D"},
    "neuseeland": {"flag": "🇳🇿", "label": "Neuseeland", "accent": "#00247D"},
    "irland": {"flag": "🇮🇪", "label": "Irland", "accent": "#169B62"},
}


DEFAULT_VIDEO_TEMPLATES = [
    # ── INTRO TEMPLATES (Generic) ──
    {
        "name": "TREFF Classic Intro",
        "description": "Klassisches TREFF-Intro mit Logo-Animation und blau-gelbem Farbuebergang. Perfekt fuer alle Reels und TikToks.",
        "template_type": "intro",
        "country": None,
        "duration_seconds": 3.0,
        "style": "default",
        "branding_config": json.dumps({
            "animation": "logo_fade_in",
            "logo_position": "center",
            "background": "gradient_blue_yellow",
            "text_overlay": "TREFF Sprachreisen",
            "subtitle": "Dein Highschool-Abenteuer",
            "transition_out": "fade_to_content",
        }),
        "cta_text": None,
    },
    {
        "name": "TREFF Modern Intro",
        "description": "Modernes, minimalistisches Intro mit schnellem Logo-Reveal und dynamischem Texteinblender.",
        "template_type": "intro",
        "country": None,
        "duration_seconds": 2.5,
        "style": "minimal",
        "branding_config": json.dumps({
            "animation": "logo_slide_up",
            "logo_position": "center",
            "background": "solid_dark",
            "text_overlay": "TREFF",
            "subtitle": None,
            "transition_out": "wipe_right",
        }),
        "cta_text": None,
    },
    {
        "name": "TREFF Bold Intro",
        "description": "Auffaelliges Intro mit grossem Schriftzug und energetischer Animation. Ideal fuer TikTok.",
        "template_type": "intro",
        "country": None,
        "duration_seconds": 2.0,
        "style": "bold",
        "branding_config": json.dumps({
            "animation": "text_zoom_in",
            "logo_position": "top_center",
            "background": "gradient_yellow_blue",
            "text_overlay": "TREFF SPRACHREISEN",
            "subtitle": "Seit 1984",
            "transition_out": "cut",
        }),
        "cta_text": None,
    },
    # ── INTRO TEMPLATES (Country-specific) ──
    {
        "name": "USA Highschool Intro",
        "description": "Intro mit USA-Flagge und American-Dream-Vibes. Fuer alle USA-Highschool-Inhalte.",
        "template_type": "intro",
        "country": "usa",
        "duration_seconds": 3.0,
        "style": "default",
        "branding_config": json.dumps({
            "animation": "flag_wave_to_logo",
            "logo_position": "center",
            "background": "usa_flag_gradient",
            "text_overlay": "TREFF × USA",
            "subtitle": "Your American Dream",
            "flag_emoji": "🇺🇸",
            "transition_out": "fade_to_content",
        }),
        "cta_text": None,
    },
    {
        "name": "Kanada Maple Intro",
        "description": "Intro mit Kanada-Maple-Leaf und natuerlichen Farben. Fuer Kanada-Inhalte.",
        "template_type": "intro",
        "country": "kanada",
        "duration_seconds": 3.0,
        "style": "elegant",
        "branding_config": json.dumps({
            "animation": "maple_leaf_fall",
            "logo_position": "center",
            "background": "canada_red_white",
            "text_overlay": "TREFF × Kanada",
            "subtitle": "O Canada!",
            "flag_emoji": "🇨🇦",
            "transition_out": "fade_to_content",
        }),
        "cta_text": None,
    },
    # ── OUTRO TEMPLATES (Generic) ──
    {
        "name": "TREFF Classic Outro",
        "description": "Standard-Outro mit Logo, Social-Handles und Website. CTA: Jetzt informieren!",
        "template_type": "outro",
        "country": None,
        "duration_seconds": 4.0,
        "style": "default",
        "branding_config": json.dumps({
            "animation": "content_fade_to_logo",
            "logo_position": "center",
            "background": "gradient_blue_yellow",
            "show_social_handles": True,
            "show_website": True,
            "show_cta": True,
            "transition_in": "fade_from_content",
        }),
        "cta_text": "Jetzt informieren!",
    },
    {
        "name": "TREFF Follow-CTA Outro",
        "description": "Outro mit starkem Follow-Aufruf, Social-Icons und Swipe-Up-Animation.",
        "template_type": "outro",
        "country": None,
        "duration_seconds": 3.5,
        "style": "bold",
        "branding_config": json.dumps({
            "animation": "social_icons_pop_in",
            "logo_position": "top_center",
            "background": "solid_treff_blue",
            "show_social_handles": True,
            "show_website": False,
            "show_cta": True,
            "transition_in": "slide_up",
        }),
        "cta_text": "Folge uns fuer mehr!",
    },
    {
        "name": "TREFF Elegant Outro",
        "description": "Elegantes, ruhiges Outro mit dezenter Animation. Fuer serioeseere Inhalte.",
        "template_type": "outro",
        "country": None,
        "duration_seconds": 4.0,
        "style": "elegant",
        "branding_config": json.dumps({
            "animation": "logo_slow_reveal",
            "logo_position": "center",
            "background": "gradient_dark_to_blue",
            "show_social_handles": True,
            "show_website": True,
            "show_cta": True,
            "transition_in": "dissolve",
        }),
        "cta_text": "Entdecke dein Abenteuer",
    },
    {
        "name": "TREFF Minimal Outro",
        "description": "Minimalistisches Outro nur mit Logo und Website. Schnell und clean.",
        "template_type": "outro",
        "country": None,
        "duration_seconds": 2.5,
        "style": "minimal",
        "branding_config": json.dumps({
            "animation": "simple_fade",
            "logo_position": "center",
            "background": "solid_white",
            "show_social_handles": False,
            "show_website": True,
            "show_cta": False,
            "transition_in": "cut",
        }),
        "cta_text": None,
    },
    # ── OUTRO TEMPLATES (Country-specific) ──
    {
        "name": "USA Outro",
        "description": "Outro mit USA-Branding, Preisinformation und Bewerbungslink.",
        "template_type": "outro",
        "country": "usa",
        "duration_seconds": 4.0,
        "style": "default",
        "branding_config": json.dumps({
            "animation": "flag_overlay_to_logo",
            "logo_position": "center",
            "background": "usa_gradient",
            "show_social_handles": True,
            "show_website": True,
            "show_cta": True,
            "flag_emoji": "🇺🇸",
            "transition_in": "fade_from_content",
        }),
        "cta_text": "USA ab 13.800 EUR - Jetzt bewerben!",
    },
    {
        "name": "Australien Outro",
        "description": "Outro mit Australien-Branding und Down-Under-Feeling.",
        "template_type": "outro",
        "country": "australien",
        "duration_seconds": 4.0,
        "style": "default",
        "branding_config": json.dumps({
            "animation": "flag_overlay_to_logo",
            "logo_position": "center",
            "background": "australia_gradient",
            "show_social_handles": True,
            "show_website": True,
            "show_cta": True,
            "flag_emoji": "🇦🇺",
            "transition_in": "fade_from_content",
        }),
        "cta_text": "Australien ab 22.400 EUR - Entdecke Down Under!",
    },
]


async def seed_video_templates(session: AsyncSession) -> int:
    """Seed default video branding templates if none exist.

    Returns the number of templates seeded.
    """
    result = await session.execute(
        select(func.count(VideoTemplate.id)).where(VideoTemplate.is_default == True)
    )
    count = result.scalar() or 0

    if count > 0:
        return 0  # Already seeded

    seeded = 0
    for tmpl_data in DEFAULT_VIDEO_TEMPLATES:
        template = VideoTemplate(
            name=tmpl_data["name"],
            description=tmpl_data["description"],
            template_type=tmpl_data["template_type"],
            country=tmpl_data.get("country"),
            duration_seconds=tmpl_data["duration_seconds"],
            style=tmpl_data.get("style", "default"),
            branding_config=tmpl_data.get("branding_config"),
            cta_text=tmpl_data.get("cta_text"),
            primary_color="#4C8BC2",
            secondary_color="#FDD000",
            social_handle_instagram="@treff_sprachreisen",
            social_handle_tiktok="@treff_sprachreisen",
            website_url="www.treff-sprachreisen.de",
            is_default=True,
            user_id=None,
        )
        session.add(template)
        seeded += 1

    await session.commit()
    return seeded
