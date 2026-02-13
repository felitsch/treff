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


def _make_story_series_html(variant: str, country: str = None) -> str:
    """Generate HTML for story-series templates optimized for multi-part Instagram Stories.

    These templates have a consistent design with series title, episode number,
    progress bar, and navigation hints for brand recognition across episodes.
    """
    d = {"w": 1080, "h": 1920}  # Story 9:16 format

    # Country-specific accent colors
    country_accent = {
        "usa": "#B22234",
        "canada": "#FF0000",
        "australia": "#00843D",
        "newzealand": "#00247D",
        "ireland": "#169B62",
    }
    accent = country_accent.get(country, TREFF_BLUE)

    if variant == "intro":
        # Intro slide: "Jonathans Geschichte — Teil 3: Der erste Schneetag"
        return f"""<div class="template-wrapper story-series story-series-intro" style="width:{d['w']}px;height:{d['h']}px;position:relative;overflow:hidden;">
  <div class="template-bg" style="position:absolute;inset:0;background:linear-gradient(180deg, {TREFF_DARK} 0%, #1E2A4A 50%, {accent} 100%);"></div>
  <div class="template-content" style="position:relative;z-index:1;display:flex;flex-direction:column;height:100%;padding:60px 50px;">
    <div class="template-header" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:40px;">
      <div class="template-logo" style="width:100px;height:36px;background:{TREFF_BLUE};border-radius:6px;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:13px;letter-spacing:1px;">TREFF</div>
      <div class="series-badge" style="background:linear-gradient(135deg, {accent}, {TREFF_YELLOW});padding:8px 18px;border-radius:16px;color:#fff;font-weight:800;font-size:13px;letter-spacing:1px;">SERIE</div>
    </div>
    <div class="template-body" style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:28px;text-align:center;">
      <div class="student-avatar" style="width:140px;height:140px;border-radius:50%;border:4px solid {TREFF_YELLOW};background:rgba(255,255,255,0.08);display:flex;align-items:center;justify-content:center;font-size:56px;">{{{{student_name_initial}}}}</div>
      <div class="arc-label" style="color:{TREFF_YELLOW};font-size:16px;font-weight:600;letter-spacing:2px;text-transform:uppercase;">{{{{arc_title}}}}</div>
      <h1 class="template-headline" style="font-size:52px;font-weight:800;color:#FFFFFF;line-height:1.15;">{{{{student_name}}}}s Geschichte</h1>
      <div class="episode-label" style="font-size:28px;font-weight:600;color:rgba(255,255,255,0.85);">Teil {{{{episode_number}}}} — {{{{episode_title}}}}</div>
      <div class="progress-bar-container" style="width:80%;max-width:600px;margin-top:20px;">
        <div class="progress-label" style="display:flex;justify-content:space-between;margin-bottom:10px;font-size:14px;color:rgba(255,255,255,0.6);">
          <span>Episode {{{{episode_number}}}}</span>
          <span>von {{{{total_episodes}}}}</span>
        </div>
        <div class="progress-track" style="height:8px;background:rgba(255,255,255,0.15);border-radius:4px;overflow:hidden;">
          <div class="progress-fill" style="height:100%;background:linear-gradient(90deg, {TREFF_YELLOW}, {accent});border-radius:4px;width:40%;transition:width 0.5s;"></div>
        </div>
      </div>
    </div>
    <div class="template-footer" style="text-align:center;padding-top:30px;">
      <div class="swipe-hint" style="color:rgba(255,255,255,0.5);font-size:15px;display:flex;flex-direction:column;align-items:center;gap:8px;">
        <span class="swipe-arrow" style="font-size:24px;animation:swipeUp 1.5s infinite;">&#8593;</span>
        Wische nach oben fuer mehr
      </div>
      <div style="margin-top:16px;color:rgba(255,255,255,0.35);font-size:12px;">@treff_sprachreisen</div>
    </div>
  </div>
</div>"""

    elif variant == "recap":
        # Recap slide: "Bisher passiert..." with mini summary
        return f"""<div class="template-wrapper story-series story-series-recap" style="width:{d['w']}px;height:{d['h']}px;position:relative;overflow:hidden;">
  <div class="template-bg" style="position:absolute;inset:0;background:linear-gradient(180deg, #0F1629 0%, {TREFF_DARK} 100%);"></div>
  <div class="template-content" style="position:relative;z-index:1;display:flex;flex-direction:column;height:100%;padding:60px 50px;">
    <div class="template-header" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:30px;">
      <div class="template-logo" style="width:100px;height:36px;background:{TREFF_BLUE};border-radius:6px;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:13px;">TREFF</div>
      <div class="episode-badge" style="background:rgba(255,255,255,0.1);padding:6px 16px;border-radius:12px;color:rgba(255,255,255,0.7);font-weight:600;font-size:13px;">EP {{{{episode_number}}}} / {{{{total_episodes}}}}</div>
    </div>
    <div class="series-title-bar" style="background:rgba(255,255,255,0.05);border-left:4px solid {TREFF_YELLOW};padding:12px 18px;border-radius:0 8px 8px 0;margin-bottom:40px;">
      <div style="color:{TREFF_YELLOW};font-size:13px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;">{{{{arc_title}}}}</div>
      <div style="color:rgba(255,255,255,0.6);font-size:14px;margin-top:4px;">{{{{student_name}}}}s Geschichte</div>
    </div>
    <div class="template-body" style="flex:1;display:flex;flex-direction:column;gap:30px;">
      <h1 class="template-headline" style="font-size:44px;font-weight:800;color:#FFFFFF;line-height:1.15;">Bisher passiert...</h1>
      <div class="recap-box" style="background:rgba(255,255,255,0.06);border-radius:16px;padding:30px;flex:1;">
        <p class="recap-text" style="font-size:22px;color:rgba(255,255,255,0.85);line-height:1.6;">{{{{previously_text}}}}</p>
      </div>
      <div class="progress-bar-container" style="width:100%;">
        <div class="progress-track" style="height:6px;background:rgba(255,255,255,0.1);border-radius:3px;overflow:hidden;">
          <div class="progress-fill" style="height:100%;background:linear-gradient(90deg, {TREFF_YELLOW}, {accent});border-radius:3px;width:40%;"></div>
        </div>
        <div class="progress-label" style="display:flex;justify-content:space-between;margin-top:8px;font-size:12px;color:rgba(255,255,255,0.4);">
          <span>Episode {{{{episode_number}}}} von {{{{total_episodes}}}}</span>
          <span>{{{{arc_title}}}}</span>
        </div>
      </div>
    </div>
    <div class="template-footer" style="text-align:center;padding-top:24px;">
      <div style="color:rgba(255,255,255,0.5);font-size:14px;">Tippe fuer die naechste Slide &#10145;</div>
      <div style="margin-top:12px;color:rgba(255,255,255,0.3);font-size:12px;">@treff_sprachreisen</div>
    </div>
  </div>
</div>"""

    elif variant == "episode":
        # Standard episode slide with content area and progress
        return f"""<div class="template-wrapper story-series story-series-episode" style="width:{d['w']}px;height:{d['h']}px;position:relative;overflow:hidden;">
  <div class="template-bg" style="position:absolute;inset:0;background:linear-gradient(180deg, {TREFF_DARK} 0%, #1A2544 60%, {accent}33 100%);"></div>
  <div class="template-content" style="position:relative;z-index:1;display:flex;flex-direction:column;height:100%;padding:60px 50px;">
    <div class="template-header" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:24px;">
      <div class="template-logo" style="width:100px;height:36px;background:{TREFF_BLUE};border-radius:6px;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:13px;">TREFF</div>
      <div class="episode-badge" style="background:{accent};padding:8px 18px;border-radius:20px;color:#fff;font-weight:800;font-size:14px;">EP {{{{episode_number}}}}</div>
    </div>
    <div class="series-title-bar" style="display:flex;align-items:center;gap:12px;margin-bottom:20px;">
      <div class="student-avatar-sm" style="width:44px;height:44px;border-radius:50%;border:3px solid {TREFF_YELLOW};background:rgba(255,255,255,0.08);display:flex;align-items:center;justify-content:center;font-size:18px;color:#fff;font-weight:700;">{{{{student_name_initial}}}}</div>
      <div>
        <div style="color:#fff;font-weight:700;font-size:15px;">{{{{student_name}}}}</div>
        <div style="color:{TREFF_YELLOW};font-size:12px;font-weight:600;letter-spacing:1px;text-transform:uppercase;">{{{{arc_title}}}}</div>
      </div>
    </div>
    <div class="progress-bar-container" style="margin-bottom:32px;">
      <div class="progress-track" style="height:4px;background:rgba(255,255,255,0.1);border-radius:2px;overflow:hidden;">
        <div class="progress-fill" style="height:100%;background:linear-gradient(90deg, {TREFF_YELLOW}, {accent});border-radius:2px;width:40%;"></div>
      </div>
    </div>
    <div class="template-body" style="flex:1;display:flex;flex-direction:column;gap:24px;">
      <h1 class="template-headline" style="font-size:40px;font-weight:800;color:#FFFFFF;line-height:1.15;">{{{{episode_title}}}}</h1>
      <p class="template-body-text" style="font-size:22px;color:rgba(255,255,255,0.85);line-height:1.6;">{{{{body_text}}}}</p>
    </div>
    <div class="template-footer" style="margin-top:auto;padding-top:30px;">
      <div class="progress-label" style="display:flex;justify-content:space-between;font-size:13px;color:rgba(255,255,255,0.45);margin-bottom:16px;">
        <span>Episode {{{{episode_number}}}} von {{{{total_episodes}}}}</span>
        <span>{{{{arc_title}}}}</span>
      </div>
      <div style="text-align:center;color:rgba(255,255,255,0.4);font-size:12px;">@treff_sprachreisen</div>
    </div>
  </div>
</div>"""

    elif variant == "cliffhanger":
        # Cliffhanger slide: "Morgen geht es weiter!"
        return f"""<div class="template-wrapper story-series story-series-cliffhanger" style="width:{d['w']}px;height:{d['h']}px;position:relative;overflow:hidden;">
  <div class="template-bg" style="position:absolute;inset:0;background:linear-gradient(180deg, {TREFF_DARK} 0%, #0D0D1A 50%, {accent}44 100%);"></div>
  <div class="template-content" style="position:relative;z-index:1;display:flex;flex-direction:column;height:100%;padding:60px 50px;">
    <div class="template-header" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:24px;">
      <div class="template-logo" style="width:100px;height:36px;background:{TREFF_BLUE};border-radius:6px;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:13px;">TREFF</div>
      <div class="episode-badge" style="background:rgba(255,255,255,0.1);padding:6px 16px;border-radius:12px;color:rgba(255,255,255,0.7);font-weight:600;font-size:13px;">EP {{{{episode_number}}}} / {{{{total_episodes}}}}</div>
    </div>
    <div class="series-title-bar" style="display:flex;align-items:center;gap:12px;margin-bottom:20px;">
      <div class="student-avatar-sm" style="width:44px;height:44px;border-radius:50%;border:3px solid {TREFF_YELLOW};background:rgba(255,255,255,0.08);display:flex;align-items:center;justify-content:center;font-size:18px;color:#fff;font-weight:700;">{{{{student_name_initial}}}}</div>
      <div>
        <div style="color:#fff;font-weight:700;font-size:15px;">{{{{student_name}}}}</div>
        <div style="color:{TREFF_YELLOW};font-size:12px;font-weight:600;letter-spacing:1px;text-transform:uppercase;">{{{{arc_title}}}}</div>
      </div>
    </div>
    <div class="template-body" style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:32px;">
      <div class="cliffhanger-icon" style="font-size:80px;animation:pulse 2s infinite;">&#128064;</div>
      <p class="cliffhanger-text" style="font-size:28px;color:rgba(255,255,255,0.9);line-height:1.5;font-style:italic;max-width:800px;">{{{{cliffhanger_text}}}}</p>
      <div class="divider" style="width:60px;height:3px;background:{TREFF_YELLOW};border-radius:2px;"></div>
      <h1 class="template-headline" style="font-size:48px;font-weight:800;color:{TREFF_YELLOW};line-height:1.2;">Morgen geht es weiter!</h1>
      <p class="next-hint" style="font-size:18px;color:rgba(255,255,255,0.5);">{{{{next_episode_hint}}}}</p>
    </div>
    <div class="template-footer" style="margin-top:auto;padding-top:24px;">
      <div class="progress-bar-container" style="width:100%;margin-bottom:16px;">
        <div class="progress-track" style="height:6px;background:rgba(255,255,255,0.1);border-radius:3px;overflow:hidden;">
          <div class="progress-fill" style="height:100%;background:linear-gradient(90deg, {TREFF_YELLOW}, {accent});border-radius:3px;width:40%;"></div>
        </div>
        <div class="progress-label" style="display:flex;justify-content:space-between;margin-top:8px;font-size:12px;color:rgba(255,255,255,0.4);">
          <span>Episode {{{{episode_number}}}} von {{{{total_episodes}}}}</span>
          <span>Fortsetzung folgt...</span>
        </div>
      </div>
      <div style="text-align:center;color:rgba(255,255,255,0.3);font-size:12px;">@treff_sprachreisen</div>
    </div>
  </div>
</div>"""

    elif variant == "finale":
        # Finale slide: Series completion celebration
        return f"""<div class="template-wrapper story-series story-series-finale" style="width:{d['w']}px;height:{d['h']}px;position:relative;overflow:hidden;">
  <div class="template-bg" style="position:absolute;inset:0;background:linear-gradient(180deg, {accent} 0%, {TREFF_DARK} 50%, #0A0A1A 100%);"></div>
  <div class="template-content" style="position:relative;z-index:1;display:flex;flex-direction:column;height:100%;padding:60px 50px;">
    <div class="template-header" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:30px;">
      <div class="template-logo" style="width:100px;height:36px;background:{TREFF_BLUE};border-radius:6px;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:13px;">TREFF</div>
      <div class="finale-badge" style="background:linear-gradient(135deg, {TREFF_YELLOW}, #FFB800);padding:8px 20px;border-radius:16px;color:{TREFF_DARK};font-weight:800;font-size:13px;letter-spacing:1px;">FINALE</div>
    </div>
    <div class="template-body" style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:28px;">
      <div class="celebration-icon" style="font-size:72px;">&#127881;</div>
      <div class="student-avatar" style="width:120px;height:120px;border-radius:50%;border:4px solid {TREFF_YELLOW};background:rgba(255,255,255,0.1);display:flex;align-items:center;justify-content:center;font-size:48px;">{{{{student_name_initial}}}}</div>
      <h1 class="template-headline" style="font-size:44px;font-weight:800;color:#FFFFFF;line-height:1.15;">{{{{episode_title}}}}</h1>
      <div class="arc-label" style="color:{TREFF_YELLOW};font-size:18px;font-weight:600;">{{{{arc_title}}}} — Das Finale</div>
      <p class="template-body-text" style="font-size:22px;color:rgba(255,255,255,0.85);line-height:1.6;max-width:800px;">{{{{body_text}}}}</p>
      <div class="progress-bar-container" style="width:80%;max-width:600px;margin-top:16px;">
        <div class="progress-track" style="height:8px;background:rgba(255,255,255,0.15);border-radius:4px;overflow:hidden;">
          <div class="progress-fill" style="height:100%;background:linear-gradient(90deg, {TREFF_YELLOW}, #FFB800, {accent});border-radius:4px;width:100%;"></div>
        </div>
        <div class="progress-label" style="display:flex;justify-content:center;margin-top:10px;font-size:14px;color:{TREFF_YELLOW};font-weight:600;">
          <span>Episode {{{{episode_number}}}} von {{{{total_episodes}}}} — Abgeschlossen!</span>
        </div>
      </div>
    </div>
    <div class="template-footer" style="text-align:center;padding-top:24px;">
      <div class="cta-container" style="margin-bottom:16px;">
        <span class="template-cta" style="display:inline-block;background:{TREFF_YELLOW};color:{TREFF_DARK};padding:14px 32px;border-radius:12px;font-weight:800;font-size:18px;">{{{{cta_text}}}}</span>
      </div>
      <div style="color:rgba(255,255,255,0.3);font-size:12px;">@treff_sprachreisen</div>
    </div>
  </div>
</div>"""

    # Fallback to episode variant
    return _make_story_series_html("episode", country)


def _make_story_series_css() -> str:
    """Generate CSS for story-series templates with animations."""
    return """
.template-wrapper.story-series {
  font-family: 'Montserrat', 'Inter', sans-serif;
  box-sizing: border-box;
}
.template-wrapper.story-series * {
  box-sizing: border-box;
}
.template-headline {
  text-shadow: 0 2px 8px rgba(0,0,0,0.4);
}
.series-badge, .finale-badge {
  text-transform: uppercase;
  letter-spacing: 1.5px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}
.episode-badge {
  backdrop-filter: blur(4px);
}
.student-avatar, .student-avatar-sm {
  box-shadow: 0 4px 16px rgba(0,0,0,0.3);
}
.recap-box {
  backdrop-filter: blur(4px);
  border: 1px solid rgba(255,255,255,0.08);
}
.progress-fill {
  transition: width 0.5s ease-out;
}
.cliffhanger-text {
  text-shadow: 0 1px 4px rgba(0,0,0,0.3);
}
.template-cta {
  text-transform: uppercase;
  letter-spacing: 0.5px;
  box-shadow: 0 4px 16px rgba(253,208,0,0.3);
}
@keyframes swipeUp {
  0%, 100% { transform: translateY(0); opacity: 0.5; }
  50% { transform: translateY(-8px); opacity: 1; }
}
@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}
"""


# Country-specific series color themes
SERIES_COUNTRY_THEMES = {
    "usa": {"primary": "#B22234", "secondary": "#3C3B6E", "accent": "#FFFFFF", "background": "#1A1A2E"},
    "canada": {"primary": "#FF0000", "secondary": "#FFFFFF", "accent": "#FF0000", "background": "#1A1A2E"},
    "australia": {"primary": "#00843D", "secondary": "#FFCD00", "accent": "#012169", "background": "#1A1A2E"},
    "newzealand": {"primary": "#00247D", "secondary": "#CC142B", "accent": "#FFFFFF", "background": "#1A1A2E"},
    "ireland": {"primary": "#169B62", "secondary": "#FF883E", "accent": "#FFFFFF", "background": "#1A1A2E"},
}

# Story series template definitions
STORY_SERIES_TEMPLATES = [
    {
        "name": "Serien-Intro: Neue Episode",
        "category": "story_series",
        "platform_format": "story",
        "slide_count": 1,
        "placeholder_fields": json.dumps(["arc_title", "episode_number", "episode_title", "student_name", "student_name_initial", "total_episodes"]),
        "is_default": True,
        "is_country_themed": False,
        "_story_series_variant": "intro",
    },
    {
        "name": "Serien-Recap: Bisher passiert",
        "category": "story_series",
        "platform_format": "story",
        "slide_count": 1,
        "placeholder_fields": json.dumps(["arc_title", "episode_number", "student_name", "previously_text", "total_episodes"]),
        "is_default": True,
        "is_country_themed": False,
        "_story_series_variant": "recap",
    },
    {
        "name": "Serien-Episode: Standard",
        "category": "story_series",
        "platform_format": "story",
        "slide_count": 1,
        "placeholder_fields": json.dumps(["arc_title", "episode_number", "episode_title", "student_name", "student_name_initial", "body_text", "total_episodes"]),
        "is_default": True,
        "is_country_themed": False,
        "_story_series_variant": "episode",
    },
    {
        "name": "Serien-Cliffhanger: Morgen weiter!",
        "category": "story_series",
        "platform_format": "story",
        "slide_count": 1,
        "placeholder_fields": json.dumps(["arc_title", "episode_number", "student_name", "student_name_initial", "cliffhanger_text", "next_episode_hint", "total_episodes"]),
        "is_default": True,
        "is_country_themed": False,
        "_story_series_variant": "cliffhanger",
    },
    {
        "name": "Serien-Finale: Abschluss",
        "category": "story_series",
        "platform_format": "story",
        "slide_count": 1,
        "placeholder_fields": json.dumps(["arc_title", "episode_number", "episode_title", "student_name", "student_name_initial", "body_text", "cta_text", "total_episodes"]),
        "is_default": True,
        "is_country_themed": False,
        "_story_series_variant": "finale",
    },
]


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
    # --- STORY-SERIEN (Instagram Story series templates) ---
    *STORY_SERIES_TEMPLATES,
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

        # Generate HTML and CSS - use special templates for story_teaser and story_series
        if category == "story_teaser":
            variant = tpl_data.get("_story_teaser_variant", "neue_serie")
            html_content = _make_story_teaser_html(variant)
            css_content = _make_story_teaser_css()
        elif category == "story_series":
            variant = tpl_data.get("_story_series_variant", "episode")
            html_content = _make_story_series_html(variant)
            css_content = _make_story_series_css()
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


async def seed_story_series_templates(db: AsyncSession) -> int:
    """Seed story-series templates if they don't exist yet.

    These are Instagram Story templates optimized for multi-part series:
    Intro, Recap, Standard Episode, Cliffhanger, and Finale slides.
    Each has a consistent design with series title, episode number,
    progress bar, and navigation hints.
    """
    # Check if story-series templates already exist
    result = await db.execute(
        select(func.count()).select_from(Template).where(
            Template.is_default == True,
            Template.category == "story_series",
        )
    )
    existing_count = result.scalar()

    if existing_count > 0:
        logger.info(f"Found {existing_count} story-series templates, skipping seed.")
        return 0

    logger.info("No story-series templates found. Seeding...")
    created = 0

    for tpl_data in STORY_SERIES_TEMPLATES:
        variant = tpl_data.get("_story_series_variant", "episode")
        country = tpl_data.get("country")
        html_content = _make_story_series_html(variant, country)
        css_content = _make_story_series_css()

        # Use country-specific colors if applicable
        if country and country in SERIES_COUNTRY_THEMES:
            colors = json.dumps(SERIES_COUNTRY_THEMES[country])
        else:
            colors = DEFAULT_COLORS

        template = Template(
            name=tpl_data["name"],
            category="story_series",
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
    logger.info(f"Seeded {created} story-series templates.")
    return created
