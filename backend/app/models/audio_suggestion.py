"""AudioSuggestion model - Trending audio & music recommendations for Reels/TikTok.

Stores curated audio/music suggestions categorized by mood, platform,
tempo and content pillar suitability. No actual audio files - only
recommendations and platform links.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Integer, String, Text, DateTime, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AudioSuggestion(Base):
    """Curated audio/music recommendation for video content.

    Each suggestion includes mood, tempo, platform suitability and
    content pillar matching to help the social media manager pick
    the right trending audio for their Reels/TikTok videos.
    """

    __tablename__ = "audio_suggestions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    artist: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    platform: Mapped[str] = mapped_column(
        String(50), nullable=False, default="both"
    )  # tiktok, instagram, both
    mood: Mapped[str] = mapped_column(
        String(50), nullable=False, default="energetic"
    )  # energetic, emotional, funny, chill, dramatic
    tempo: Mapped[str] = mapped_column(
        String(20), nullable=False, default="medium"
    )  # slow, medium, fast
    trending_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=5.0
    )  # 1.0-10.0
    url_hint: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )  # Link to the platform where the audio can be found
    suitable_for: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON array: ["laender_spotlight", "erfahrungsberichte", ...]
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_royalty_free: Mapped[bool] = mapped_column(Boolean, default=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # null = system/seed data

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
