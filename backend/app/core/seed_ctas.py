"""Seed default CTAs (Call-to-Actions) for the CTA library."""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.cta import CTA

logger = logging.getLogger(__name__)

# 35 professional CTAs categorised by goal, platform, and format
DEFAULT_CTAS = [
    # ── Engagement CTAs (encourage interaction) ──────────────────────
    {
        "text": "Kommentier dein Traumland!",
        "category": "engagement",
        "platform": "both",
        "format": "feed",
        "emoji": "🌍",
    },
    {
        "text": "Tag deinen besten Freund!",
        "category": "engagement",
        "platform": "both",
        "format": "feed",
        "emoji": "👯",
    },
    {
        "text": "Speicher dir das!",
        "category": "engagement",
        "platform": "instagram",
        "format": "feed",
        "emoji": "📌",
    },
    {
        "text": "Teile das mit jemandem der ins Ausland will!",
        "category": "engagement",
        "platform": "both",
        "format": "feed",
        "emoji": "📤",
    },
    {
        "text": "Willst du wissen wie es weitergeht?",
        "category": "engagement",
        "platform": "both",
        "format": "reel",
        "emoji": "👀",
    },
    {
        "text": "Schreib JA in die Kommentare!",
        "category": "engagement",
        "platform": "both",
        "format": "reel",
        "emoji": "✅",
    },
    {
        "text": "Welches Land waere deins?",
        "category": "engagement",
        "platform": "both",
        "format": "feed",
        "emoji": "🤔",
    },
    {
        "text": "Stimmst du zu? Sag's uns!",
        "category": "engagement",
        "platform": "both",
        "format": "feed",
        "emoji": "💬",
    },
    {
        "text": "Like wenn du das auch willst!",
        "category": "engagement",
        "platform": "both",
        "format": "reel",
        "emoji": "❤️",
    },
    {
        "text": "Folge uns fuer mehr!",
        "category": "engagement",
        "platform": "both",
        "format": "all",
        "emoji": "➕",
    },
    # ── Conversion CTAs (drive signups / enquiries) ──────────────────
    {
        "text": "Link in Bio!",
        "category": "conversion",
        "platform": "instagram",
        "format": "all",
        "emoji": "🔗",
    },
    {
        "text": "DM uns fuer Infos!",
        "category": "conversion",
        "platform": "both",
        "format": "all",
        "emoji": "📩",
    },
    {
        "text": "Melde dich jetzt an!",
        "category": "conversion",
        "platform": "both",
        "format": "feed",
        "emoji": "✍️",
    },
    {
        "text": "Jetzt kostenlos beraten lassen!",
        "category": "conversion",
        "platform": "both",
        "format": "feed",
        "emoji": "📞",
    },
    {
        "text": "Sichere dir deinen Platz!",
        "category": "conversion",
        "platform": "both",
        "format": "feed",
        "emoji": "🎯",
    },
    {
        "text": "Bewirb dich jetzt!",
        "category": "conversion",
        "platform": "both",
        "format": "all",
        "emoji": "🚀",
    },
    {
        "text": "Fruehbucher-Rabatt sichern!",
        "category": "conversion",
        "platform": "both",
        "format": "feed",
        "emoji": "💰",
    },
    {
        "text": "Mehr Infos auf treff-sprachreisen.de",
        "category": "conversion",
        "platform": "both",
        "format": "all",
        "emoji": "🌐",
    },
    {
        "text": "Schreib uns eine Nachricht!",
        "category": "conversion",
        "platform": "both",
        "format": "story",
        "emoji": "💌",
    },
    {
        "text": "Katalog kostenlos anfordern!",
        "category": "conversion",
        "platform": "both",
        "format": "feed",
        "emoji": "📖",
    },
    # ── Awareness CTAs (brand & info sharing) ────────────────────────
    {
        "text": "Seit 1984 dein Partner!",
        "category": "awareness",
        "platform": "both",
        "format": "all",
        "emoji": "🏆",
    },
    {
        "text": "Erfahre mehr ueber TREFF!",
        "category": "awareness",
        "platform": "both",
        "format": "feed",
        "emoji": "ℹ️",
    },
    {
        "text": "Wusstest du das schon?",
        "category": "awareness",
        "platform": "both",
        "format": "reel",
        "emoji": "💡",
    },
    {
        "text": "200+ Schueler pro Jahr!",
        "category": "awareness",
        "platform": "both",
        "format": "feed",
        "emoji": "🎓",
    },
    {
        "text": "Entdecke 5 Laender mit TREFF!",
        "category": "awareness",
        "platform": "both",
        "format": "feed",
        "emoji": "🗺️",
    },
    {
        "text": "Dein Abenteuer wartet!",
        "category": "awareness",
        "platform": "both",
        "format": "all",
        "emoji": "✨",
    },
    {
        "text": "40 Jahre Erfahrung!",
        "category": "awareness",
        "platform": "both",
        "format": "all",
        "emoji": "⭐",
    },
    # ── Traffic CTAs (drive to website / stories / next slide) ───────
    {
        "text": "Swipe fuer mehr!",
        "category": "traffic",
        "platform": "instagram",
        "format": "story",
        "emoji": "👉",
    },
    {
        "text": "Link in der Bio anklicken!",
        "category": "traffic",
        "platform": "instagram",
        "format": "feed",
        "emoji": "👆",
    },
    {
        "text": "Mehr in unserer Story!",
        "category": "traffic",
        "platform": "instagram",
        "format": "feed",
        "emoji": "📱",
    },
    {
        "text": "Teil 2 kommt morgen!",
        "category": "traffic",
        "platform": "both",
        "format": "reel",
        "emoji": "⏭️",
    },
    {
        "text": "Alle Infos im Highlight!",
        "category": "traffic",
        "platform": "instagram",
        "format": "story",
        "emoji": "⭕",
    },
    {
        "text": "Jetzt Profil besuchen!",
        "category": "traffic",
        "platform": "tiktok",
        "format": "reel",
        "emoji": "👤",
    },
    {
        "text": "Schau dir das Video an!",
        "category": "traffic",
        "platform": "both",
        "format": "feed",
        "emoji": "🎬",
    },
    {
        "text": "Weiterlesen auf der Website!",
        "category": "traffic",
        "platform": "both",
        "format": "feed",
        "emoji": "📰",
    },
]


async def seed_default_ctas(session: AsyncSession) -> int:
    """Seed default CTAs if not already present.

    Returns the number of CTAs seeded.
    """
    # Check if CTAs already exist
    result = await session.execute(select(func.count(CTA.id)))
    existing_count = result.scalar() or 0

    if existing_count > 0:
        logger.info(f"CTAs already seeded ({existing_count} found), skipping.")
        return 0

    count = 0
    for cta_data in DEFAULT_CTAS:
        cta = CTA(
            text=cta_data["text"],
            category=cta_data["category"],
            platform=cta_data["platform"],
            format=cta_data["format"],
            emoji=cta_data.get("emoji"),
            performance_score=0.0,
            usage_count=0,
            is_default=1,
        )
        session.add(cta)
        count += 1

    await session.commit()
    logger.info(f"Seeded {count} default CTAs")
    return count
