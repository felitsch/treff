"""Video Script Generator API routes.

Generates scene-by-scene video scripts for Instagram Reels and TikTok,
using hook formulas, timing templates, and strategy context from JSON files.
"""
from __future__ import annotations

import json
import logging
import random
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.core.strategy_loader import StrategyLoader
from app.models.video_script import VideoScript
from app.models.setting import Setting

logger = logging.getLogger(__name__)

router = APIRouter()

# ──────────────────────────────────────────────
# Timing templates: how to distribute time per scene type
# ──────────────────────────────────────────────
TIMING_TEMPLATES = {
    15: {
        "label": "15s Reel",
        "scenes": [
            {"scene_type": "hook", "duration": 3, "description": "Attention-grabbing Hook"},
            {"scene_type": "content", "duration": 9, "description": "Main content / key message"},
            {"scene_type": "cta", "duration": 3, "description": "Call-to-Action"},
        ],
    },
    30: {
        "label": "30s Reel",
        "scenes": [
            {"scene_type": "hook", "duration": 5, "description": "Attention-grabbing Hook"},
            {"scene_type": "problem", "duration": 7, "description": "Problem or question setup"},
            {"scene_type": "content", "duration": 8, "description": "Main content / solution"},
            {"scene_type": "proof", "duration": 5, "description": "Evidence or example"},
            {"scene_type": "cta", "duration": 5, "description": "Call-to-Action"},
        ],
    },
    60: {
        "label": "60s Reel",
        "scenes": [
            {"scene_type": "hook", "duration": 5, "description": "Attention-grabbing Hook"},
            {"scene_type": "problem", "duration": 10, "description": "Problem or question setup"},
            {"scene_type": "content", "duration": 15, "description": "Main content part 1"},
            {"scene_type": "content_2", "duration": 10, "description": "Main content part 2"},
            {"scene_type": "proof", "duration": 10, "description": "Evidence, example or testimony"},
            {"scene_type": "cta", "duration": 10, "description": "Call-to-Action and wrap-up"},
        ],
    },
    90: {
        "label": "90s TikTok",
        "scenes": [
            {"scene_type": "hook", "duration": 5, "description": "Attention-grabbing Hook"},
            {"scene_type": "intro", "duration": 10, "description": "Topic introduction"},
            {"scene_type": "content", "duration": 20, "description": "Main content part 1"},
            {"scene_type": "content_2", "duration": 15, "description": "Main content part 2"},
            {"scene_type": "content_3", "duration": 10, "description": "Main content part 3"},
            {"scene_type": "proof", "duration": 10, "description": "Evidence or personal story"},
            {"scene_type": "transition", "duration": 5, "description": "Transition / summary"},
            {"scene_type": "cta", "duration": 15, "description": "Call-to-Action and wrap-up"},
        ],
    },
}

# Country data for script generation
COUNTRY_NAMES = {
    "usa": "USA", "canada": "Kanada", "australia": "Australien",
    "newzealand": "Neuseeland", "ireland": "Irland",
}

COUNTRY_VISUALS = {
    "usa": ["Typisches High-School-Gebaeude", "American Football Spiel", "Yellow School Bus", "Cheerleader", "Locker Hallway", "Homecoming Dance"],
    "canada": ["Rocky Mountains Panorama", "Ahornblatt / Maple Leaf", "Hockey-Spiel", "Bunte Herbstlandschaft", "Multikulturelles Stadtzentrum", "Niagara Falls"],
    "australia": ["Strand mit Surfern", "Koala im Baum", "Sydney Opera House", "Great Barrier Reef Unterwasser", "Outback-Landschaft", "Schuluniform-Gruppe"],
    "newzealand": ["Herr-der-Ringe-Landschaft", "Maori Haka Aufführung", "Bungee-Jumping", "Schafe auf gruener Wiese", "Milford Sound", "Schulhof mit Bergen"],
    "ireland": ["Gruene Klippen (Cliffs of Moher)", "Dublin Temple Bar Strasse", "Irische Pub-Atmosphaere", "Steinmauern und Schafe", "Gaelisches Fussballspiel", "Regenbogen ueber Landschaft"],
}


def _build_scene_script_prompt(
    topic: str,
    platform: str,
    duration: int,
    hook_formula: Optional[dict],
    country: Optional[str],
    category: Optional[str],
    buyer_journey_stage: Optional[str],
    tone: str,
    strategy: StrategyLoader,
) -> str:
    """Build the Gemini prompt for video script generation."""
    timing = TIMING_TEMPLATES.get(duration, TIMING_TEMPLATES[30])
    country_name = COUNTRY_NAMES.get(country, "ein Land")

    # Build scene structure description
    scene_descriptions = []
    current_time = 0
    for i, scene in enumerate(timing["scenes"]):
        end_time = current_time + scene["duration"]
        scene_descriptions.append(
            f"  Szene {i + 1} ({scene['scene_type']}): {current_time}s - {end_time}s ({scene['duration']}s) - {scene['description']}"
        )
        current_time = end_time

    scene_structure = "\n".join(scene_descriptions)

    # Hook formula instruction
    hook_instruction = ""
    if hook_formula:
        hook_name = hook_formula.get("name", "")
        hook_template = hook_formula.get("template", "")
        hook_examples = hook_formula.get("examples", [])
        example_str = f'\nBeispiel: "{hook_examples[0]}"' if hook_examples else ""
        hook_instruction = f"""
HOOK-FORMEL (PFLICHT fuer Szene 1):
Verwende die "{hook_name}" Hook-Formel: "{hook_template}"{example_str}
Die erste Szene MUSS dieser Formel folgen und sofort Aufmerksamkeit erregen!"""

    # Strategy context
    strategy_context = strategy.build_strategy_prompt_sections(
        platform=platform,
        category=category,
        buyer_journey_stage=buyer_journey_stage,
    )

    # Country visuals
    visuals = COUNTRY_VISUALS.get(country, ["Internationale Szenen", "Schulgebaeude", "Landschaft"])
    visual_suggestions = ", ".join(random.sample(visuals, min(3, len(visuals))))

    prompt = f"""Du bist ein Video-Script-Experte fuer TREFF Sprachreisen Social Media.

AUFGABE: Erstelle ein komplettes Video-Script fuer ein {timing['label']} ({duration} Sekunden).

THEMA: {topic}
PLATTFORM: {platform}
LAND: {country_name}
TONALITAET: {tone}
{hook_instruction}

TIMING-VORLAGE (MUSS exakt eingehalten werden):
{scene_structure}

VISUELLE VORSCHLAEGE fuer {country_name}: {visual_suggestions}

{strategy_context}

ANFORDERUNGEN:
- Erstelle genau {len(timing['scenes'])} Szenen
- Jede Szene hat: voiceover_text, visual_description, text_overlay (kurzer On-Screen Text), music_note, b_roll_suggestion
- Die Zeiten MUESSEN exakt der Timing-Vorlage entsprechen
- Voiceover-Text soll zur Sprechgeschwindigkeit passen (~2.5 Worte/Sekunde)
- Alle Texte auf Deutsch
- Der Text-Overlay soll maximal 6-8 Worte pro Szene haben
- Die letzte Szene MUSS einen klaren Call-to-Action enthalten

Antworte AUSSCHLIESSLICH im folgenden JSON-Format:
{{
  "title": "Kurzer Script-Titel",
  "scenes": [
    {{
      "scene_number": 1,
      "start_time": 0,
      "end_time": 3,
      "scene_type": "hook",
      "voiceover_text": "Der gesprochene Text fuer diese Szene",
      "visual_description": "Was visuell zu sehen ist (B-Roll, Bilder, etc.)",
      "text_overlay": "Kurzer On-Screen Text (max 8 Worte)",
      "music_note": "Musikstimmung: z.B. Trending Beat, emotional, upbeat",
      "b_roll_suggestion": "Konkreter B-Roll Vorschlag"
    }}
  ],
  "voiceover_full": "Der komplette Voiceover-Text aller Szenen zusammen",
  "visual_notes": "Allgemeine visuelle Anmerkungen zum gesamten Video",
  "cta_type": "question|save|share|ugc|dm|link_in_bio"
}}"""

    return prompt


def _generate_rule_based_script(
    topic: str,
    platform: str,
    duration: int,
    hook_formula: Optional[dict],
    country: Optional[str],
    tone: str,
) -> dict:
    """Generate a rule-based video script as fallback when Gemini is unavailable."""
    timing = TIMING_TEMPLATES.get(duration, TIMING_TEMPLATES[30])
    country_name = COUNTRY_NAMES.get(country, "ein Land")
    visuals = COUNTRY_VISUALS.get(country, ["Internationale Szenen", "Schulgebaeude"])

    # Generate hook text
    if hook_formula:
        hook_template = hook_formula.get("template", "")
        hook_examples = hook_formula.get("examples", [])
        if hook_examples:
            hook_text = random.choice(hook_examples)
        else:
            hook_text = hook_template.replace("{Land A}", country_name).replace("{Land B}", "Kanada" if country != "canada" else "USA")
    else:
        hook_text = f"Wusstest du das ueber {country_name}? Das hat mich TOTAL ueberrascht..."

    # Build scenes
    scenes = []
    current_time = 0
    for i, scene_template in enumerate(timing["scenes"]):
        end_time = current_time + scene_template["duration"]
        scene_type = scene_template["scene_type"]

        if scene_type == "hook":
            voiceover = hook_text
            text_overlay = hook_text[:50] + ("..." if len(hook_text) > 50 else "")
            visual = random.choice(visuals)
            music = "Attention-grabbing Beat Drop"
            b_roll = f"Schnelle Montage: {', '.join(random.sample(visuals, min(2, len(visuals))))}"
        elif scene_type == "cta":
            cta_options = [
                f"Folge TREFF Sprachreisen fuer mehr! Link in Bio!",
                f"Willst du auch nach {country_name}? DM uns!",
                f"Speicher dieses Video fuer spaeter!",
                f"Tagge jemanden der das wissen muss!",
            ]
            voiceover = random.choice(cta_options)
            text_overlay = "Link in Bio!"
            visual = "TREFF Logo + Website URL Einblendung"
            music = "Upbeat Outro"
            b_roll = "Montage von gluecklichen Austauschschuelern"
        elif scene_type in ("problem", "intro"):
            voiceover = f"Viele fragen sich: Wie ist ein Highschool-Jahr in {country_name} wirklich? {topic}"
            text_overlay = topic[:50]
            visual = f"B-Roll: {country_name} Alltagsszenen"
            music = "Spannungsaufbau"
            b_roll = random.choice(visuals)
        elif scene_type == "proof":
            voiceover = f"Das sagen TREFF-Schueler die wirklich dort waren. Ueber 200 Teilnehmer pro Jahr seit 1984."
            text_overlay = "Seit 1984 - 200+ Schueler/Jahr"
            visual = "Testimonial-Clips oder Fotos von TREFF-Alumni"
            music = "Emotional, aufbauend"
            b_roll = "Collage von Schueler-Fotos"
        elif scene_type == "transition":
            voiceover = f"Also wenn du dir unsicher bist: {country_name} koennte genau das Richtige fuer dich sein."
            text_overlay = f"{country_name} wartet auf dich!"
            visual = f"Panorama-Aufnahme {country_name}"
            music = "Uebergang, sanft"
            b_roll = random.choice(visuals)
        else:
            # content, content_2, content_3
            content_options = [
                f"Das Schulsystem in {country_name} ist komplett anders als in Deutschland. Und das ist gut so!",
                f"Deine Gastfamilie wird dich aufnehmen wie ein eigenes Kind. Das ist das Besondere.",
                f"Von Ausfluegen ueber Sport bis zu Clubs - in {country_name} ist immer was los.",
                f"Und das Beste: Dein Englisch wird so gut, wie es kein Schulunterricht je schaffen koennte.",
                f"TREFF Sprachreisen betreut dich von der Bewerbung bis zur Rueckkehr. Du bist nie allein.",
            ]
            voiceover = random.choice(content_options)
            text_overlay = voiceover[:40] + "..."
            visual = random.choice(visuals)
            music = "Upbeat, modern"
            b_roll = random.choice(visuals)

        scenes.append({
            "scene_number": i + 1,
            "start_time": current_time,
            "end_time": end_time,
            "scene_type": scene_type,
            "voiceover_text": voiceover,
            "visual_description": visual,
            "text_overlay": text_overlay,
            "music_note": music,
            "b_roll_suggestion": b_roll,
        })
        current_time = end_time

    # Combine voiceover
    voiceover_full = " ".join(s["voiceover_text"] for s in scenes)

    return {
        "title": f"Video-Script: {topic} ({country_name})",
        "scenes": scenes,
        "voiceover_full": voiceover_full,
        "visual_notes": f"Fokus auf authentische Bilder aus {country_name}. Mix aus B-Roll und Text-Overlays. Untertitel sind Pflicht.",
        "cta_type": random.choice(["question", "save", "share", "link_in_bio"]),
    }


async def _get_gemini_api_key(user_id: int, db: AsyncSession) -> Optional[str]:
    """Get Gemini API key from user settings or environment."""
    import os

    # Check user settings first
    result = await db.execute(
        select(Setting).where(
            Setting.user_id == user_id,
            Setting.key == "gemini_api_key",
        )
    )
    setting = result.scalar_one_or_none()
    if setting and setting.value:
        return setting.value

    # Fall back to environment
    return os.environ.get("GEMINI_API_KEY", "")


def _script_to_dict(script: VideoScript) -> dict:
    """Convert a VideoScript model to a dict for API response."""
    return {
        "id": script.id,
        "title": script.title,
        "platform": script.platform,
        "duration_seconds": script.duration_seconds,
        "hook_formula": script.hook_formula,
        "topic": script.topic,
        "country": script.country,
        "category": script.category,
        "buyer_journey_stage": script.buyer_journey_stage,
        "tone": script.tone,
        "scenes": json.loads(script.scenes) if isinstance(script.scenes, str) else script.scenes,
        "voiceover_full": script.voiceover_full,
        "visual_notes": script.visual_notes,
        "cta_type": script.cta_type,
        "source": script.source,
        "post_id": script.post_id,
        "created_at": script.created_at.isoformat() if script.created_at else None,
        "updated_at": script.updated_at.isoformat() if script.updated_at else None,
    }


# ──────────────────────────────────────────────
# API Endpoints
# ──────────────────────────────────────────────

@router.get("/timing-templates")
async def get_timing_templates(user_id: int = Depends(get_current_user_id)):
    """Return available timing templates for video scripts."""
    return {
        "templates": {
            str(k): {"label": v["label"], "duration": k, "scene_count": len(v["scenes"]),
                      "scenes": v["scenes"]}
            for k, v in TIMING_TEMPLATES.items()
        }
    }


@router.get("/hook-formulas")
async def get_hook_formulas(
    platform: str = "instagram_reels",
    user_id: int = Depends(get_current_user_id),
):
    """Return available hook formulas from strategy JSON, optionally filtered by platform."""
    strategy = StrategyLoader.instance()
    formulas = strategy.get_hook_formulas(platform)
    return {
        "formulas": formulas,
        "count": len(formulas),
    }


@router.post("/generate")
async def generate_video_script(
    request: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Generate a complete video script with scene-by-scene breakdown.

    Body:
    - topic (str, required): Video topic
    - platform (str): reels, tiktok, story (default: reels)
    - duration (int): 15, 30, 60, or 90 seconds (default: 30)
    - hook_formula_id (str, optional): ID of hook formula from social-content.json
    - country (str, optional): Country code (usa, canada, etc.)
    - category (str, optional): Content category
    - buyer_journey_stage (str, optional): awareness, consideration, decision
    - tone (str, optional): Tone of voice (default: jugendlich)
    """
    topic = request.get("topic", "")
    if not topic:
        raise HTTPException(status_code=400, detail="topic is required")

    platform = request.get("platform", "reels")
    duration = request.get("duration", 30)
    hook_formula_id = request.get("hook_formula_id")
    country = request.get("country")
    category = request.get("category")
    buyer_journey_stage = request.get("buyer_journey_stage")
    tone = request.get("tone", "jugendlich")

    # Validate duration
    if duration not in TIMING_TEMPLATES:
        raise HTTPException(status_code=400, detail=f"Invalid duration: {duration}. Must be one of {list(TIMING_TEMPLATES.keys())}")

    # Map platform to social-content platform names for strategy
    platform_map = {
        "reels": "instagram_reels",
        "tiktok": "tiktok",
        "story": "instagram_stories",
    }
    strategy_platform = platform_map.get(platform, "instagram_reels")

    # Load strategy and hook formula
    strategy = StrategyLoader.instance()

    hook_formula = None
    if hook_formula_id:
        formulas = strategy.get_hook_formulas()
        for f in formulas:
            if f.get("id") == hook_formula_id:
                hook_formula = f
                break
    if not hook_formula:
        # Pick a weighted random one
        hook_formula = strategy.get_weighted_hook(strategy_platform)

    # Pick weighted country if not specified
    if not country:
        country = strategy.pick_weighted_country()

    # Try Gemini first
    source = "rule_based"
    script_data = None
    api_key = await _get_gemini_api_key(user_id, db)

    if api_key:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)
            prompt = _build_scene_script_prompt(
                topic=topic,
                platform=strategy_platform,
                duration=duration,
                hook_formula=hook_formula,
                country=country,
                category=category,
                buyer_journey_stage=buyer_journey_stage,
                tone=tone,
                strategy=strategy,
            )

            system_prompt = """Du bist ein professioneller Video-Script-Autor fuer TREFF Sprachreisen.
Du erstellst praezise, zeitlich exakte Video-Skripte fuer Instagram Reels und TikTok.
Alle Texte auf Deutsch. Antworte NUR im geforderten JSON-Format."""

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    temperature=0.8,
                    max_output_tokens=4096,
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

            script_data = json.loads(response_text)
            source = "gemini"
            logger.info("Gemini video script generation succeeded for topic=%s, platform=%s", topic, platform)

        except Exception as e:
            logger.warning("Gemini video script generation failed: %s", e)
            script_data = None

    # Fall back to rule-based
    if not script_data:
        script_data = _generate_rule_based_script(
            topic=topic,
            platform=platform,
            duration=duration,
            hook_formula=hook_formula,
            country=country,
            tone=tone,
        )

    # Save to database
    video_script = VideoScript(
        user_id=user_id,
        title=script_data.get("title", f"Script: {topic}"),
        platform=platform,
        duration_seconds=duration,
        hook_formula=hook_formula.get("id", "") if hook_formula else None,
        topic=topic,
        country=country,
        category=category,
        buyer_journey_stage=buyer_journey_stage,
        tone=tone,
        scenes=json.dumps(script_data.get("scenes", []), ensure_ascii=False),
        voiceover_full=script_data.get("voiceover_full", ""),
        visual_notes=script_data.get("visual_notes", ""),
        cta_type=script_data.get("cta_type", ""),
        source=source,
    )
    db.add(video_script)
    await db.commit()
    await db.refresh(video_script)

    logger.info("Video script saved: id=%d, topic=%s, platform=%s, duration=%ds", video_script.id, topic, platform, duration)

    return _script_to_dict(video_script)


@router.get("")
async def list_video_scripts(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    limit: int = 20,
    offset: int = 0,
):
    """List user's video scripts, most recent first."""
    result = await db.execute(
        select(VideoScript)
        .where(VideoScript.user_id == user_id)
        .order_by(desc(VideoScript.created_at))
        .limit(limit)
        .offset(offset)
    )
    scripts = result.scalars().all()
    return {"scripts": [_script_to_dict(s) for s in scripts], "count": len(scripts)}


@router.get("/{script_id}")
async def get_video_script(
    script_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a single video script by ID."""
    result = await db.execute(
        select(VideoScript).where(
            VideoScript.id == script_id,
            VideoScript.user_id == user_id,
        )
    )
    script = result.scalar_one_or_none()
    if not script:
        raise HTTPException(status_code=404, detail="Video script not found")
    return _script_to_dict(script)


@router.put("/{script_id}")
async def update_video_script(
    script_id: int,
    request: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update a video script (edit scenes, title, etc.)."""
    result = await db.execute(
        select(VideoScript).where(
            VideoScript.id == script_id,
            VideoScript.user_id == user_id,
        )
    )
    script = result.scalar_one_or_none()
    if not script:
        raise HTTPException(status_code=404, detail="Video script not found")

    # Update allowed fields
    if "title" in request:
        script.title = request["title"]
    if "scenes" in request:
        script.scenes = json.dumps(request["scenes"], ensure_ascii=False)
    if "voiceover_full" in request:
        script.voiceover_full = request["voiceover_full"]
    if "visual_notes" in request:
        script.visual_notes = request["visual_notes"]
    if "cta_type" in request:
        script.cta_type = request["cta_type"]
    if "post_id" in request:
        script.post_id = request["post_id"]

    await db.commit()
    await db.refresh(script)

    return _script_to_dict(script)


@router.delete("/{script_id}")
async def delete_video_script(
    script_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a video script."""
    result = await db.execute(
        select(VideoScript).where(
            VideoScript.id == script_id,
            VideoScript.user_id == user_id,
        )
    )
    script = result.scalar_one_or_none()
    if not script:
        raise HTTPException(status_code=404, detail="Video script not found")

    await db.delete(script)
    await db.commit()

    return {"success": True, "deleted_id": script_id}
