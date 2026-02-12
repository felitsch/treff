"""Seed default content suggestions for dashboard display."""

import logging
from datetime import datetime, timezone, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.content_suggestion import ContentSuggestion

logger = logging.getLogger(__name__)


async def seed_default_suggestions(session: AsyncSession) -> int:
    """Seed default content suggestions if none exist.

    Returns the number of suggestions created.
    """
    # Check if any suggestions already exist
    result = await session.execute(select(func.count(ContentSuggestion.id)))
    count = result.scalar() or 0

    if count > 0:
        return 0  # Already seeded

    today = date.today()

    suggestions = [
        ContentSuggestion(
            suggestion_type="seasonal",
            title="Bewerbungsfristen-Reminder fuer USA 2027",
            description="Informiere ueber die Bewerbungsfrist fuer das USA Classic Programm 2027. Viele Familien beginnen im Fruehling mit der Planung.",
            suggested_category="fristen_cta",
            suggested_country="usa",
            suggested_date=today + timedelta(days=3),
            reason="Saisonale Erinnerung: Bewerbungsfristen fuer Herbst-Abreisen stehen an",
            status="pending",
            created_at=datetime.now(timezone.utc),
        ),
        ContentSuggestion(
            suggestion_type="country_rotation",
            title="Kanada-Spotlight: Zweisprachigkeit erleben",
            description="Erstelle einen Laender-Spotlight Post ueber Kanada mit Fokus auf das bilinguale Erlebnis (Englisch + Franzoesisch).",
            suggested_category="laender_spotlight",
            suggested_country="canada",
            suggested_date=today + timedelta(days=5),
            reason="Kanada war in den letzten 2 Wochen unterrepraesentiert",
            status="pending",
            created_at=datetime.now(timezone.utc),
        ),
        ContentSuggestion(
            suggestion_type="category_balance",
            title="FAQ: Visum und Versicherung",
            description="Erstelle einen FAQ-Carousel-Post zu den haeufigsten Fragen rund um Visum und Auslandskrankenversicherung.",
            suggested_category="faq",
            suggested_country=None,
            suggested_date=today + timedelta(days=7),
            reason="Kategorie-Balance: Bisher keine FAQ-Posts in diesem Monat",
            status="pending",
            created_at=datetime.now(timezone.utc),
        ),
        ContentSuggestion(
            suggestion_type="gap_fill",
            title="Erfahrungsbericht: Rueckkehrer-Story",
            description="Teile die Geschichte eines TREFF-Rueckkehrers mit Zitaten ueber ihre Erfahrungen im Ausland.",
            suggested_category="erfahrungsberichte",
            suggested_country="australia",
            suggested_date=today + timedelta(days=2),
            reason="Luecke erkannt: Keine Posts fuer morgen und uebermorgen geplant",
            status="pending",
            created_at=datetime.now(timezone.utc),
        ),
        ContentSuggestion(
            suggestion_type="weekly_plan",
            title="Tipps fuer die Gastfamilien-Suche",
            description="Erstelle einen Tipps-&-Tricks-Carousel mit praktischen Ratschlaegen fuer die Gastfamilien-Suche.",
            suggested_category="tipps_tricks",
            suggested_country=None,
            suggested_date=today + timedelta(days=4),
            reason="Wochenplan-Vorschlag: Abwechslung im Content-Mix",
            status="pending",
            created_at=datetime.now(timezone.utc),
        ),
    ]

    for s in suggestions:
        session.add(s)

    await session.commit()
    logger.info(f"Seeded {len(suggestions)} default content suggestions")
    return len(suggestions)
