"""MusicTrack model - Royalty-free music library for video audio layers."""

from datetime import datetime, timezone
from sqlalchemy import Integer, String, Text, DateTime, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MusicTrack(Base):
    __tablename__ = "music_tracks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    category: Mapped[str] = mapped_column(String, nullable=False)  # upbeat, emotional, chill, dramatic, inspirational, fun
    mood: Mapped[str | None] = mapped_column(String, nullable=True)  # happy, sad, energetic, calm, epic, playful
    bpm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
