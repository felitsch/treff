"""HashtagSet model for managing hashtag collections per country/category."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class HashtagSet(Base):
    """A named collection of hashtags grouped by category and country.

    Used for strategic hashtag management:
    - Predefined sets per country (e.g., #HighSchoolUSA, #AustauschjahrUSA)
    - Custom sets per campaign or theme
    - Performance tracking scores
    """

    __tablename__ = "hashtag_sets"
    __table_args__ = (
        Index("ix_hashtag_sets_user_id", "user_id"),
        Index("ix_hashtag_sets_category", "category"),
        Index("ix_hashtag_sets_country", "country"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=True)  # NULL = system default
    name: Mapped[str] = mapped_column(String, nullable=False)
    hashtags: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array of hashtag strings
    category: Mapped[str | None] = mapped_column(String, nullable=True)  # e.g., "laender_spotlight", "allgemein"
    country: Mapped[str | None] = mapped_column(String, nullable=True)  # e.g., "usa", "canada"
    performance_score: Mapped[float] = mapped_column(Float, default=0.0)
    is_default: Mapped[int] = mapped_column(Integer, default=0)  # 1 = system default set

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
