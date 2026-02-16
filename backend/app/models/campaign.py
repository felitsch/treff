"""Campaign model — marketing campaign grouping posts around a specific goal."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Integer, String, DateTime, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Campaign(Base):
    __tablename__ = "campaigns"
    __table_args__ = (
        Index("ix_campaigns_user_id", "user_id"),
        Index("ix_campaigns_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    goal: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # awareness, engagement, conversion, traffic
    start_date: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # ISO date string
    end_date: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # ISO date string
    platforms: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array: ["instagram_feed","tiktok"]
    status: Mapped[str] = mapped_column(String, default="draft")  # draft, active, completed
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    campaign_posts = relationship("CampaignPost", back_populates="campaign", cascade="all, delete-orphan", order_by="CampaignPost.order")
