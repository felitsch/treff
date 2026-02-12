"""ContentSuggestion model."""

from datetime import datetime, timezone, date
from sqlalchemy import Integer, String, Date, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ContentSuggestion(Base):
    __tablename__ = "content_suggestions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    suggestion_type: Mapped[str] = mapped_column(String, nullable=False)  # weekly_plan, gap_fill, seasonal, country_rotation, category_balance
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggested_category: Mapped[str | None] = mapped_column(String, nullable=True)
    suggested_country: Mapped[str | None] = mapped_column(String, nullable=True)
    suggested_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending")  # pending, accepted, dismissed
    accepted_post_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("posts.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
