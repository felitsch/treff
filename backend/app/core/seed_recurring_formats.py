"""Seed default recurring formats for the Running Gags und wiederkehrende Formate feature."""

import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.recurring_format import RecurringFormat

logger = logging.getLogger(__name__)

# The 5 standard recurring formats as specified in the feature requirements
DEFAULT_RECURRING_FORMATS = [
    {
        "name": "TREFF Freitags-Fail",
        "description": "Lustiger Kulturschock der Woche! Jeden Freitag teilen wir den witzigsten Culture-Shock-Moment unserer Austauschschueler. Leichtherzig, relatable und perfekt zum Wochenende.",
        "frequency": "weekly",
        "preferred_day": "Freitag",
        "preferred_time": "17:00",
        "tone": "witzig",
        "hashtags": json.dumps(["#TREFFFreitagsFail", "#CultureShock", "#Auslandsjahr", "#TREFFSprachreisen", "#FridayFails"]),
        "icon": "😂",
        "category": "faq",
        "is_active": True,
        "is_default": True,
    },
    {
        "name": "Motivation Monday",
        "description": "Jeden Montag starten wir die Woche mit einem epischen Moment eines TREFF-Schuelers! Inspirierende Zitate, Erfolgsgeschichten oder atemberaubende Fotos aus dem Ausland.",
        "frequency": "weekly",
        "preferred_day": "Montag",
        "preferred_time": "07:30",
        "tone": "motivierend",
        "hashtags": json.dumps(["#MotivationMonday", "#TREFFSprachreisen", "#Auslandsjahr", "#Inspiration", "#MondayMotivation"]),
        "icon": "💪",
        "category": "tipps_tricks",
        "is_active": True,
        "is_default": True,
    },
    {
        "name": "Throwback Thursday",
        "description": "Jeden Donnerstag blicken wir zurueck auf unvergessliche Momente unserer Alumni! Ehemalige Austauschschueler teilen ihre besten Erinnerungen und wie das Auslandsjahr ihr Leben veraendert hat.",
        "frequency": "weekly",
        "preferred_day": "Donnerstag",
        "preferred_time": "18:00",
        "tone": "emotional",
        "hashtags": json.dumps(["#ThrowbackThursday", "#TBT", "#TREFFAlumni", "#TREFFSprachreisen", "#Auslandsjahr"]),
        "icon": "📸",
        "category": "erfahrungsberichte",
        "is_active": True,
        "is_default": True,
    },
    {
        "name": "Wusstest-du-Mittwoch",
        "description": "Jeden Mittwoch ein ueberraschender Fun Fact ueber eines unserer Ziellaender! Wusstest du, dass in Neuseeland mehr Schafe als Menschen leben? Bildend, unterhaltsam und teilbar.",
        "frequency": "weekly",
        "preferred_day": "Mittwoch",
        "preferred_time": "12:00",
        "tone": "informativ",
        "hashtags": json.dumps(["#WusstestDu", "#FunFact", "#TREFFSprachreisen", "#Auslandsjahr", "#HighSchoolAbroad"]),
        "icon": "🤓",
        "category": "laender_spotlight",
        "is_active": True,
        "is_default": True,
    },
    {
        "name": "Sonntags-Sehnsucht",
        "description": "Jeden Sonntag ein stimmungsvolles Bild oder Zitat, das Fernweh weckt. Schoene Landschaften, Sonnenuntergaenge oder emotionale Momente aus dem Auslandsjahr. Perfekt zum Traeumen.",
        "frequency": "weekly",
        "preferred_day": "Sonntag",
        "preferred_time": "19:00",
        "tone": "emotional",
        "hashtags": json.dumps(["#SonntagsSehnsucht", "#Fernweh", "#TREFFSprachreisen", "#Auslandsjahr", "#Wanderlust"]),
        "icon": "🌅",
        "category": "erfahrungsberichte",
        "is_active": True,
        "is_default": True,
    },
]


async def seed_recurring_formats(session: AsyncSession) -> int:
    """Seed default recurring formats if not already present.

    Returns the number of formats seeded.
    """
    # Check if recurring formats already exist
    result = await session.execute(select(func.count(RecurringFormat.id)))
    existing_count = result.scalar() or 0

    if existing_count > 0:
        logger.info(f"Recurring formats already seeded ({existing_count} found), skipping.")
        return 0

    count = 0
    for fmt_data in DEFAULT_RECURRING_FORMATS:
        recurring_format = RecurringFormat(
            name=fmt_data["name"],
            description=fmt_data["description"],
            frequency=fmt_data["frequency"],
            preferred_day=fmt_data["preferred_day"],
            preferred_time=fmt_data["preferred_time"],
            tone=fmt_data["tone"],
            hashtags=fmt_data["hashtags"],
            icon=fmt_data["icon"],
            category=fmt_data["category"],
            is_active=fmt_data["is_active"],
            is_default=fmt_data["is_default"],
            user_id=None,  # System defaults have no user
        )
        session.add(recurring_format)
        count += 1

    await session.commit()
    logger.info(f"Seeded {count} recurring formats")
    return count
