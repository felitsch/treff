"""Seed data for AudioSuggestion table.

Provides 25+ curated audio/music recommendations covering all moods,
tempos, platforms and content pillars relevant to TREFF Sprachreisen
social media content.
"""

import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.audio_suggestion import AudioSuggestion

logger = logging.getLogger(__name__)

SEED_AUDIO_SUGGESTIONS = [
    # ── Energetic / Fast ──────────────────────────────────────
    {
        "title": "Trending Upbeat Pop Beat",
        "artist": "Trending Audio",
        "platform": "both",
        "mood": "energetic",
        "tempo": "fast",
        "trending_score": 9.2,
        "url_hint": "https://www.tiktok.com/music/trending",
        "suitable_for": ["laender_spotlight", "tipps_tricks"],
        "description": "Schneller, mitreissender Pop-Beat perfekt fuer dynamische Laender-Montagen und Reisetipps. Hohe Engagement-Rate bei Teenager-Zielgruppe.",
        "is_royalty_free": False,
    },
    {
        "title": "Energetic EDM Drop",
        "artist": "Trending Audio",
        "platform": "tiktok",
        "mood": "energetic",
        "tempo": "fast",
        "trending_score": 8.5,
        "url_hint": "https://www.tiktok.com/music/trending",
        "suitable_for": ["laender_spotlight", "fristen_cta"],
        "description": "EDM-Drop mit hohem Wiedererkennungswert. Ideal fuer schnelle Schnitte und Countdown-Content (Bewerbungsfristen).",
        "is_royalty_free": False,
    },
    {
        "title": "Summer Vibes Tropical House",
        "artist": "Trending Audio",
        "platform": "both",
        "mood": "energetic",
        "tempo": "fast",
        "trending_score": 8.0,
        "url_hint": "https://www.instagram.com/reels/audio/",
        "suitable_for": ["laender_spotlight", "erfahrungsberichte"],
        "description": "Tropical House mit Sommer-Feeling. Perfekt fuer Strand- und Outdoor-Content aus Australien und Neuseeland.",
        "is_royalty_free": False,
    },
    {
        "title": "Upbeat Indie Rock",
        "artist": "Royalty-Free Library",
        "platform": "both",
        "mood": "energetic",
        "tempo": "fast",
        "trending_score": 6.5,
        "url_hint": "",
        "suitable_for": ["laender_spotlight", "tipps_tricks", "erfahrungsberichte"],
        "description": "Indie-Rock mit positiver Energie. Lizenzfrei, ideal fuer Schul-Alltag-Montagen und Abenteuer-Content.",
        "is_royalty_free": True,
    },
    # ── Energetic / Medium ────────────────────────────────────
    {
        "title": "Feel-Good Lo-Fi Pop",
        "artist": "Trending Audio",
        "platform": "instagram",
        "mood": "energetic",
        "tempo": "medium",
        "trending_score": 7.8,
        "url_hint": "https://www.instagram.com/reels/audio/",
        "suitable_for": ["tipps_tricks", "faq", "erfahrungsberichte"],
        "description": "Lockerer Lo-Fi-Pop, beliebt bei Instagram Reels. Gut fuer Talking-Head-Videos und Tipps-Listen.",
        "is_royalty_free": False,
    },
    # ── Emotional / Slow ──────────────────────────────────────
    {
        "title": "Emotional Piano Ballad",
        "artist": "Royalty-Free Library",
        "platform": "both",
        "mood": "emotional",
        "tempo": "slow",
        "trending_score": 7.5,
        "url_hint": "",
        "suitable_for": ["erfahrungsberichte", "laender_spotlight"],
        "description": "Sanfte Klaviermelodie fuer emotionale Erfahrungsberichte und Abschied-/Heimweh-Szenen. Lizenzfrei.",
        "is_royalty_free": True,
    },
    {
        "title": "Cinematic Strings - Fernweh",
        "artist": "Royalty-Free Library",
        "platform": "both",
        "mood": "emotional",
        "tempo": "slow",
        "trending_score": 7.0,
        "url_hint": "",
        "suitable_for": ["laender_spotlight", "erfahrungsberichte"],
        "description": "Filmische Streicher die Fernweh erzeugen. Perfekt fuer Landschafts-Panoramen und Goodbye-Szenen.",
        "is_royalty_free": True,
    },
    {
        "title": "Acoustic Guitar Storytelling",
        "artist": "Trending Audio",
        "platform": "instagram",
        "mood": "emotional",
        "tempo": "slow",
        "trending_score": 8.0,
        "url_hint": "https://www.instagram.com/reels/audio/",
        "suitable_for": ["erfahrungsberichte", "faq"],
        "description": "Akustische Gitarre fuer persoenliche Geschichten. Trending bei emotionalen Reels mit Untertiteln.",
        "is_royalty_free": False,
    },
    {
        "title": "Nostalgic Indie Folk",
        "artist": "Trending Audio",
        "platform": "both",
        "mood": "emotional",
        "tempo": "medium",
        "trending_score": 7.2,
        "url_hint": "https://www.tiktok.com/music/trending",
        "suitable_for": ["erfahrungsberichte", "laender_spotlight"],
        "description": "Nostalgischer Indie-Folk fuer Erinnerungs-Montagen. Gut fuer Before/After-Content.",
        "is_royalty_free": False,
    },
    # ── Funny / Medium-Fast ───────────────────────────────────
    {
        "title": "Quirky Comedy Beat",
        "artist": "Trending Audio",
        "platform": "tiktok",
        "mood": "funny",
        "tempo": "medium",
        "trending_score": 8.8,
        "url_hint": "https://www.tiktok.com/music/trending",
        "suitable_for": ["tipps_tricks", "faq"],
        "description": "Witziger Beat fuer Comedy-Sketches und 'Erwartung vs. Realitaet' Content. Sehr hohe Viralitaet auf TikTok.",
        "is_royalty_free": False,
    },
    {
        "title": "Cartoon Sound Effects Mix",
        "artist": "Sound Library",
        "platform": "tiktok",
        "mood": "funny",
        "tempo": "fast",
        "trending_score": 7.5,
        "url_hint": "https://www.tiktok.com/music/trending",
        "suitable_for": ["tipps_tricks", "faq"],
        "description": "Cartoon-Soundeffekte fuer lustige Reaktions-Videos und Pannen-Compilations. Ideal fuer Gen-Z Content.",
        "is_royalty_free": False,
    },
    {
        "title": "Meme Remix Beat",
        "artist": "Trending Audio",
        "platform": "tiktok",
        "mood": "funny",
        "tempo": "fast",
        "trending_score": 9.0,
        "url_hint": "https://www.tiktok.com/music/trending",
        "suitable_for": ["tipps_tricks", "faq", "fristen_cta"],
        "description": "Meme-Beat der gerade viral geht. Perfekt fuer ironische Takes und Kulturschock-Vergleiche.",
        "is_royalty_free": False,
    },
    {
        "title": "Playful Ukulele",
        "artist": "Royalty-Free Library",
        "platform": "both",
        "mood": "funny",
        "tempo": "medium",
        "trending_score": 6.0,
        "url_hint": "",
        "suitable_for": ["tipps_tricks", "faq", "erfahrungsberichte"],
        "description": "Froehliche Ukulele-Melodie fuer leichte, unterhaltsame Inhalte. Lizenzfrei und vielseitig einsetzbar.",
        "is_royalty_free": True,
    },
    # ── Chill / Slow-Medium ───────────────────────────────────
    {
        "title": "Lo-Fi Study Beats",
        "artist": "Royalty-Free Library",
        "platform": "both",
        "mood": "chill",
        "tempo": "slow",
        "trending_score": 7.0,
        "url_hint": "",
        "suitable_for": ["tipps_tricks", "faq", "erfahrungsberichte"],
        "description": "Lo-Fi Hip-Hop Beats fuer ruhige Erklaervideos und Studien-Alltag-Content. Lizenzfrei, dauerhaft beliebt.",
        "is_royalty_free": True,
    },
    {
        "title": "Ambient Chill Waves",
        "artist": "Royalty-Free Library",
        "platform": "instagram",
        "mood": "chill",
        "tempo": "slow",
        "trending_score": 6.5,
        "url_hint": "",
        "suitable_for": ["laender_spotlight", "erfahrungsberichte"],
        "description": "Ruhige Ambient-Wellen fuer Sonnenuntergang- und Naturszenen. Ideal fuer Neuseeland und Irland Content.",
        "is_royalty_free": True,
    },
    {
        "title": "Soft R&B Groove",
        "artist": "Trending Audio",
        "platform": "instagram",
        "mood": "chill",
        "tempo": "medium",
        "trending_score": 7.3,
        "url_hint": "https://www.instagram.com/reels/audio/",
        "suitable_for": ["erfahrungsberichte", "laender_spotlight"],
        "description": "Sanfter R&B-Groove fuer Lifestyle-Content und taegliche Routine-Videos im Ausland.",
        "is_royalty_free": False,
    },
    {
        "title": "Dreamy Synth Pop",
        "artist": "Trending Audio",
        "platform": "both",
        "mood": "chill",
        "tempo": "medium",
        "trending_score": 7.8,
        "url_hint": "https://www.tiktok.com/music/trending",
        "suitable_for": ["laender_spotlight", "erfahrungsberichte"],
        "description": "Traumerischer Synthpop mit Retro-Feeling. Trending fuer aesthetische Travel-Content und ASMR-artige Videos.",
        "is_royalty_free": False,
    },
    # ── Dramatic / Various ────────────────────────────────────
    {
        "title": "Epic Cinematic Trailer",
        "artist": "Royalty-Free Library",
        "platform": "both",
        "mood": "dramatic",
        "tempo": "medium",
        "trending_score": 7.5,
        "url_hint": "",
        "suitable_for": ["laender_spotlight", "fristen_cta"],
        "description": "Epische Filmmusik fuer Laender-Reveal-Videos und Countdown-Content. Baut Spannung auf.",
        "is_royalty_free": True,
    },
    {
        "title": "Dark Hip-Hop Beat",
        "artist": "Trending Audio",
        "platform": "tiktok",
        "mood": "dramatic",
        "tempo": "medium",
        "trending_score": 8.2,
        "url_hint": "https://www.tiktok.com/music/trending",
        "suitable_for": ["fristen_cta", "laender_spotlight"],
        "description": "Dunkler Hip-Hop-Beat fuer Storytime-Videos und dramatische Reveals ('Was passiert wenn die Frist ablaeuft').",
        "is_royalty_free": False,
    },
    {
        "title": "Suspenseful Build-Up",
        "artist": "Royalty-Free Library",
        "platform": "both",
        "mood": "dramatic",
        "tempo": "slow",
        "trending_score": 6.8,
        "url_hint": "",
        "suitable_for": ["fristen_cta", "laender_spotlight"],
        "description": "Spannungsaufbau mit langsamer Steigerung. Perfekt fuer 'Wirst du angenommen?' Reveal-Videos.",
        "is_royalty_free": True,
    },
    {
        "title": "Orchestral Adventure Theme",
        "artist": "Royalty-Free Library",
        "platform": "both",
        "mood": "dramatic",
        "tempo": "fast",
        "trending_score": 7.0,
        "url_hint": "",
        "suitable_for": ["laender_spotlight", "erfahrungsberichte"],
        "description": "Abenteuerliche Orchestermusik fuer Reise-Montagen und 'Mein Jahr im Ausland' Zusammenfassungen.",
        "is_royalty_free": True,
    },
    # ── Additional mixed moods ────────────────────────────────
    {
        "title": "Motivational Hip-Hop",
        "artist": "Trending Audio",
        "platform": "both",
        "mood": "energetic",
        "tempo": "medium",
        "trending_score": 8.3,
        "url_hint": "https://www.tiktok.com/music/trending",
        "suitable_for": ["erfahrungsberichte", "fristen_cta", "tipps_tricks"],
        "description": "Motivierender Hip-Hop Beat fuer 'Du schaffst das' Content und Bewerbungs-Motivation.",
        "is_royalty_free": False,
    },
    {
        "title": "Country Road Acoustic",
        "artist": "Royalty-Free Library",
        "platform": "instagram",
        "mood": "chill",
        "tempo": "medium",
        "trending_score": 6.2,
        "url_hint": "",
        "suitable_for": ["laender_spotlight", "erfahrungsberichte"],
        "description": "Akustischer Country-Sound speziell fuer USA und Kanada Content. Road-Trip-Feeling.",
        "is_royalty_free": True,
    },
    {
        "title": "Celtic Folk Melody",
        "artist": "Royalty-Free Library",
        "platform": "both",
        "mood": "emotional",
        "tempo": "medium",
        "trending_score": 6.5,
        "url_hint": "",
        "suitable_for": ["laender_spotlight"],
        "description": "Keltische Folkmusik mit Floete und Harfe. Perfekt fuer Irland-Spotlight-Content.",
        "is_royalty_free": True,
    },
    {
        "title": "Didgeridoo & Nature Sounds",
        "artist": "Royalty-Free Library",
        "platform": "both",
        "mood": "chill",
        "tempo": "slow",
        "trending_score": 5.8,
        "url_hint": "",
        "suitable_for": ["laender_spotlight"],
        "description": "Didgeridoo mit Naturklaengen fuer Australien-Content. Authentische Atmosphaere.",
        "is_royalty_free": True,
    },
    {
        "title": "Viral Dance Challenge Beat",
        "artist": "Trending Audio",
        "platform": "tiktok",
        "mood": "energetic",
        "tempo": "fast",
        "trending_score": 9.5,
        "url_hint": "https://www.tiktok.com/music/trending",
        "suitable_for": ["tipps_tricks", "erfahrungsberichte", "fristen_cta"],
        "description": "Aktueller viraler Dance-Challenge-Beat. Hoechste Reichweite moeglich wenn mit Trend kombiniert.",
        "is_royalty_free": False,
    },
]


async def seed_audio_suggestions(session: AsyncSession) -> int:
    """Seed audio suggestions into the database.

    Only adds entries if the table is empty or has fewer entries
    than the seed data.

    Returns:
        Number of suggestions added.
    """
    result = await session.execute(
        select(func.count(AudioSuggestion.id))
    )
    existing_count = result.scalar() or 0

    if existing_count >= len(SEED_AUDIO_SUGGESTIONS):
        logger.info(
            "Audio suggestions already seeded (%d entries). Skipping.",
            existing_count,
        )
        return 0

    added = 0
    for data in SEED_AUDIO_SUGGESTIONS:
        # Check if this title already exists
        check = await session.execute(
            select(AudioSuggestion).where(AudioSuggestion.title == data["title"])
        )
        if check.scalar_one_or_none():
            continue

        suggestion = AudioSuggestion(
            title=data["title"],
            artist=data.get("artist"),
            platform=data["platform"],
            mood=data["mood"],
            tempo=data["tempo"],
            trending_score=data["trending_score"],
            url_hint=data.get("url_hint", ""),
            suitable_for=json.dumps(data.get("suitable_for", []), ensure_ascii=False),
            description=data.get("description", ""),
            is_royalty_free=data.get("is_royalty_free", False),
            is_default=True,
            user_id=None,
        )
        session.add(suggestion)
        added += 1

    if added > 0:
        await session.commit()
        logger.info("Seeded %d audio suggestions.", added)

    return added
