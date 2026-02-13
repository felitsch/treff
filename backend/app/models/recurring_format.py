"""RecurringFormat model for recurring content formats (Running Gags, weekly themes)."""

from datetime import datetime, timezone
from sqlalchemy import Integer, String, DateTime, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RecurringFormat(Base):
    __tablename__ = "recurring_formats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    frequency: Mapped[str] = mapped_column(String, nullable=False, default="weekly")  # daily, weekly, biweekly, monthly
    preferred_day: Mapped[str] = mapped_column(String, nullable=True)  # Montag, Dienstag, etc. (for weekly/biweekly)
    preferred_time: Mapped[str] = mapped_column(String, nullable=True)  # HH:MM format
    tone: Mapped[str] = mapped_column(String, nullable=True)  # jugendlich, witzig, emotional, etc.
    template_id: Mapped[int] = mapped_column(Integer, nullable=True)  # optional link to a template
    hashtags: Mapped[str] = mapped_column(Text, nullable=True)  # JSON array of hashtags
    icon: Mapped[str] = mapped_column(String, nullable=True)  # emoji icon for UI
    category: Mapped[str] = mapped_column(String, nullable=True)  # post category mapping
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)  # system default vs user-created
    user_id: Mapped[int] = mapped_column(Integer, nullable=True)  # NULL for system defaults
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
