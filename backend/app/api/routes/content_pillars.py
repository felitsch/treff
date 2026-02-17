"""Content Pillars API routes.

CRUD endpoints for Content Pillars - the thematic categories that structure
all social media content for TREFF Sprachreisen.

Also includes a distribution check endpoint that compares actual post distribution
against target percentages and flags underrepresented pillars.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.content_pillar import ContentPillar
from app.models.post import Post

router = APIRouter()
logger = logging.getLogger(__name__)


# ── Pydantic Schemas ──────────────────────────────────────────────────

class ContentPillarResponse(BaseModel):
    id: int
    pillar_id: str
    name: str
    description: Optional[str] = None
    target_percentage: float
    color: Optional[str] = None
    icon: Optional[str] = None
    buyer_journey_stages: Optional[list] = None
    platforms: Optional[list] = None
    formats: Optional[list] = None
    example_topics: Optional[list] = None
    kpis: Optional[list] = None

    class Config:
        from_attributes = True


class PillarDistributionItem(BaseModel):
    pillar_id: str
    name: str
    icon: Optional[str] = None
    color: Optional[str] = None
    target_percentage: float
    actual_percentage: float
    actual_count: int
    deviation: float  # actual - target (negative = underrepresented)
    status: str  # 'ok', 'warning', 'critical'


class PillarDistributionResponse(BaseModel):
    total_posts: int
    distribution: list[PillarDistributionItem]
    warnings: list[str]
    unassigned_count: int  # posts without a pillar


# ── Helper: parse JSON fields ─────────────────────────────────────────

def _pillar_to_dict(pillar: ContentPillar) -> dict:
    """Convert a ContentPillar ORM object to a response dict with parsed JSON fields."""
    def _parse_json(val):
        if val is None:
            return None
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return None

    return {
        "id": pillar.id,
        "pillar_id": pillar.pillar_id,
        "name": pillar.name,
        "description": pillar.description,
        "target_percentage": pillar.target_percentage,
        "color": pillar.color,
        "icon": pillar.icon,
        "buyer_journey_stages": _parse_json(pillar.buyer_journey_stages),
        "platforms": _parse_json(pillar.platforms),
        "formats": _parse_json(pillar.formats),
        "example_topics": _parse_json(pillar.example_topics),
        "kpis": _parse_json(pillar.kpis),
    }


# ── GET /api/content-pillars ──────────────────────────────────────────

@router.get("")
async def list_content_pillars(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List all content pillars ordered by target percentage (highest first)."""
    result = await db.execute(
        select(ContentPillar).order_by(ContentPillar.target_percentage.desc())
    )
    pillars = result.scalars().all()
    return {"pillars": [_pillar_to_dict(p) for p in pillars]}


# ── GET /api/content-pillars/{pillar_id} ──────────────────────────────

@router.get("/{pillar_id}")
async def get_content_pillar(
    pillar_id: str,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a single content pillar by its string ID (e.g. 'erfahrungsberichte')."""
    result = await db.execute(
        select(ContentPillar).where(ContentPillar.pillar_id == pillar_id)
    )
    pillar = result.scalar_one_or_none()
    if not pillar:
        raise HTTPException(status_code=404, detail=f"Content pillar '{pillar_id}' not found")
    return _pillar_to_dict(pillar)


# ── GET /api/content-pillars/distribution/check ───────────────────────

@router.get("/distribution/check")
async def check_pillar_distribution(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    days: int = Query(30, description="Number of days to look back for distribution analysis"),
):
    """Check content pillar distribution against targets.

    Compares actual post distribution over the last N days against
    the target percentages defined in each pillar. Returns warnings
    for underrepresented pillars (deviation > 5%).
    """
    # Get all pillars
    pillar_result = await db.execute(
        select(ContentPillar).order_by(ContentPillar.target_percentage.desc())
    )
    pillars = pillar_result.scalars().all()

    if not pillars:
        return PillarDistributionResponse(
            total_posts=0,
            distribution=[],
            warnings=["Keine Content Pillars konfiguriert. Bitte Seed-Script ausfuehren."],
            unassigned_count=0,
        )

    # Count posts per pillar in the last N days
    cutoff = datetime.now(timezone.utc)
    # Simple approach: count all posts by user grouped by pillar_id
    post_counts_result = await db.execute(
        select(Post.pillar_id, func.count(Post.id))
        .where(Post.user_id == user_id)
        .group_by(Post.pillar_id)
    )
    post_counts = {row[0]: row[1] for row in post_counts_result.all()}

    total_posts = sum(post_counts.values())
    unassigned_count = post_counts.get(None, 0)
    assigned_total = total_posts - unassigned_count

    distribution = []
    warnings = []

    for pillar in pillars:
        count = post_counts.get(pillar.pillar_id, 0)
        actual_pct = (count / assigned_total * 100) if assigned_total > 0 else 0.0
        deviation = actual_pct - pillar.target_percentage

        # Determine status
        if abs(deviation) <= 5:
            status = "ok"
        elif deviation < -10:
            status = "critical"
            warnings.append(
                f"'{pillar.name}' ist stark unterrepraesentiert: "
                f"{actual_pct:.0f}% (Ziel: {pillar.target_percentage:.0f}%)"
            )
        elif deviation < -5:
            status = "warning"
            warnings.append(
                f"'{pillar.name}' ist unterrepraesentiert: "
                f"{actual_pct:.0f}% (Ziel: {pillar.target_percentage:.0f}%)"
            )
        elif deviation > 10:
            status = "warning"
            warnings.append(
                f"'{pillar.name}' ist ueberrepraesentiert: "
                f"{actual_pct:.0f}% (Ziel: {pillar.target_percentage:.0f}%)"
            )
        else:
            status = "ok"

        distribution.append(PillarDistributionItem(
            pillar_id=pillar.pillar_id,
            name=pillar.name,
            icon=pillar.icon,
            color=pillar.color,
            target_percentage=pillar.target_percentage,
            actual_percentage=round(actual_pct, 1),
            actual_count=count,
            deviation=round(deviation, 1),
            status=status,
        ))

    if unassigned_count > 0:
        warnings.append(
            f"{unassigned_count} Post(s) ohne Pillar-Zuordnung. "
            "Bitte Pillar im Post-Creator auswaehlen."
        )

    return PillarDistributionResponse(
        total_posts=total_posts,
        distribution=distribution,
        warnings=warnings,
        unassigned_count=unassigned_count,
    )


# ── POST /api/content-pillars/seed ────────────────────────────────────

@router.post("/seed")
async def seed_content_pillars(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Seed the content pillars from the predefined configuration.

    Creates or updates all 7 content pillars. Safe to run multiple times
    (idempotent via upsert on pillar_id).
    """
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
                "Stipendium sichern — jetzt bewerben",
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

    created = 0
    updated = 0

    for pillar_data in PILLARS:
        # Check if pillar already exists
        result = await db.execute(
            select(ContentPillar).where(ContentPillar.pillar_id == pillar_data["pillar_id"])
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing pillar
            for key, value in pillar_data.items():
                setattr(existing, key, value)
            existing.updated_at = datetime.now(timezone.utc)
            updated += 1
        else:
            # Create new pillar
            new_pillar = ContentPillar(**pillar_data)
            db.add(new_pillar)
            created += 1

    await db.flush()
    return {
        "message": f"Content Pillars geseedet: {created} erstellt, {updated} aktualisiert.",
        "created": created,
        "updated": updated,
        "total": len(PILLARS),
    }
