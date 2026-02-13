"""SeriesReminder model - notifications for story series scheduling."""

from datetime import datetime, timezone
from sqlalchemy import Integer, String, Text, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SeriesReminder(Base):
    __tablename__ = "series_reminders"
    __table_args__ = (
        Index("ix_series_reminders_user_id", "user_id"),
        Index("ix_series_reminders_story_arc_id", "story_arc_id"),
        Index("ix_series_reminders_type", "reminder_type"),
        Index("ix_series_reminders_is_read", "is_read"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    story_arc_id: Mapped[int] = mapped_column(Integer, ForeignKey("story_arcs.id"), nullable=False)
    # Types: upcoming_episode, series_paused, series_ending, gap_warning
    reminder_type: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user = relationship("User")
    story_arc = relationship("StoryArc")
