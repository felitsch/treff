"""CTA (Call-to-Action) model for the CTA library."""

from datetime import datetime, timezone
from sqlalchemy import Integer, String, DateTime, Text, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CTA(Base):
    __tablename__ = "ctas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    text: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)  # engagement, conversion, awareness, traffic
    platform: Mapped[str] = mapped_column(String, nullable=False, default="both")  # instagram, tiktok, both
    format: Mapped[str] = mapped_column(String, nullable=False, default="all")  # feed, story, reel, all
    emoji: Mapped[str | None] = mapped_column(String, nullable=True)
    performance_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_default: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 1 = seeded default, 0 = user-created
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
