"""Seed default video branding templates (Intro/Outro) with TREFF branding.

Includes country-specific intro/outro templates for all 5 TREFF destinations:
- USA: Stars & Stripes motif, Navy/Red colors
- Kanada: Maple Leaf animation, Red/White colors
- Australien: Surf/Outback gradient, Earth tones
- Neuseeland: Fern/Kiwi motif, Forest Green/Sky Blue
- Irland: Clover/Rolling Hills motif, Green/Gold

Each template has a corresponding HTML/CSS file in templates/video/intros/ and
templates/video/outros/ for visual reference and potential Puppeteer rendering.
"""

import json
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.video_template import VideoTemplate


# Country-specific configuration for video templates
COUNTRY_CONFIG = {
    "usa": {
        "flag": "🇺🇸",
        "label": "USA",
        "accent": "#B22234",
        "primary": "#002868",
        "secondary": "#BF0A30",
        "motif": "stars_and_stripes",
        "price": "13.800",
    },
    "kanada": {
        "flag": "🇨🇦",
        "label": "Kanada",
        "accent": "#FF0000",
        "primary": "#FF0000",
        "secondary": "#FFFFFF",
        "motif": "maple_leaf",
        "price": "14.900",
    },
    "australien": {
        "flag": "🇦🇺",
        "label": "Australien",
        "accent": "#00843D",
        "primary": "#F4A460",
        "secondary": "#87CEEB",
        "motif": "surf_outback",
        "price": "22.400",
    },
    "neuseeland": {
        "flag": "🇳🇿",
        "label": "Neuseeland",
        "accent": "#00247D",
        "primary": "#228B22",
        "secondary": "#87CEEB",
        "motif": "fern_kiwi",
        "price": "19.800",
    },
    "irland": {
        "flag": "🇮🇪",
        "label": "Irland",
        "accent": "#169B62",
        "primary": "#169B62",
        "secondary": "#FFA500",
        "motif": "clover_hills",
        "price": "14.500",
    },
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

    # ── INTRO TEMPLATES (Country-specific: 5 countries) ──
    {
        "name": "USA Stars & Stripes Intro",
        "description": "Intro mit Stars & Stripes Motiv, Navy/Red Farbwelt und American-Dream-Vibes. Fuer alle USA-Highschool-Inhalte.",
        "template_type": "intro",
        "country": "usa",
        "duration_seconds": 3.0,
        "style": "bold",
        "primary_color": "#002868",
        "secondary_color": "#BF0A30",
        "branding_config": json.dumps({
            "animation": "flag_wave_to_logo",
            "logo_position": "center",
            "background": "usa_stars_stripes",
            "background_gradient": "linear-gradient(135deg, #002868, #1A1A2E, #BF0A30)",
            "text_overlay": "TREFF × USA",
            "subtitle": "Your American Dream",
            "flag_emoji": "🇺🇸",
            "motif": "stars_and_stripes",
            "country_accent": "#B22234",
            "html_template": "templates/video/intros/usa.html",
            "transition_out": "fade_to_content",
        }),
        "cta_text": None,
    },
    {
        "name": "Kanada Maple Leaf Intro",
        "description": "Intro mit fallenden Maple Leaf Animationen, Rot/Weiss Farbwelt. Fuer Kanada-Highschool-Inhalte.",
        "template_type": "intro",
        "country": "kanada",
        "duration_seconds": 3.0,
        "style": "elegant",
        "primary_color": "#FF0000",
        "secondary_color": "#FFFFFF",
        "branding_config": json.dumps({
            "animation": "maple_leaf_fall",
            "logo_position": "center",
            "background": "canada_red_white",
            "background_gradient": "linear-gradient(180deg, #FFFFFF, #FF0000, #8B0000)",
            "text_overlay": "TREFF × Kanada",
            "subtitle": "O Canada!",
            "flag_emoji": "🇨🇦",
            "motif": "maple_leaf",
            "country_accent": "#FF0000",
            "html_template": "templates/video/intros/kanada.html",
            "transition_out": "fade_to_content",
        }),
        "cta_text": None,
    },
    {
        "name": "Australien Surf & Outback Intro",
        "description": "Intro mit Wellen/Outback-Gradient, Earth-Tones und Down-Under-Feeling. Fuer Australien-Highschool-Inhalte.",
        "template_type": "intro",
        "country": "australien",
        "duration_seconds": 3.0,
        "style": "default",
        "primary_color": "#F4A460",
        "secondary_color": "#87CEEB",
        "branding_config": json.dumps({
            "animation": "wave_rise_to_logo",
            "logo_position": "center",
            "background": "australia_surf_outback",
            "background_gradient": "linear-gradient(180deg, #87CEEB, #F4A460, #CD853F, #8B4513)",
            "text_overlay": "TREFF × Australien",
            "subtitle": "Discover Down Under",
            "flag_emoji": "🇦🇺",
            "motif": "surf_outback",
            "country_accent": "#00843D",
            "html_template": "templates/video/intros/australien.html",
            "transition_out": "fade_to_content",
        }),
        "cta_text": None,
    },
    {
        "name": "Neuseeland Fern & Kiwi Intro",
        "description": "Intro mit Fern-Entfaltungs-Animation, Forest-Green/Sky-Blue Farbwelt. Fuer Neuseeland-Highschool-Inhalte.",
        "template_type": "intro",
        "country": "neuseeland",
        "duration_seconds": 3.0,
        "style": "elegant",
        "primary_color": "#228B22",
        "secondary_color": "#87CEEB",
        "branding_config": json.dumps({
            "animation": "fern_unfurl_to_logo",
            "logo_position": "center",
            "background": "nz_fern_mountain",
            "background_gradient": "linear-gradient(180deg, #87CEEB, #228B22, #006400, #1A1A2E)",
            "text_overlay": "TREFF × Neuseeland",
            "subtitle": "Kia Ora!",
            "flag_emoji": "🇳🇿",
            "motif": "fern_kiwi",
            "country_accent": "#00247D",
            "html_template": "templates/video/intros/neuseeland.html",
            "transition_out": "fade_to_content",
        }),
        "cta_text": None,
    },
    {
        "name": "Irland Clover & Hills Intro",
        "description": "Intro mit Clover/Rolling-Hills Motiv, Green/Gold Farbwelt. Fuer Irland-Highschool-Inhalte.",
        "template_type": "intro",
        "country": "irland",
        "duration_seconds": 3.0,
        "style": "elegant",
        "primary_color": "#169B62",
        "secondary_color": "#FFA500",
        "branding_config": json.dumps({
            "animation": "clover_float_to_logo",
            "logo_position": "center",
            "background": "ireland_green_gold",
            "background_gradient": "linear-gradient(180deg, #87CEEB, #169B62, #0D6B3D, #1A1A2E)",
            "text_overlay": "TREFF × Irland",
            "subtitle": "Cead Mile Failte",
            "flag_emoji": "🇮🇪",
            "motif": "clover_hills",
            "country_accent": "#169B62",
            "html_template": "templates/video/intros/irland.html",
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

    # ── OUTRO TEMPLATES (Country-specific: 5 countries) ──
    {
        "name": "USA Stars & Stripes Outro",
        "description": "Outro mit USA Stars & Stripes Branding, Preisinformation und Bewerbungslink.",
        "template_type": "outro",
        "country": "usa",
        "duration_seconds": 4.0,
        "style": "bold",
        "primary_color": "#002868",
        "secondary_color": "#BF0A30",
        "branding_config": json.dumps({
            "animation": "flag_overlay_to_logo",
            "logo_position": "center",
            "background": "usa_stars_stripes",
            "background_gradient": "linear-gradient(135deg, #002868, #1A1A2E, #BF0A30)",
            "show_social_handles": True,
            "show_website": True,
            "show_cta": True,
            "flag_emoji": "🇺🇸",
            "motif": "stars_and_stripes",
            "country_accent": "#B22234",
            "html_template": "templates/video/outros/usa.html",
            "transition_in": "fade_from_content",
        }),
        "cta_text": "USA ab 13.800 EUR - Jetzt bewerben!",
    },
    {
        "name": "Kanada Maple Leaf Outro",
        "description": "Outro mit Kanada Maple Leaf Branding, Preisinformation und natuerlichen Farben.",
        "template_type": "outro",
        "country": "kanada",
        "duration_seconds": 4.0,
        "style": "elegant",
        "primary_color": "#FF0000",
        "secondary_color": "#FFFFFF",
        "branding_config": json.dumps({
            "animation": "maple_overlay_to_logo",
            "logo_position": "center",
            "background": "canada_red_white",
            "background_gradient": "linear-gradient(180deg, #FFFFFF, #FF0000, #8B0000)",
            "show_social_handles": True,
            "show_website": True,
            "show_cta": True,
            "flag_emoji": "🇨🇦",
            "motif": "maple_leaf",
            "country_accent": "#FF0000",
            "html_template": "templates/video/outros/kanada.html",
            "transition_in": "fade_from_content",
        }),
        "cta_text": "Kanada ab 14.900 EUR - Entdecke Kanada!",
    },
    {
        "name": "Australien Surf & Outback Outro",
        "description": "Outro mit Australien-Branding, Surf/Outback-Feeling und Down-Under-CTA.",
        "template_type": "outro",
        "country": "australien",
        "duration_seconds": 4.0,
        "style": "default",
        "primary_color": "#F4A460",
        "secondary_color": "#87CEEB",
        "branding_config": json.dumps({
            "animation": "wave_fade_to_logo",
            "logo_position": "center",
            "background": "australia_surf_outback",
            "background_gradient": "linear-gradient(180deg, #87CEEB, #F4A460, #8B4513)",
            "show_social_handles": True,
            "show_website": True,
            "show_cta": True,
            "flag_emoji": "🇦🇺",
            "motif": "surf_outback",
            "country_accent": "#00843D",
            "html_template": "templates/video/outros/australien.html",
            "transition_in": "fade_from_content",
        }),
        "cta_text": "Australien ab 22.400 EUR - Entdecke Down Under!",
    },
    {
        "name": "Neuseeland Fern & Kiwi Outro",
        "description": "Outro mit Neuseeland Fern-Motiv, Forest-Green Farbwelt und Kia-Ora-CTA.",
        "template_type": "outro",
        "country": "neuseeland",
        "duration_seconds": 4.0,
        "style": "elegant",
        "primary_color": "#228B22",
        "secondary_color": "#87CEEB",
        "branding_config": json.dumps({
            "animation": "fern_fade_to_logo",
            "logo_position": "center",
            "background": "nz_fern_mountain",
            "background_gradient": "linear-gradient(180deg, #87CEEB, #228B22, #006400, #1A1A2E)",
            "show_social_handles": True,
            "show_website": True,
            "show_cta": True,
            "flag_emoji": "🇳🇿",
            "motif": "fern_kiwi",
            "country_accent": "#00247D",
            "html_template": "templates/video/outros/neuseeland.html",
            "transition_in": "fade_from_content",
        }),
        "cta_text": "Neuseeland ab 19.800 EUR - Kia Ora!",
    },
    {
        "name": "Irland Clover & Hills Outro",
        "description": "Outro mit Irland Clover/Rolling-Hills Motiv, Green/Gold Farbwelt und Slainte-CTA.",
        "template_type": "outro",
        "country": "irland",
        "duration_seconds": 4.0,
        "style": "elegant",
        "primary_color": "#169B62",
        "secondary_color": "#FFA500",
        "branding_config": json.dumps({
            "animation": "clover_fade_to_logo",
            "logo_position": "center",
            "background": "ireland_green_gold",
            "background_gradient": "linear-gradient(180deg, #87CEEB, #169B62, #0D6B3D, #1A1A2E)",
            "show_social_handles": True,
            "show_website": True,
            "show_cta": True,
            "flag_emoji": "🇮🇪",
            "motif": "clover_hills",
            "country_accent": "#169B62",
            "html_template": "templates/video/outros/irland.html",
            "transition_in": "fade_from_content",
        }),
        "cta_text": "Irland ab 14.500 EUR - Slainte!",
    },
]


async def seed_video_templates(session: AsyncSession) -> int:
    """Seed default video branding templates, adding any missing ones.

    Creates all generic + country-specific intro/outro templates.
    Total: 3 generic intros + 5 country intros + 4 generic outros + 5 country outros = 17 templates.

    Uses upsert logic: checks which templates already exist by name and only adds missing ones.

    Returns the number of templates seeded.
    """
    # Get existing template names to avoid duplicates
    result = await session.execute(
        select(VideoTemplate.name).where(VideoTemplate.is_default == True)
    )
    existing_names = {row[0] for row in result.fetchall()}

    seeded = 0
    for tmpl_data in DEFAULT_VIDEO_TEMPLATES:
        if tmpl_data["name"] in existing_names:
            continue  # Skip already existing templates

        template = VideoTemplate(
            name=tmpl_data["name"],
            description=tmpl_data["description"],
            template_type=tmpl_data["template_type"],
            country=tmpl_data.get("country"),
            duration_seconds=tmpl_data["duration_seconds"],
            style=tmpl_data.get("style", "default"),
            branding_config=tmpl_data.get("branding_config"),
            cta_text=tmpl_data.get("cta_text"),
            primary_color=tmpl_data.get("primary_color", "#4C8BC2"),
            secondary_color=tmpl_data.get("secondary_color", "#FDD000"),
            social_handle_instagram="@treff_sprachreisen",
            social_handle_tiktok="@treff_sprachreisen",
            website_url="www.treff-sprachreisen.de",
            is_default=True,
            user_id=None,
        )
        session.add(template)
        seeded += 1

    if seeded > 0:
        await session.commit()
    return seeded
