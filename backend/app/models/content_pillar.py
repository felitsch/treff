"""Content Pillar model.

Represents a content strategy pillar (e.g., 'Erfahrungsberichte', 'Laender-Spotlights')
that categorizes posts for distribution tracking and AI content generation context.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Integer, String, DateTime, Text, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ContentPillar(Base):
    __tablename__ = "content_pillars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pillar_id: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)  # e.g. 'erfahrungsberichte'
    name: Mapped[str] = mapped_column(String, nullable=False)  # e.g. 'Erfahrungsberichte & Testimonials'
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)  # e.g. 30.0 for 30%
    color: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # e.g. '#E74C3C'
    icon: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # emoji icon
    buyer_journey_stages: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array: ["awareness","consideration"]
    platforms: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array: ["instagram_feed","tiktok"]
    formats: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array: ["Carousel","Reel"]
    example_topics: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    kpis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array: ["Saves","Shares"]
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
