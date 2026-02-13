"""Seed predefined hashtag sets for TREFF Sprachreisen.

Provides country-specific, category-specific, and campaign hashtag collections.
"""

import json
import logging

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hashtag_set import HashtagSet

logger = logging.getLogger(__name__)

# Predefined hashtag sets organized by country and category
DEFAULT_HASHTAG_SETS = [
    # ═══════════════════════════════════════════════════
    # ALLGEMEIN (brand + general)
    # ═══════════════════════════════════════════════════
    {
        "name": "TREFF Brand Basics",
        "hashtags": [
            "#TREFFSprachreisen", "#Auslandsjahr", "#Highschool",
            "#GapYear", "#Austauschschueler", "#Sprachreise",
            "#StudyAbroad", "#HighSchoolAbroad", "#Schueleraustausch"
        ],
        "category": "allgemein",
        "country": None,
        "performance_score": 9.0,
    },
    {
        "name": "Engagement Booster",
        "hashtags": [
            "#Fernweh", "#Abenteuer", "#TraumErfuellen",
            "#NewAdventure", "#LifeChanging", "#BestTimeOfMyLife",
            "#MakingMemories", "#OnceInALifetime"
        ],
        "category": "allgemein",
        "country": None,
        "performance_score": 7.5,
    },
    {
        "name": "Eltern & Vertrauen",
        "hashtags": [
            "#TREFFSprachreisen", "#SicherImAusland", "#ElternRatgeber",
            "#Seit1984", "#ErfahrungZaehlt", "#Qualitaet",
            "#Gastfamilie", "#Betreuung"
        ],
        "category": "allgemein",
        "country": None,
        "performance_score": 6.5,
    },
    # ═══════════════════════════════════════════════════
    # USA
    # ═══════════════════════════════════════════════════
    {
        "name": "USA Allgemein",
        "hashtags": [
            "#TREFFSprachreisen", "#HighSchoolUSA", "#AustauschjahrUSA",
            "#AmericanHighSchool", "#USAExchange", "#AmericanDream",
            "#HighSchoolLife", "#USAAustausch"
        ],
        "category": "laender_spotlight",
        "country": "usa",
        "performance_score": 8.5,
    },
    {
        "name": "USA Erfahrungsberichte",
        "hashtags": [
            "#TREFFSprachreisen", "#MeinAuslandsjahr", "#HighSchoolUSA",
            "#Gastfamilie", "#AmericanLife", "#SchoolSpirit",
            "#Prom", "#Homecoming"
        ],
        "category": "erfahrungsberichte",
        "country": "usa",
        "performance_score": 8.0,
    },
    {
        "name": "USA Fristen & CTA",
        "hashtags": [
            "#TREFFSprachreisen", "#JetztBewerben", "#HighSchoolUSA",
            "#Bewerbungsfrist", "#TraumVerwirklichen", "#AuslandsjahrPlanen",
            "#USAClassic", "#USASelect"
        ],
        "category": "fristen_cta",
        "country": "usa",
        "performance_score": 7.0,
    },
    # ═══════════════════════════════════════════════════
    # KANADA
    # ═══════════════════════════════════════════════════
    {
        "name": "Kanada Allgemein",
        "hashtags": [
            "#TREFFSprachreisen", "#HighSchoolKanada", "#AustauschjahrKanada",
            "#CanadaExchange", "#KanadaAustausch", "#OhCanada",
            "#StudyInCanada", "#CanadianHighSchool"
        ],
        "category": "laender_spotlight",
        "country": "canada",
        "performance_score": 8.0,
    },
    {
        "name": "Kanada Erfahrungsberichte",
        "hashtags": [
            "#TREFFSprachreisen", "#MeinAuslandsjahr", "#KanadaAustausch",
            "#CanadianLife", "#Bilingue", "#RockyMountains",
            "#Hockey", "#Poutine"
        ],
        "category": "erfahrungsberichte",
        "country": "canada",
        "performance_score": 7.5,
    },
    # ═══════════════════════════════════════════════════
    # AUSTRALIEN
    # ═══════════════════════════════════════════════════
    {
        "name": "Australien Allgemein",
        "hashtags": [
            "#TREFFSprachreisen", "#HighSchoolAustralien", "#AustauschjahrAustralien",
            "#AustraliaExchange", "#DownUnder", "#AustralienAustausch",
            "#StudyInAustralia", "#AussieLife"
        ],
        "category": "laender_spotlight",
        "country": "australia",
        "performance_score": 8.0,
    },
    {
        "name": "Australien Erfahrungsberichte",
        "hashtags": [
            "#TREFFSprachreisen", "#MeinAuslandsjahr", "#AustralienAustausch",
            "#SurfLife", "#GreatBarrierReef", "#AussieAdventure",
            "#SchoolUniform", "#BeachLife"
        ],
        "category": "erfahrungsberichte",
        "country": "australia",
        "performance_score": 7.5,
    },
    # ═══════════════════════════════════════════════════
    # NEUSEELAND
    # ═══════════════════════════════════════════════════
    {
        "name": "Neuseeland Allgemein",
        "hashtags": [
            "#TREFFSprachreisen", "#HighSchoolNeuseeland", "#AustauschjahrNeuseeland",
            "#NewZealandExchange", "#NZAustausch", "#KiwiLife",
            "#StudyInNZ", "#Aotearoa"
        ],
        "category": "laender_spotlight",
        "country": "newzealand",
        "performance_score": 7.5,
    },
    {
        "name": "Neuseeland Erfahrungsberichte",
        "hashtags": [
            "#TREFFSprachreisen", "#MeinAuslandsjahr", "#NeuseelandAustausch",
            "#MaoriCulture", "#Haka", "#NZAdventure",
            "#MiddleEarth", "#OutdoorNZ"
        ],
        "category": "erfahrungsberichte",
        "country": "newzealand",
        "performance_score": 7.0,
    },
    # ═══════════════════════════════════════════════════
    # IRLAND
    # ═══════════════════════════════════════════════════
    {
        "name": "Irland Allgemein",
        "hashtags": [
            "#TREFFSprachreisen", "#HighSchoolIrland", "#AustauschjahrIrland",
            "#IrelandExchange", "#IrlandAustausch", "#EmeraldIsle",
            "#StudyInIreland", "#IrishLife"
        ],
        "category": "laender_spotlight",
        "country": "ireland",
        "performance_score": 7.5,
    },
    {
        "name": "Irland Erfahrungsberichte",
        "hashtags": [
            "#TREFFSprachreisen", "#MeinAuslandsjahr", "#IrlandAustausch",
            "#IrishCulture", "#GreenIsland", "#Dublin",
            "#IrishFriendliness", "#CelticSpirit"
        ],
        "category": "erfahrungsberichte",
        "country": "ireland",
        "performance_score": 7.0,
    },
    # ═══════════════════════════════════════════════════
    # CATEGORY-SPECIFIC (no country)
    # ═══════════════════════════════════════════════════
    {
        "name": "FAQ & Wissen",
        "hashtags": [
            "#TREFFSprachreisen", "#AuslandsjahrFAQ", "#GutZuWissen",
            "#FragenUndAntworten", "#Austauschtipps", "#Wissenswertes",
            "#ElternFragen", "#SchuelerFragen"
        ],
        "category": "faq",
        "country": None,
        "performance_score": 6.0,
    },
    {
        "name": "Tipps & Tricks",
        "hashtags": [
            "#TREFFSprachreisen", "#AuslandsjahrTipps", "#PacklisteTipps",
            "#Vorbereitung", "#AustauschTipps", "#LifeHacks",
            "#GastfamilienTipps", "#SchuleTipps"
        ],
        "category": "tipps_tricks",
        "country": None,
        "performance_score": 6.5,
    },
    {
        "name": "Infografiken & Zahlen",
        "hashtags": [
            "#TREFFSprachreisen", "#Infografik", "#FaktenCheck",
            "#WusstestDu", "#Statistik", "#Auslandsjahr",
            "#Vergleich", "#ZahlenUndFakten"
        ],
        "category": "infografiken",
        "country": None,
        "performance_score": 5.5,
    },
]


async def seed_hashtag_sets(session: AsyncSession) -> int:
    """Seed default hashtag sets if none exist.

    Returns the number of sets created.
    """
    # Check if any default sets already exist
    result = await session.execute(
        select(func.count(HashtagSet.id)).where(HashtagSet.is_default == 1)
    )
    existing_count = result.scalar_one()

    if existing_count > 0:
        logger.info("Hashtag sets already seeded (%d existing), skipping.", existing_count)
        return 0

    count = 0
    for set_data in DEFAULT_HASHTAG_SETS:
        hashtag_set = HashtagSet(
            user_id=None,  # System defaults have no user
            name=set_data["name"],
            hashtags=json.dumps(set_data["hashtags"]),
            category=set_data.get("category"),
            country=set_data.get("country"),
            performance_score=set_data.get("performance_score", 0.0),
            is_default=1,
        )
        session.add(hashtag_set)
        count += 1

    await session.commit()
    logger.info("Seeded %d default hashtag sets.", count)
    return count
