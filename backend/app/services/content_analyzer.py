from __future__ import annotations

"""
Content Analyzer Service - AI-powered media analysis for the Smart Content Pipeline.

Analyzes uploaded images/videos using Gemini Vision API to suggest:
- Post type (feed, story, reel/TikTok, carousel)
- Caption seeds (starting points for captions)
- Best platforms for the content
- Detected country (if recognizable landmarks/flags/symbols)
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# Country detection keywords/landmarks
COUNTRY_INDICATORS = {
    "usa": [
        "american flag", "statue of liberty", "golden gate", "new york", "los angeles",
        "usa", "united states", "hollywood", "times square", "grand canyon",
        "yellow school bus", "football", "baseball", "cheerleader", "prom",
        "high school", "homecoming", "stars and stripes", "bald eagle",
    ],
    "kanada": [
        "maple leaf", "canada", "canadian", "toronto", "vancouver", "montreal",
        "niagara falls", "rocky mountains", "cn tower", "hockey", "mountie",
        "moose", "beaver", "tim hortons",
    ],
    "australien": [
        "australia", "australian", "sydney opera house", "harbour bridge",
        "great barrier reef", "outback", "kangaroo", "koala", "surfing",
        "uluru", "ayers rock", "melbourne", "brisbane",
    ],
    "neuseeland": [
        "new zealand", "auckland", "wellington", "queenstown", "milford sound",
        "hobbiton", "maori", "kiwi", "fern", "lord of the rings",
        "sheep", "bungee", "fiordland",
    ],
    "irland": [
        "ireland", "irish", "dublin", "shamrock", "clover", "celtic",
        "cliffs of moher", "galway", "cork", "pub", "guinness",
        "green hills", "castle",
    ],
}

# Post type suggestions based on content characteristics
POST_TYPE_RULES = {
    "portrait_photo": {
        "post_type": "instagram_feed",
        "platforms": ["instagram_feed", "instagram_story"],
        "caption_context": "Portraet eines Schuelers/einer Schuelerin",
    },
    "landscape_scenery": {
        "post_type": "instagram_feed",
        "platforms": ["instagram_feed", "tiktok"],
        "caption_context": "Landschaft oder Sehenswuerdigkeit",
    },
    "group_photo": {
        "post_type": "instagram_feed",
        "platforms": ["instagram_feed", "instagram_story"],
        "caption_context": "Gruppenfoto mit Freunden oder Gastfamilie",
    },
    "school_event": {
        "post_type": "instagram_feed",
        "platforms": ["instagram_feed", "instagram_story", "tiktok"],
        "caption_context": "Schulevent oder Schulaktivitaet",
    },
    "daily_life": {
        "post_type": "instagram_story",
        "platforms": ["instagram_story", "tiktok"],
        "caption_context": "Alltagsszene aus dem Auslandsaufenthalt",
    },
    "food": {
        "post_type": "instagram_story",
        "platforms": ["instagram_story", "instagram_feed"],
        "caption_context": "Typisches Essen aus dem Gastland",
    },
    "video_clip": {
        "post_type": "tiktok",
        "platforms": ["tiktok", "instagram_story"],
        "caption_context": "Kurzes Video aus dem Austauschprogramm",
    },
    "generic": {
        "post_type": "instagram_feed",
        "platforms": ["instagram_feed", "instagram_story", "tiktok"],
        "caption_context": "Allgemeiner Content vom Highschool-Aufenthalt",
    },
}


async def analyze_media_with_ai(
    file_path: str,
    file_type: str,
    source_description: Optional[str] = None,
) -> dict:
    """Analyze an image/video using Gemini Vision API.

    Args:
        file_path: Path to the media file on disk
        file_type: MIME type (e.g. image/jpeg, video/mp4)
        source_description: Optional context from the student/uploader

    Returns:
        dict with keys:
            suggested_post_type: str
            suggested_caption_seeds: list[str]
            suggested_platforms: list[str]
            detected_country: str | None
            analysis_summary: str
    """
    # Try AI analysis first
    if settings.GEMINI_API_KEY:
        try:
            return await _analyze_with_gemini(file_path, file_type, source_description)
        except Exception as e:
            logger.warning(f"Gemini Vision analysis failed, using rule-based fallback: {e}")

    # Fallback to rule-based analysis
    return _analyze_rule_based(file_path, file_type, source_description)


async def _analyze_with_gemini(
    file_path: str,
    file_type: str,
    source_description: Optional[str] = None,
) -> dict:
    """Analyze media using Gemini Vision API (runs sync call in thread pool)."""
    loop = asyncio.get_event_loop()
    result = await asyncio.wait_for(
        loop.run_in_executor(
            None,
            _analyze_with_gemini_sync,
            file_path,
            file_type,
            source_description,
        ),
        timeout=30.0,
    )
    return result


def _analyze_with_gemini_sync(
    file_path: str,
    file_type: str,
    source_description: Optional[str] = None,
) -> dict:
    """Synchronous Gemini Vision API call (runs in thread pool)."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    # Read the file
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Media file not found: {file_path}")

    file_bytes = path.read_bytes()

    context_hint = ""
    if source_description:
        context_hint = f"\nKontext vom Schueler/Uploader: {source_description}"

    prompt = f"""Du bist ein Social-Media-Experte fuer TREFF Sprachreisen, einen deutschen Anbieter von Highschool-Aufenthalten im Ausland (USA, Kanada, Australien, Neuseeland, Irland).

Analysiere dieses Bild/Video und gib eine JSON-Antwort zurueck:
{context_hint}

Antworte NUR mit einem JSON-Objekt (kein Markdown, kein Text drumherum):
{{
  "content_type": "portrait_photo|landscape_scenery|group_photo|school_event|daily_life|food|video_clip|generic",
  "suggested_post_type": "instagram_feed|instagram_story|tiktok|carousel",
  "suggested_caption_seeds": [
    "Drei verschiedene Ideen fuer Instagram/TikTok Captions auf Deutsch, jugendlich aber serioess",
    "Zweite Idee...",
    "Dritte Idee..."
  ],
  "suggested_platforms": ["instagram_feed", "instagram_story", "tiktok"],
  "detected_country": "usa|kanada|australien|neuseeland|irland|null",
  "analysis_summary": "Kurze Beschreibung des Bildinhalts auf Deutsch (1-2 Saetze)"
}}

Beachte:
- Caption Seeds sollen typisch TREFF sein: jugendlich aber serioess, Eltern lesen mit
- Plattform-Vorschlaege basierend auf Bildformat und Inhalt
- Land erkennen anhand von Flaggen, Landmarken, Schuluniformen, Natur etc.
- Falls kein Land erkennbar: detected_country = null"""

    is_image = file_type.startswith("image/")

    if is_image:
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-05-20",
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part(text=prompt),
                        types.Part(
                            inline_data=types.Blob(
                                mime_type=file_type,
                                data=file_bytes,
                            )
                        ),
                    ],
                )
            ],
        )
    else:
        # For video, just use the prompt with description
        video_prompt = prompt.replace("dieses Bild/Video", "dieses Video (basierend auf dem Dateinamen und Kontext)")
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-05-20",
            contents=[types.Content(role="user", parts=[types.Part(text=video_prompt)])],
        )

    # Parse JSON from response
    text = response.text.strip()
    # Remove markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    data = json.loads(text)

    return {
        "suggested_post_type": data.get("suggested_post_type", "instagram_feed"),
        "suggested_caption_seeds": data.get("suggested_caption_seeds", []),
        "suggested_platforms": data.get("suggested_platforms", ["instagram_feed"]),
        "detected_country": data.get("detected_country"),
        "analysis_summary": data.get("analysis_summary", "Medieninhalt analysiert"),
    }


def _analyze_rule_based(
    file_path: str,
    file_type: str,
    source_description: Optional[str] = None,
) -> dict:
    """Rule-based fallback analysis when AI is not available."""
    is_video = file_type.startswith("video/")
    is_image = file_type.startswith("image/")

    # Determine content type from file type
    if is_video:
        content_key = "video_clip"
    elif is_image:
        content_key = "generic"  # Can't determine without AI
    else:
        content_key = "generic"

    rules = POST_TYPE_RULES[content_key]

    # Try to detect country from description
    detected_country = None
    if source_description:
        desc_lower = source_description.lower()
        for country, indicators in COUNTRY_INDICATORS.items():
            for indicator in indicators:
                if indicator in desc_lower:
                    detected_country = country
                    break
            if detected_country:
                break

    # Generate caption seeds based on content type and country
    caption_seeds = _generate_fallback_captions(content_key, detected_country, source_description)

    # Determine summary
    if is_video:
        summary = "Video-Upload erkannt. Geeignet fuer TikTok oder Instagram Story/Reel."
    elif is_image:
        summary = "Bild-Upload erkannt. Geeignet fuer Instagram Feed oder Story."
    else:
        summary = "Medien-Upload erkannt."

    if source_description:
        summary += f" Kontext: {source_description[:100]}"

    return {
        "suggested_post_type": rules["post_type"],
        "suggested_caption_seeds": caption_seeds,
        "suggested_platforms": rules["platforms"],
        "detected_country": detected_country,
        "analysis_summary": summary,
    }


def _generate_fallback_captions(
    content_key: str,
    country: Optional[str] = None,
    description: Optional[str] = None,
) -> list[str]:
    """Generate fallback caption seeds without AI."""
    country_name = {
        "usa": "USA",
        "kanada": "Kanada",
        "australien": "Australien",
        "neuseeland": "Neuseeland",
        "irland": "Irland",
    }.get(country, "Ausland")

    captions = {
        "portrait_photo": [
            f"Unser/e Austauschschueler/in erlebt gerade die beste Zeit in {country_name}!",
            f"So sieht Abenteuer aus: Highschool-Leben in {country_name}",
            f"Ein Laecheln sagt mehr als tausend Worte - Gruss aus {country_name}!",
        ],
        "landscape_scenery": [
            f"Diese Aussicht gibt es nur in {country_name} - atemberaubend!",
            f"Postkartenmotiv? Nein, einfach Alltag fuer unsere Schueler in {country_name}",
            f"Wer wuerde hier nicht gerne zur Schule gehen? {country_name} von seiner schoensten Seite",
        ],
        "group_photo": [
            f"Freundschaften, die ein Leben lang halten - Austauschschueler in {country_name}",
            f"Together is better! Unsere Gruppe in {country_name}",
            f"Diese Erinnerungen bleiben fuer immer - Highschool in {country_name}",
        ],
        "school_event": [
            f"Mittendrin statt nur dabei - Schulleben in {country_name}",
            f"So sieht ein typischer Tag an einer High School in {country_name} aus",
            f"Schulevents in {country_name} sind einfach anders - und wir lieben es!",
        ],
        "daily_life": [
            f"Ein ganz normaler Tag in {country_name} - oder doch nicht so normal?",
            f"Alltag im Ausland: Kleine Momente, grosse Erinnerungen",
            f"Aus dem Leben eines Austauschschuelers in {country_name}",
        ],
        "food": [
            f"Typisch {country_name}: Dieses Essen muss man probiert haben!",
            f"Gastfamilien-Dinner in {country_name} - lecker!",
            f"Food-Check: Was gibt es heute in {country_name}?",
        ],
        "video_clip": [
            f"Einblick in den Alltag in {country_name} - unser Schueler nimmt euch mit!",
            f"Real Talk: So ist das Leben als Austauschschueler in {country_name} wirklich",
            f"POV: Du bist Austauschschueler in {country_name}",
        ],
        "generic": [
            f"Impressionen aus {country_name} von unseren Austauschschuelern",
            f"Highschool-Aufenthalt in {country_name} mit TREFF Sprachreisen",
            f"Ein Stueck {country_name} fuer euren Feed - was meint ihr?",
        ],
    }

    return captions.get(content_key, captions["generic"])
