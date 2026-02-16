"""CampaignPost model — links a campaign to individual posts with ordering."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CampaignPost(Base):
    __tablename__ = "campaign_posts"
    __table_args__ = (
        Index("ix_campaign_posts_campaign_id", "campaign_id"),
        Index("ix_campaign_posts_post_id", "post_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    post_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("posts.id", ondelete="SET NULL"), nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0)
    scheduled_date: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # ISO date string
    status: Mapped[str] = mapped_column(String, default="planned")  # planned, draft_created, scheduled, posted
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    campaign = relationship("Campaign", back_populates="campaign_posts")
    post = relationship("Post", foreign_keys=[post_id])
