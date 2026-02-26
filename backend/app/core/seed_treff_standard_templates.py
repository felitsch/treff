"""Seed TREFF Standard-Templates — 10 vorgefertigte Templates fuer die haeufigsten Post-Typen.

These templates are immediately usable and cover the most common post types:
Erfahrungsbericht, Countdown, Land-Factsheet, Motivations-Quote, Vorher/Nachher,
Event-Ankuendigung, Tipp der Woche, Story-Umfrage, Bewerbungs-CTA, Carousel-Slide.

All templates use TREFF brand colors (#4C8BC2 / #FDD000), Montserrat/Inter fonts,
and include a TREFF logo placeholder.
"""

import json
import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.template import Template

logger = logging.getLogger(__name__)

# TREFF Brand colors (consistent with seed_templates.py)
TREFF_BLUE = "#3B7AB1"
TREFF_YELLOW = "#FDD000"
TREFF_DARK = "#1A1A2E"
TREFF_LIGHT = "#F5F5F5"

DEFAULT_COLORS = json.dumps({
    "primary": TREFF_BLUE,
    "secondary": TREFF_YELLOW,
    "accent": "#FFFFFF",
    "background": TREFF_DARK,
})

DEFAULT_FONTS = json.dumps({
    "heading_font": "Montserrat",
    "body_font": "Inter",
})

# Marker name prefix so we can detect these templates
STANDARD_PREFIX = "TREFF Standard:"


def _html_erfahrungsbericht() -> str:
    """Erfahrungsbericht — Foto + Quote-Overlay + Name/Land."""
    return f"""<div class="template-wrapper treff-erfahrungsbericht" style="width:1080px;height:1080px;position:relative;overflow:hidden;">
  <div class="template-bg" style="position:absolute;inset:0;background:linear-gradient(180deg, {TREFF_DARK} 0%, #1E2A4A 100%);"></div>
  <div class="photo-area" style="position:absolute;top:0;left:0;right:0;height:55%;background:rgba(255,255,255,0.05);display:flex;align-items:center;justify-content:center;">
    <div style="width:100%;height:100%;background:rgba(59,122,177,0.15);display:flex;align-items:center;justify-content:center;font-size:64px;color:rgba(255,255,255,0.2);">{{{{image}}}}</div>
  </div>
  <div class="quote-overlay" style="position:absolute;bottom:0;left:0;right:0;height:55%;background:linear-gradient(0deg, {TREFF_DARK} 60%, transparent 100%);display:flex;flex-direction:column;justify-content:flex-end;padding:50px 60px;">
    <div class="template-logo" style="width:100px;height:34px;background:{TREFF_BLUE};border-radius:6px;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:12px;letter-spacing:1px;margin-bottom:20px;">TREFF</div>
    <div class="quote-mark" style="font-size:48px;color:{TREFF_YELLOW};line-height:1;margin-bottom:8px;">&ldquo;</div>
    <p class="quote-text" style="font-size:28px;font-weight:600;color:#FFFFFF;line-height:1.4;margin-bottom:20px;font-style:italic;">{{{{quote_text}}}}</p>
    <div class="author-row" style="display:flex;align-items:center;gap:16px;">
      <div class="author-avatar" style="width:48px;height:48px;border-radius:50%;background:{TREFF_BLUE};display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:20px;">{{{{quote_author_initial}}}}</div>
      <div>
        <div style="color:#FFFFFF;font-weight:700;font-size:18px;">{{{{quote_author}}}}</div>
        <div style="color:{TREFF_YELLOW};font-size:14px;font-weight:500;">{{{{country_label}}}}</div>
      </div>
    </div>
  </div>
</div>"""


def _css_erfahrungsbericht() -> str:
    return """.template-wrapper.treff-erfahrungsbericht {
  font-family: 'Montserrat', 'Inter', sans-serif;
  box-sizing: border-box;
}
.template-wrapper.treff-erfahrungsbericht * { box-sizing: border-box; }
.quote-text { text-shadow: 0 2px 8px rgba(0,0,0,0.4); }
.quote-mark { text-shadow: 0 2px 4px rgba(0,0,0,0.3); }
"""


def _html_countdown() -> str:
    """Countdown — X Tage bis Abflug mit Zahl-Fokus."""
    return f"""<div class="template-wrapper treff-countdown" style="width:1080px;height:1080px;position:relative;overflow:hidden;">
  <div class="template-bg" style="position:absolute;inset:0;background:linear-gradient(135deg, {TREFF_DARK} 0%, #0D1B3E 50%, {TREFF_BLUE} 100%);"></div>
  <div class="template-content" style="position:relative;z-index:1;display:flex;flex-direction:column;height:100%;padding:60px;">
    <div class="template-header" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:40px;">
      <div class="template-logo" style="width:120px;height:40px;background:{TREFF_BLUE};border-radius:8px;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:14px;letter-spacing:1px;">TREFF</div>
      <div class="flight-icon" style="font-size:32px;">&#9992;</div>
    </div>
    <div class="template-body" style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:16px;">
      <div class="countdown-label" style="font-size:20px;font-weight:600;color:{TREFF_YELLOW};text-transform:uppercase;letter-spacing:3px;">{{{{headline}}}}</div>
      <div class="countdown-number" style="font-size:180px;font-weight:900;color:#FFFFFF;line-height:1;text-shadow:0 4px 20px rgba(59,122,177,0.5);">{{{{countdown_number}}}}</div>
      <div class="countdown-unit" style="font-size:36px;font-weight:700;color:rgba(255,255,255,0.7);text-transform:uppercase;letter-spacing:4px;">TAGE</div>
      <div class="divider" style="width:80px;height:4px;background:{TREFF_YELLOW};border-radius:2px;margin:16px 0;"></div>
      <p class="subtext" style="font-size:22px;color:rgba(255,255,255,0.8);line-height:1.4;max-width:700px;">{{{{subheadline}}}}</p>
    </div>
    <div class="template-footer" style="display:flex;justify-content:space-between;align-items:center;margin-top:auto;">
      <span class="template-cta" style="background:{TREFF_YELLOW};color:{TREFF_DARK};padding:14px 28px;border-radius:10px;font-weight:700;font-size:16px;">{{{{cta_text}}}}</span>
      <span style="color:#9CA3AF;font-size:14px;">@treff_sprachreisen</span>
    </div>
  </div>
</div>"""


def _css_countdown() -> str:
    return """.template-wrapper.treff-countdown {
  font-family: 'Montserrat', 'Inter', sans-serif;
  box-sizing: border-box;
}
.template-wrapper.treff-countdown * { box-sizing: border-box; }
.countdown-number {
  background: linear-gradient(180deg, #FFFFFF 0%, rgba(255,255,255,0.7) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.template-cta { text-transform: uppercase; letter-spacing: 0.5px; }
"""


def _html_land_factsheet() -> str:
    """Land-Factsheet — 5-6 Fakten ueber ein Land im Card-Design."""
    return f"""<div class="template-wrapper treff-factsheet" style="width:1080px;height:1350px;position:relative;overflow:hidden;">
  <div class="template-bg" style="position:absolute;inset:0;background:linear-gradient(180deg, {TREFF_BLUE} 0%, {TREFF_DARK} 40%);"></div>
  <div class="template-content" style="position:relative;z-index:1;display:flex;flex-direction:column;height:100%;padding:50px;">
    <div class="template-header" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:30px;">
      <div class="template-logo" style="width:100px;height:34px;background:rgba(255,255,255,0.15);border-radius:6px;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:12px;">TREFF</div>
      <div class="country-flag" style="font-size:36px;">{{{{country_flag}}}}</div>
    </div>
    <h1 class="template-headline" style="font-size:44px;font-weight:800;color:#FFFFFF;line-height:1.1;margin-bottom:8px;">{{{{headline}}}}</h1>
    <p class="template-subtitle" style="font-size:18px;color:{TREFF_YELLOW};font-weight:600;margin-bottom:30px;letter-spacing:1px;text-transform:uppercase;">{{{{subheadline}}}}</p>
    <div class="facts-grid" style="flex:1;display:flex;flex-direction:column;gap:14px;">
      <div class="fact-card" style="background:rgba(255,255,255,0.06);border-radius:16px;padding:22px 26px;display:flex;align-items:center;gap:18px;border:1px solid rgba(255,255,255,0.08);">
        <div class="fact-icon" style="width:48px;height:48px;border-radius:12px;background:{TREFF_BLUE};display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0;">&#127891;</div>
        <div><div style="color:#fff;font-weight:700;font-size:17px;">{{{{fact_1_title}}}}</div><div style="color:rgba(255,255,255,0.65);font-size:14px;margin-top:2px;">{{{{fact_1_text}}}}</div></div>
      </div>
      <div class="fact-card" style="background:rgba(255,255,255,0.06);border-radius:16px;padding:22px 26px;display:flex;align-items:center;gap:18px;border:1px solid rgba(255,255,255,0.08);">
        <div class="fact-icon" style="width:48px;height:48px;border-radius:12px;background:{TREFF_YELLOW};display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0;color:{TREFF_DARK};">&#127758;</div>
        <div><div style="color:#fff;font-weight:700;font-size:17px;">{{{{fact_2_title}}}}</div><div style="color:rgba(255,255,255,0.65);font-size:14px;margin-top:2px;">{{{{fact_2_text}}}}</div></div>
      </div>
      <div class="fact-card" style="background:rgba(255,255,255,0.06);border-radius:16px;padding:22px 26px;display:flex;align-items:center;gap:18px;border:1px solid rgba(255,255,255,0.08);">
        <div class="fact-icon" style="width:48px;height:48px;border-radius:12px;background:{TREFF_BLUE};display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0;">&#128176;</div>
        <div><div style="color:#fff;font-weight:700;font-size:17px;">{{{{fact_3_title}}}}</div><div style="color:rgba(255,255,255,0.65);font-size:14px;margin-top:2px;">{{{{fact_3_text}}}}</div></div>
      </div>
      <div class="fact-card" style="background:rgba(255,255,255,0.06);border-radius:16px;padding:22px 26px;display:flex;align-items:center;gap:18px;border:1px solid rgba(255,255,255,0.08);">
        <div class="fact-icon" style="width:48px;height:48px;border-radius:12px;background:{TREFF_YELLOW};display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0;color:{TREFF_DARK};">&#127968;</div>
        <div><div style="color:#fff;font-weight:700;font-size:17px;">{{{{fact_4_title}}}}</div><div style="color:rgba(255,255,255,0.65);font-size:14px;margin-top:2px;">{{{{fact_4_text}}}}</div></div>
      </div>
      <div class="fact-card" style="background:rgba(255,255,255,0.06);border-radius:16px;padding:22px 26px;display:flex;align-items:center;gap:18px;border:1px solid rgba(255,255,255,0.08);">
        <div class="fact-icon" style="width:48px;height:48px;border-radius:12px;background:{TREFF_BLUE};display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0;">&#9996;</div>
        <div><div style="color:#fff;font-weight:700;font-size:17px;">{{{{fact_5_title}}}}</div><div style="color:rgba(255,255,255,0.65);font-size:14px;margin-top:2px;">{{{{fact_5_text}}}}</div></div>
      </div>
    </div>
    <div class="template-footer" style="display:flex;justify-content:space-between;align-items:center;margin-top:24px;">
      <span class="template-cta" style="background:{TREFF_YELLOW};color:{TREFF_DARK};padding:14px 28px;border-radius:10px;font-weight:700;font-size:16px;">{{{{cta_text}}}}</span>
      <span style="color:#9CA3AF;font-size:14px;">@treff_sprachreisen</span>
    </div>
  </div>
</div>"""


def _css_land_factsheet() -> str:
    return """.template-wrapper.treff-factsheet {
  font-family: 'Montserrat', 'Inter', sans-serif;
  box-sizing: border-box;
}
.template-wrapper.treff-factsheet * { box-sizing: border-box; }
.fact-card { transition: transform 0.2s; }
.fact-card:hover { transform: translateX(4px); }
.template-headline { text-shadow: 0 2px 8px rgba(0,0,0,0.3); }
.template-cta { text-transform: uppercase; letter-spacing: 0.5px; }
"""


def _html_motivations_quote() -> str:
    """Motivations-Quote — Inspirierender Spruch auf Hintergrundbild."""
    return f"""<div class="template-wrapper treff-quote" style="width:1080px;height:1080px;position:relative;overflow:hidden;">
  <div class="template-bg" style="position:absolute;inset:0;background:linear-gradient(135deg, #0D1B3E 0%, {TREFF_DARK} 50%, #1E2A4A 100%);"></div>
  <div class="bg-pattern" style="position:absolute;inset:0;background:radial-gradient(circle at 20% 80%, rgba(59,122,177,0.15) 0%, transparent 50%),radial-gradient(circle at 80% 20%, rgba(253,208,0,0.1) 0%, transparent 50%);"></div>
  <div class="template-content" style="position:relative;z-index:1;display:flex;flex-direction:column;height:100%;padding:60px;">
    <div class="template-header" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:auto;">
      <div class="template-logo" style="width:100px;height:34px;background:{TREFF_BLUE};border-radius:6px;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:12px;">TREFF</div>
    </div>
    <div class="template-body" style="display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:24px;padding:40px 20px;">
      <div class="quote-decoration-top" style="width:60px;height:4px;background:{TREFF_YELLOW};border-radius:2px;"></div>
      <div class="quote-mark" style="font-size:56px;color:{TREFF_YELLOW};line-height:1;">&ldquo;</div>
      <p class="quote-text" style="font-size:36px;font-weight:700;color:#FFFFFF;line-height:1.35;max-width:850px;font-style:italic;">{{{{quote_text}}}}</p>
      <div class="quote-mark-end" style="font-size:56px;color:{TREFF_YELLOW};line-height:1;">&rdquo;</div>
      <div class="quote-decoration-bottom" style="width:60px;height:4px;background:{TREFF_YELLOW};border-radius:2px;"></div>
    </div>
    <div class="template-footer" style="display:flex;justify-content:center;align-items:center;margin-top:auto;">
      <span style="color:#9CA3AF;font-size:14px;">@treff_sprachreisen</span>
    </div>
  </div>
</div>"""


def _css_motivations_quote() -> str:
    return """.template-wrapper.treff-quote {
  font-family: 'Montserrat', 'Inter', sans-serif;
  box-sizing: border-box;
}
.template-wrapper.treff-quote * { box-sizing: border-box; }
.quote-text { text-shadow: 0 2px 12px rgba(0,0,0,0.4); }
.quote-mark, .quote-mark-end { text-shadow: 0 2px 8px rgba(253,208,0,0.3); }
"""


def _html_vorher_nachher() -> str:
    """Vorher/Nachher — Split-Screen Vergleich."""
    return f"""<div class="template-wrapper treff-vergleich" style="width:1080px;height:1080px;position:relative;overflow:hidden;">
  <div class="template-bg" style="position:absolute;inset:0;background:{TREFF_DARK};"></div>
  <div class="template-content" style="position:relative;z-index:1;display:flex;flex-direction:column;height:100%;">
    <div class="template-header" style="display:flex;justify-content:space-between;align-items:center;padding:30px 40px;">
      <div class="template-logo" style="width:100px;height:34px;background:{TREFF_BLUE};border-radius:6px;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:12px;">TREFF</div>
      <h1 class="template-headline" style="font-size:28px;font-weight:800;color:#FFFFFF;">{{{{headline}}}}</h1>
    </div>
    <div class="split-container" style="flex:1;display:flex;gap:4px;padding:0 40px;">
      <div class="split-left" style="flex:1;background:rgba(255,255,255,0.04);border-radius:20px;display:flex;flex-direction:column;overflow:hidden;">
        <div class="split-label" style="background:{TREFF_BLUE};padding:14px 24px;text-align:center;">
          <span style="color:#fff;font-weight:800;font-size:18px;text-transform:uppercase;letter-spacing:2px;">{{{{label_before}}}}</span>
        </div>
        <div class="split-content" style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:30px;text-align:center;gap:16px;">
          <div style="font-size:48px;">{{{{icon_before}}}}</div>
          <p style="font-size:20px;color:rgba(255,255,255,0.85);line-height:1.5;">{{{{text_before}}}}</p>
        </div>
      </div>
      <div class="split-divider" style="display:flex;align-items:center;justify-content:center;width:60px;">
        <div style="background:{TREFF_YELLOW};width:44px;height:44px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:20px;font-weight:800;color:{TREFF_DARK};">VS</div>
      </div>
      <div class="split-right" style="flex:1;background:rgba(255,255,255,0.04);border-radius:20px;display:flex;flex-direction:column;overflow:hidden;">
        <div class="split-label" style="background:{TREFF_YELLOW};padding:14px 24px;text-align:center;">
          <span style="color:{TREFF_DARK};font-weight:800;font-size:18px;text-transform:uppercase;letter-spacing:2px;">{{{{label_after}}}}</span>
        </div>
        <div class="split-content" style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:30px;text-align:center;gap:16px;">
          <div style="font-size:48px;">{{{{icon_after}}}}</div>
          <p style="font-size:20px;color:rgba(255,255,255,0.85);line-height:1.5;">{{{{text_after}}}}</p>
        </div>
      </div>
    </div>
    <div class="template-footer" style="display:flex;justify-content:space-between;align-items:center;padding:24px 40px;">
      <span class="template-cta" style="background:{TREFF_YELLOW};color:{TREFF_DARK};padding:12px 24px;border-radius:10px;font-weight:700;font-size:15px;">{{{{cta_text}}}}</span>
      <span style="color:#9CA3AF;font-size:14px;">@treff_sprachreisen</span>
    </div>
  </div>
</div>"""


def _css_vorher_nachher() -> str:
    return """.template-wrapper.treff-vergleich {
  font-family: 'Montserrat', 'Inter', sans-serif;
  box-sizing: border-box;
}
.template-wrapper.treff-vergleich * { box-sizing: border-box; }
.split-left, .split-right { border: 1px solid rgba(255,255,255,0.06); }
.template-cta { text-transform: uppercase; letter-spacing: 0.5px; }
"""


def _html_event_ankuendigung() -> str:
    """Event-Ankuendigung — Datum, Ort, CTA fuer Infoveranstaltungen."""
    return f"""<div class="template-wrapper treff-event" style="width:1080px;height:1080px;position:relative;overflow:hidden;">
  <div class="template-bg" style="position:absolute;inset:0;background:linear-gradient(135deg, {TREFF_DARK} 0%, #162240 100%);"></div>
  <div class="accent-bar" style="position:absolute;top:0;left:0;right:0;height:8px;background:linear-gradient(90deg, {TREFF_BLUE}, {TREFF_YELLOW});"></div>
  <div class="template-content" style="position:relative;z-index:1;display:flex;flex-direction:column;height:100%;padding:60px;">
    <div class="template-header" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:30px;">
      <div class="template-logo" style="width:120px;height:40px;background:{TREFF_BLUE};border-radius:8px;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:14px;">TREFF</div>
      <div class="event-badge" style="background:{TREFF_YELLOW};color:{TREFF_DARK};padding:8px 20px;border-radius:20px;font-weight:800;font-size:14px;text-transform:uppercase;letter-spacing:1px;">EVENT</div>
    </div>
    <div class="template-body" style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:28px;">
      <h1 class="template-headline" style="font-size:48px;font-weight:800;color:#FFFFFF;line-height:1.1;">{{{{headline}}}}</h1>
      <p class="template-description" style="font-size:20px;color:rgba(255,255,255,0.8);line-height:1.5;">{{{{body_text}}}}</p>
      <div class="event-details" style="display:flex;flex-direction:column;gap:16px;background:rgba(255,255,255,0.05);border-radius:16px;padding:28px;border-left:4px solid {TREFF_YELLOW};">
        <div class="detail-row" style="display:flex;align-items:center;gap:16px;">
          <div style="width:40px;height:40px;border-radius:10px;background:{TREFF_BLUE};display:flex;align-items:center;justify-content:center;font-size:20px;">&#128197;</div>
          <div><div style="color:rgba(255,255,255,0.5);font-size:12px;text-transform:uppercase;letter-spacing:1px;">Datum</div><div style="color:#fff;font-weight:700;font-size:20px;">{{{{event_date}}}}</div></div>
        </div>
        <div class="detail-row" style="display:flex;align-items:center;gap:16px;">
          <div style="width:40px;height:40px;border-radius:10px;background:{TREFF_BLUE};display:flex;align-items:center;justify-content:center;font-size:20px;">&#128205;</div>
          <div><div style="color:rgba(255,255,255,0.5);font-size:12px;text-transform:uppercase;letter-spacing:1px;">Ort</div><div style="color:#fff;font-weight:700;font-size:20px;">{{{{event_location}}}}</div></div>
        </div>
        <div class="detail-row" style="display:flex;align-items:center;gap:16px;">
          <div style="width:40px;height:40px;border-radius:10px;background:{TREFF_BLUE};display:flex;align-items:center;justify-content:center;font-size:20px;">&#128336;</div>
          <div><div style="color:rgba(255,255,255,0.5);font-size:12px;text-transform:uppercase;letter-spacing:1px;">Uhrzeit</div><div style="color:#fff;font-weight:700;font-size:20px;">{{{{event_time}}}}</div></div>
        </div>
      </div>
    </div>
    <div class="template-footer" style="display:flex;justify-content:space-between;align-items:center;margin-top:auto;padding-top:20px;">
      <span class="template-cta" style="background:{TREFF_YELLOW};color:{TREFF_DARK};padding:16px 32px;border-radius:10px;font-weight:800;font-size:18px;">{{{{cta_text}}}}</span>
      <span style="color:#9CA3AF;font-size:14px;">@treff_sprachreisen</span>
    </div>
  </div>
</div>"""


def _css_event_ankuendigung() -> str:
    return """.template-wrapper.treff-event {
  font-family: 'Montserrat', 'Inter', sans-serif;
  box-sizing: border-box;
}
.template-wrapper.treff-event * { box-sizing: border-box; }
.template-headline { text-shadow: 0 2px 8px rgba(0,0,0,0.3); }
.event-details { backdrop-filter: blur(4px); }
.template-cta { text-transform: uppercase; letter-spacing: 0.5px; box-shadow: 0 4px 16px rgba(253,208,0,0.3); }
"""


def _html_tipp_der_woche() -> str:
    """Tipp der Woche — Nummerierte Tipps mit Icon."""
    return f"""<div class="template-wrapper treff-tipp" style="width:1080px;height:1350px;position:relative;overflow:hidden;">
  <div class="template-bg" style="position:absolute;inset:0;background:linear-gradient(180deg, {TREFF_DARK} 0%, #0F1A30 100%);"></div>
  <div class="template-content" style="position:relative;z-index:1;display:flex;flex-direction:column;height:100%;padding:50px;">
    <div class="template-header" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:24px;">
      <div class="template-logo" style="width:100px;height:34px;background:{TREFF_BLUE};border-radius:6px;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:12px;">TREFF</div>
      <div class="tipp-badge" style="background:{TREFF_YELLOW};color:{TREFF_DARK};padding:8px 18px;border-radius:20px;font-weight:800;font-size:13px;text-transform:uppercase;letter-spacing:1px;">&#128161; Tipp</div>
    </div>
    <h1 class="template-headline" style="font-size:40px;font-weight:800;color:#FFFFFF;line-height:1.1;margin-bottom:8px;">{{{{headline}}}}</h1>
    <p class="template-subtitle" style="font-size:18px;color:{TREFF_YELLOW};font-weight:600;margin-bottom:28px;">{{{{subheadline}}}}</p>
    <div class="tips-list" style="flex:1;display:flex;flex-direction:column;gap:16px;">
      <div class="tip-item" style="display:flex;align-items:flex-start;gap:18px;background:rgba(255,255,255,0.04);border-radius:14px;padding:20px 22px;border:1px solid rgba(255,255,255,0.06);">
        <div class="tip-number" style="width:42px;height:42px;border-radius:50%;background:{TREFF_BLUE};display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;font-size:18px;flex-shrink:0;">1</div>
        <div><div style="color:#fff;font-weight:700;font-size:17px;margin-bottom:4px;">{{{{tip_1_title}}}}</div><div style="color:rgba(255,255,255,0.65);font-size:14px;line-height:1.4;">{{{{tip_1_text}}}}</div></div>
      </div>
      <div class="tip-item" style="display:flex;align-items:flex-start;gap:18px;background:rgba(255,255,255,0.04);border-radius:14px;padding:20px 22px;border:1px solid rgba(255,255,255,0.06);">
        <div class="tip-number" style="width:42px;height:42px;border-radius:50%;background:{TREFF_BLUE};display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;font-size:18px;flex-shrink:0;">2</div>
        <div><div style="color:#fff;font-weight:700;font-size:17px;margin-bottom:4px;">{{{{tip_2_title}}}}</div><div style="color:rgba(255,255,255,0.65);font-size:14px;line-height:1.4;">{{{{tip_2_text}}}}</div></div>
      </div>
      <div class="tip-item" style="display:flex;align-items:flex-start;gap:18px;background:rgba(255,255,255,0.04);border-radius:14px;padding:20px 22px;border:1px solid rgba(255,255,255,0.06);">
        <div class="tip-number" style="width:42px;height:42px;border-radius:50%;background:{TREFF_BLUE};display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;font-size:18px;flex-shrink:0;">3</div>
        <div><div style="color:#fff;font-weight:700;font-size:17px;margin-bottom:4px;">{{{{tip_3_title}}}}</div><div style="color:rgba(255,255,255,0.65);font-size:14px;line-height:1.4;">{{{{tip_3_text}}}}</div></div>
      </div>
      <div class="tip-item" style="display:flex;align-items:flex-start;gap:18px;background:rgba(255,255,255,0.04);border-radius:14px;padding:20px 22px;border:1px solid rgba(255,255,255,0.06);">
        <div class="tip-number" style="width:42px;height:42px;border-radius:50%;background:{TREFF_YELLOW};display:flex;align-items:center;justify-content:center;color:{TREFF_DARK};font-weight:800;font-size:18px;flex-shrink:0;">4</div>
        <div><div style="color:#fff;font-weight:700;font-size:17px;margin-bottom:4px;">{{{{tip_4_title}}}}</div><div style="color:rgba(255,255,255,0.65);font-size:14px;line-height:1.4;">{{{{tip_4_text}}}}</div></div>
      </div>
    </div>
    <div class="template-footer" style="display:flex;justify-content:space-between;align-items:center;margin-top:24px;">
      <span class="template-cta" style="background:{TREFF_YELLOW};color:{TREFF_DARK};padding:14px 28px;border-radius:10px;font-weight:700;font-size:16px;">{{{{cta_text}}}}</span>
      <span style="color:#9CA3AF;font-size:14px;">@treff_sprachreisen</span>
    </div>
  </div>
</div>"""


def _css_tipp_der_woche() -> str:
    return """.template-wrapper.treff-tipp {
  font-family: 'Montserrat', 'Inter', sans-serif;
  box-sizing: border-box;
}
.template-wrapper.treff-tipp * { box-sizing: border-box; }
.template-headline { text-shadow: 0 2px 4px rgba(0,0,0,0.3); }
.tip-item { transition: transform 0.2s; }
.tip-item:hover { transform: translateX(4px); }
.template-cta { text-transform: uppercase; letter-spacing: 0.5px; }
"""


def _html_story_umfrage() -> str:
    """Story-Umfrage — Story-Format mit Frage und 2 Optionen."""
    return f"""<div class="template-wrapper treff-umfrage" style="width:1080px;height:1920px;position:relative;overflow:hidden;">
  <div class="template-bg" style="position:absolute;inset:0;background:linear-gradient(180deg, {TREFF_DARK} 0%, #0F1A30 50%, {TREFF_BLUE}33 100%);"></div>
  <div class="template-content" style="position:relative;z-index:1;display:flex;flex-direction:column;height:100%;padding:60px 50px;">
    <div class="template-header" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:40px;">
      <div class="template-logo" style="width:100px;height:34px;background:{TREFF_BLUE};border-radius:6px;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:12px;">TREFF</div>
      <div class="poll-badge" style="background:linear-gradient(135deg, {TREFF_BLUE}, {TREFF_YELLOW});padding:8px 18px;border-radius:16px;color:#fff;font-weight:800;font-size:13px;letter-spacing:1px;">UMFRAGE</div>
    </div>
    <div class="template-body" style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:40px;">
      <div class="question-icon" style="font-size:72px;">&#129300;</div>
      <h1 class="template-headline" style="font-size:48px;font-weight:800;color:#FFFFFF;line-height:1.15;max-width:900px;">{{{{headline}}}}</h1>
      <div class="options-container" style="width:100%;max-width:800px;display:flex;flex-direction:column;gap:20px;margin-top:20px;">
        <div class="option-a" style="background:rgba(59,122,177,0.2);border:3px solid {TREFF_BLUE};border-radius:20px;padding:28px 36px;display:flex;align-items:center;gap:20px;cursor:pointer;">
          <div class="option-letter" style="width:52px;height:52px;border-radius:50%;background:{TREFF_BLUE};display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;font-size:22px;flex-shrink:0;">A</div>
          <span style="font-size:24px;font-weight:700;color:#FFFFFF;">{{{{option_a}}}}</span>
        </div>
        <div class="option-b" style="background:rgba(253,208,0,0.1);border:3px solid {TREFF_YELLOW};border-radius:20px;padding:28px 36px;display:flex;align-items:center;gap:20px;cursor:pointer;">
          <div class="option-letter" style="width:52px;height:52px;border-radius:50%;background:{TREFF_YELLOW};display:flex;align-items:center;justify-content:center;color:{TREFF_DARK};font-weight:800;font-size:22px;flex-shrink:0;">B</div>
          <span style="font-size:24px;font-weight:700;color:#FFFFFF;">{{{{option_b}}}}</span>
        </div>
      </div>
      <p class="poll-hint" style="font-size:18px;color:rgba(255,255,255,0.5);margin-top:12px;">Tippe auf deine Antwort! &#128071;</p>
    </div>
    <div class="template-footer" style="text-align:center;margin-top:auto;padding-top:30px;">
      <span style="color:rgba(255,255,255,0.3);font-size:12px;">@treff_sprachreisen</span>
    </div>
  </div>
</div>"""


def _css_story_umfrage() -> str:
    return """.template-wrapper.treff-umfrage {
  font-family: 'Montserrat', 'Inter', sans-serif;
  box-sizing: border-box;
}
.template-wrapper.treff-umfrage * { box-sizing: border-box; }
.template-headline { text-shadow: 0 2px 8px rgba(0,0,0,0.4); }
.option-a:hover { background: rgba(59,122,177,0.35); }
.option-b:hover { background: rgba(253,208,0,0.2); }
"""


def _html_bewerbungs_cta() -> str:
    """Bewerbungs-CTA — Jetzt bewerben mit Deadline."""
    return f"""<div class="template-wrapper treff-bewerbung" style="width:1080px;height:1080px;position:relative;overflow:hidden;">
  <div class="template-bg" style="position:absolute;inset:0;background:linear-gradient(135deg, {TREFF_BLUE} 0%, {TREFF_DARK} 60%, #0A0A1A 100%);"></div>
  <div class="urgency-bar" style="position:absolute;top:0;left:0;right:0;height:6px;background:{TREFF_YELLOW};"></div>
  <div class="template-content" style="position:relative;z-index:1;display:flex;flex-direction:column;height:100%;padding:60px;">
    <div class="template-header" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:40px;">
      <div class="template-logo" style="width:120px;height:40px;background:rgba(255,255,255,0.1);border-radius:8px;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:14px;">TREFF</div>
      <div class="deadline-badge" style="background:rgba(253,208,0,0.15);border:2px solid {TREFF_YELLOW};padding:8px 20px;border-radius:20px;color:{TREFF_YELLOW};font-weight:800;font-size:14px;">&#9200; {{{{deadline}}}}</div>
    </div>
    <div class="template-body" style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:24px;">
      <div class="program-label" style="font-size:16px;font-weight:600;color:{TREFF_YELLOW};text-transform:uppercase;letter-spacing:3px;">{{{{subheadline}}}}</div>
      <h1 class="template-headline" style="font-size:52px;font-weight:900;color:#FFFFFF;line-height:1.1;">{{{{headline}}}}</h1>
      <p class="template-description" style="font-size:22px;color:rgba(255,255,255,0.8);line-height:1.5;max-width:800px;">{{{{body_text}}}}</p>
      <div class="cta-section" style="margin-top:20px;display:flex;flex-direction:column;align-items:center;gap:12px;">
        <span class="template-cta" style="display:inline-block;background:{TREFF_YELLOW};color:{TREFF_DARK};padding:18px 48px;border-radius:14px;font-weight:800;font-size:22px;">{{{{cta_text}}}}</span>
        <span class="cta-sub" style="color:rgba(255,255,255,0.5);font-size:14px;">{{{{cta_subtext}}}}</span>
      </div>
    </div>
    <div class="template-footer" style="display:flex;justify-content:center;align-items:center;margin-top:auto;">
      <span style="color:#9CA3AF;font-size:14px;">@treff_sprachreisen &middot; treff-sprachreisen.de</span>
    </div>
  </div>
</div>"""


def _css_bewerbungs_cta() -> str:
    return """.template-wrapper.treff-bewerbung {
  font-family: 'Montserrat', 'Inter', sans-serif;
  box-sizing: border-box;
}
.template-wrapper.treff-bewerbung * { box-sizing: border-box; }
.template-headline { text-shadow: 0 4px 16px rgba(0,0,0,0.4); }
.template-cta {
  text-transform: uppercase;
  letter-spacing: 1px;
  box-shadow: 0 6px 24px rgba(253,208,0,0.4);
  animation: pulse-cta 2s infinite;
}
@keyframes pulse-cta {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.03); }
}
.deadline-badge { animation: blink-border 2s infinite; }
@keyframes blink-border {
  0%, 100% { border-color: #FDD000; }
  50% { border-color: rgba(253,208,0,0.4); }
}
"""


def _html_carousel_slide() -> str:
    """Carousel-Slide — Einheitliches Design fuer Carousel-Posts."""
    return f"""<div class="template-wrapper treff-carousel" style="width:1080px;height:1080px;position:relative;overflow:hidden;">
  <div class="template-bg" style="position:absolute;inset:0;background:linear-gradient(180deg, {TREFF_DARK} 0%, #151D30 100%);"></div>
  <div class="slide-indicator" style="position:absolute;top:30px;right:40px;background:rgba(255,255,255,0.1);padding:6px 14px;border-radius:12px;color:rgba(255,255,255,0.6);font-size:14px;font-weight:600;">{{{{slide_number}}}} / {{{{total_slides}}}}</div>
  <div class="template-content" style="position:relative;z-index:1;display:flex;flex-direction:column;height:100%;padding:60px;">
    <div class="template-header" style="display:flex;align-items:center;gap:12px;margin-bottom:auto;">
      <div class="template-logo" style="width:100px;height:34px;background:{TREFF_BLUE};border-radius:6px;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:12px;">TREFF</div>
      <div class="series-label" style="color:{TREFF_YELLOW};font-size:14px;font-weight:600;letter-spacing:1px;">{{{{series_label}}}}</div>
    </div>
    <div class="template-body" style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:24px;">
      <h1 class="template-headline" style="font-size:44px;font-weight:800;color:#FFFFFF;line-height:1.1;">{{{{headline}}}}</h1>
      <div class="content-divider" style="width:60px;height:4px;background:{TREFF_YELLOW};border-radius:2px;"></div>
      <p class="template-body-text" style="font-size:22px;color:rgba(255,255,255,0.85);line-height:1.6;">{{{{body_text}}}}</p>
    </div>
    <div class="template-footer" style="display:flex;justify-content:space-between;align-items:center;margin-top:auto;">
      <div class="swipe-hint" style="display:flex;align-items:center;gap:8px;color:rgba(255,255,255,0.4);font-size:14px;">
        Wische weiter <span style="font-size:18px;">&#10145;</span>
      </div>
      <span style="color:#9CA3AF;font-size:14px;">@treff_sprachreisen</span>
    </div>
  </div>
</div>"""


def _css_carousel_slide() -> str:
    return """.template-wrapper.treff-carousel {
  font-family: 'Montserrat', 'Inter', sans-serif;
  box-sizing: border-box;
}
.template-wrapper.treff-carousel * { box-sizing: border-box; }
.template-headline { text-shadow: 0 2px 8px rgba(0,0,0,0.3); }
.content-divider { transition: width 0.3s; }
"""


# ==============================================================================
# Template definitions list
# ==============================================================================

TREFF_STANDARD_TEMPLATES = [
    {
        "name": "TREFF Standard: Erfahrungsbericht",
        "category": "erfahrungsberichte",
        "platform_format": "feed_portrait",
        "slide_count": 1,
        "placeholder_fields": json.dumps([
            "image", "quote_text", "quote_author", "quote_author_initial", "country_label"
        ]),
        "is_default": True,
        "is_country_themed": False,
        "_html_fn": _html_erfahrungsbericht,
        "_css_fn": _css_erfahrungsbericht,
    },
    {
        "name": "TREFF Standard: Countdown",
        "category": "fristen_cta",
        "platform_format": "feed_portrait",
        "slide_count": 1,
        "placeholder_fields": json.dumps([
            "headline", "countdown_number", "subheadline", "cta_text"
        ]),
        "is_default": True,
        "is_country_themed": False,
        "_html_fn": _html_countdown,
        "_css_fn": _css_countdown,
    },
    {
        "name": "TREFF Standard: Land-Factsheet",
        "category": "laender_spotlight",
        "platform_format": "feed_portrait",
        "slide_count": 1,
        "placeholder_fields": json.dumps([
            "headline", "subheadline", "country_flag",
            "fact_1_title", "fact_1_text",
            "fact_2_title", "fact_2_text",
            "fact_3_title", "fact_3_text",
            "fact_4_title", "fact_4_text",
            "fact_5_title", "fact_5_text",
            "cta_text"
        ]),
        "is_default": True,
        "is_country_themed": True,
        "_html_fn": _html_land_factsheet,
        "_css_fn": _css_land_factsheet,
    },
    {
        "name": "TREFF Standard: Motivations-Quote",
        "category": "foto_posts",
        "platform_format": "feed_portrait",
        "slide_count": 1,
        "placeholder_fields": json.dumps(["quote_text"]),
        "is_default": True,
        "is_country_themed": False,
        "_html_fn": _html_motivations_quote,
        "_css_fn": _css_motivations_quote,
    },
    {
        "name": "TREFF Standard: Vorher/Nachher",
        "category": "infografiken",
        "platform_format": "feed_portrait",
        "slide_count": 1,
        "placeholder_fields": json.dumps([
            "headline", "label_before", "icon_before", "text_before",
            "label_after", "icon_after", "text_after", "cta_text"
        ]),
        "is_default": True,
        "is_country_themed": False,
        "_html_fn": _html_vorher_nachher,
        "_css_fn": _css_vorher_nachher,
    },
    {
        "name": "TREFF Standard: Event-Ankuendigung",
        "category": "fristen_cta",
        "platform_format": "feed_portrait",
        "slide_count": 1,
        "placeholder_fields": json.dumps([
            "headline", "body_text", "event_date", "event_location",
            "event_time", "cta_text"
        ]),
        "is_default": True,
        "is_country_themed": False,
        "_html_fn": _html_event_ankuendigung,
        "_css_fn": _css_event_ankuendigung,
    },
    {
        "name": "TREFF Standard: Tipp der Woche",
        "category": "tipps_tricks",
        "platform_format": "feed_portrait",
        "slide_count": 1,
        "placeholder_fields": json.dumps([
            "headline", "subheadline",
            "tip_1_title", "tip_1_text",
            "tip_2_title", "tip_2_text",
            "tip_3_title", "tip_3_text",
            "tip_4_title", "tip_4_text",
            "cta_text"
        ]),
        "is_default": True,
        "is_country_themed": False,
        "_html_fn": _html_tipp_der_woche,
        "_css_fn": _css_tipp_der_woche,
    },
    {
        "name": "TREFF Standard: Story-Umfrage",
        "category": "story_posts",
        "platform_format": "story",
        "slide_count": 1,
        "placeholder_fields": json.dumps([
            "headline", "option_a", "option_b"
        ]),
        "is_default": True,
        "is_country_themed": False,
        "_html_fn": _html_story_umfrage,
        "_css_fn": _css_story_umfrage,
    },
    {
        "name": "TREFF Standard: Bewerbungs-CTA",
        "category": "fristen_cta",
        "platform_format": "feed_portrait",
        "slide_count": 1,
        "placeholder_fields": json.dumps([
            "headline", "subheadline", "body_text", "deadline",
            "cta_text", "cta_subtext"
        ]),
        "is_default": True,
        "is_country_themed": False,
        "_html_fn": _html_bewerbungs_cta,
        "_css_fn": _css_bewerbungs_cta,
    },
    {
        "name": "TREFF Standard: Carousel-Slide",
        "category": "infografiken",
        "platform_format": "feed_portrait",
        "slide_count": 5,
        "placeholder_fields": json.dumps([
            "headline", "body_text", "slide_number", "total_slides",
            "series_label"
        ]),
        "is_default": True,
        "is_country_themed": False,
        "_html_fn": _html_carousel_slide,
        "_css_fn": _css_carousel_slide,
    },
]


async def seed_treff_standard_templates(db: AsyncSession) -> int:
    """Seed TREFF Standard-Templates if they don't exist yet.

    Creates 10 production-ready templates covering the most common post types.
    Each template has unique, specialized HTML/CSS with TREFF brand styling.

    Returns:
        Number of templates created (0 if already seeded).
    """
    # Check if TREFF standard templates already exist
    result = await db.execute(
        select(func.count()).select_from(Template).where(
            Template.is_default == True,
            Template.name.like("TREFF Standard:%"),
        )
    )
    existing_count = result.scalar()

    if existing_count > 0:
        logger.info("Found %d TREFF standard templates, skipping seed.", existing_count)
        return 0

    logger.info("No TREFF standard templates found. Seeding 10 templates...")
    created = 0

    for tpl_data in TREFF_STANDARD_TEMPLATES:
        html_fn = tpl_data.pop("_html_fn")
        css_fn = tpl_data.pop("_css_fn")

        html_content = html_fn()
        css_content = css_fn()

        template = Template(
            name=tpl_data["name"],
            category=tpl_data["category"],
            platform_format=tpl_data["platform_format"],
            slide_count=tpl_data["slide_count"],
            html_content=html_content,
            css_content=css_content,
            default_colors=DEFAULT_COLORS,
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
    logger.info("Seeded %d TREFF standard templates.", created)
    return created
