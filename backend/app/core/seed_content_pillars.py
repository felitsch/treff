"""Seed default Content Pillars into the database.

Creates or updates the 7 content pillars defined in the TREFF content strategy.
Safe to run multiple times (idempotent via upsert on pillar_id).
"""

import json
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_pillar import ContentPillar

logger = logging.getLogger(__name__)

PILLARS = [
    {
        "pillar_id": "erfahrungsberichte",
        "name": "Erfahrungsberichte & Testimonials",
        "description": "Echte Geschichten von TREFF-Teilnehmern: Vor, waehrend und nach dem Auslandsjahr. Der emotionale Kern unserer Strategie.",
        "target_percentage": 30.0,
        "color": "#E74C3C",
        "icon": "\U0001f4dd",
        "buyer_journey_stages": json.dumps(["awareness", "consideration"]),
        "platforms": json.dumps(["instagram_feed", "instagram_story", "tiktok"]),
        "formats": json.dumps(["Carousel", "Reel", "Story-Serie", "Interview-Clip"]),
        "example_topics": json.dumps([
            "Mein erster Tag an der High School",
            "Gastfamilie: Erwartung vs. Realitaet",
            "Was ich nach 3 Monaten gelernt habe",
        ]),
        "kpis": json.dumps(["Saves", "Shares", "Comments", "Story Replies"]),
    },
    {
        "pillar_id": "laender_spotlight",
        "name": "Laender-Spotlights & Destination Content",
        "description": "Informative und inspirierende Inhalte ueber unsere 5 Ziellaender. Fakten, Highlights, Vergleiche.",
        "target_percentage": 20.0,
        "color": "#3498DB",
        "icon": "\U0001f30d",
        "buyer_journey_stages": json.dumps(["awareness", "consideration"]),
        "platforms": json.dumps(["instagram_feed", "instagram_story", "tiktok"]),
        "formats": json.dumps(["Carousel", "Infografik", "Reel", "Quiz-Story"]),
        "example_topics": json.dumps([
            "USA vs. Kanada: Welches Land passt zu dir?",
            "10 Fakten ueber Australien die du nicht wusstest",
        ]),
        "kpis": json.dumps(["Reach", "Saves", "Profile Visits"]),
    },
    {
        "pillar_id": "tipps_tricks",
        "name": "Tipps, Tricks & Guides",
        "description": "Praktische Ratschlaege fuer Bewerbung, Vorbereitung, Packliste, Alltag im Ausland. Mehrwert-Content der geteilt wird.",
        "target_percentage": 20.0,
        "color": "#F39C12",
        "icon": "\U0001f4a1",
        "buyer_journey_stages": json.dumps(["consideration", "decision"]),
        "platforms": json.dumps(["instagram_feed", "instagram_story", "tiktok"]),
        "formats": json.dumps(["Carousel", "Listicle", "How-To Reel", "Checklisten-Story"]),
        "example_topics": json.dumps([
            "Packliste Auslandsjahr: Das muss mit!",
            "Bewerbung Schritt fuer Schritt erklaert",
        ]),
        "kpis": json.dumps(["Saves", "Shares", "Website Clicks"]),
    },
    {
        "pillar_id": "fristen_cta",
        "name": "Fristen, CTAs & Conversion",
        "description": "Bewerbungsfristen, Stipendien-Infos, direkte Handlungsaufforderungen. Conversion-optimiert aber nicht aufdringlich.",
        "target_percentage": 10.0,
        "color": "#E67E22",
        "icon": "\u23f0",
        "buyer_journey_stages": json.dumps(["decision"]),
        "platforms": json.dumps(["instagram_feed", "instagram_story"]),
        "formats": json.dumps(["Single Image", "Story mit Countdown", "Reel"]),
        "example_topics": json.dumps([
            "Bewerbungsfrist USA Classic: Noch 30 Tage!",
            "Stipendium sichern - jetzt bewerben",
        ]),
        "kpis": json.dumps(["Website Clicks", "Link Taps", "DM Inquiries"]),
    },
    {
        "pillar_id": "faq",
        "name": "FAQ & Wissenswertes",
        "description": "Haeufig gestellte Fragen beantwortet. Baut Vertrauen auf und reduziert Hemmschwelle zur Kontaktaufnahme.",
        "target_percentage": 10.0,
        "color": "#9B59B6",
        "icon": "\u2753",
        "buyer_journey_stages": json.dumps(["consideration", "decision"]),
        "platforms": json.dumps(["instagram_feed", "instagram_story", "tiktok"]),
        "formats": json.dumps(["Carousel", "Story-Highlight", "Reel"]),
        "example_topics": json.dumps([
            "Wie viel kostet ein Auslandsjahr?",
            "Brauche ich ein Visum?",
        ]),
        "kpis": json.dumps(["Saves", "DM Inquiries", "Website Clicks"]),
    },
    {
        "pillar_id": "behind_the_scenes",
        "name": "Behind the Scenes & Team",
        "description": "Einblicke ins TREFF-Team, Bueroalltag, Events, Messen. Macht die Marke menschlich und nahbar.",
        "target_percentage": 5.0,
        "color": "#1ABC9C",
        "icon": "\U0001f3ac",
        "buyer_journey_stages": json.dumps(["awareness", "consideration"]),
        "platforms": json.dumps(["instagram_story", "instagram_feed", "tiktok"]),
        "formats": json.dumps(["Story", "Reel", "Foto-Post"]),
        "example_topics": json.dumps([
            "Ein Tag im TREFF-Buero",
            "Wir auf der JuBi Messe",
        ]),
        "kpis": json.dumps(["Engagement Rate", "Follower Growth", "Story Views"]),
    },
    {
        "pillar_id": "infografiken",
        "name": "Infografiken & Daten",
        "description": "Visuelle Aufbereitung von Statistiken, Vergleichen, Prozessen. Hochgradig teilbar und speicherbar.",
        "target_percentage": 5.0,
        "color": "#2ECC71",
        "icon": "\U0001f4ca",
        "buyer_journey_stages": json.dumps(["awareness", "consideration"]),
        "platforms": json.dumps(["instagram_feed", "instagram_story"]),
        "formats": json.dumps(["Carousel", "Single Image", "Story"]),
        "example_topics": json.dumps([
            "Highschool-Aufenthalt in Zahlen",
            "Kostenvergleich: 5 Laender im Ueberblick",
        ]),
        "kpis": json.dumps(["Saves", "Shares", "Reach"]),
    },
]


async def seed_content_pillars(session: AsyncSession) -> int:
    """Seed content pillars. Returns number of new pillars created."""
    created = 0
    for pillar_data in PILLARS:
        result = await session.execute(
            select(ContentPillar).where(ContentPillar.pillar_id == pillar_data["pillar_id"])
        )
        existing = result.scalar_one_or_none()
        if not existing:
            new_pillar = ContentPillar(**pillar_data)
            session.add(new_pillar)
            created += 1

    if created > 0:
        await session.commit()
    return created
