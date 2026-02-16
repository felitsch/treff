"""ContentSuggestion model."""

from datetime import datetime, timezone, date
from typing import Optional
from sqlalchemy import Integer, String, Date, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ContentSuggestion(Base):
    __tablename__ = "content_suggestions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    suggestion_type: Mapped[str] = mapped_column(String, nullable=False)  # weekly_plan, gap_fill, seasonal, country_rotation, category_balance
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    suggested_category: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    suggested_country: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    suggested_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    suggested_format: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # instagram_feed, instagram_story, tiktok, carousel
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending")  # pending, accepted, dismissed
    accepted_post_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("posts.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
