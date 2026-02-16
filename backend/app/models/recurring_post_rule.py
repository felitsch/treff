"""Recurring Post Rule model.

Stores the recurrence rule for a template post that should repeat
on a schedule (weekly, biweekly, monthly). The system generates
concrete Post instances based on these rules.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RecurringPostRule(Base):
    __tablename__ = "recurring_post_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    # Source post that serves as the template
    source_post_id: Mapped[int] = mapped_column(Integer, ForeignKey("posts.id"), nullable=False)

    # Recurrence config
    frequency: Mapped[str] = mapped_column(String, nullable=False)  # weekly, biweekly, monthly
    weekday: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 0=Mon, 6=Sun (for weekly/biweekly)
    day_of_month: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-28 (for monthly)
    time: Mapped[str] = mapped_column(String, default="10:00")  # HH:MM

    # End condition: either end_date OR max_occurrences (whichever first)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    max_occurrences: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # State
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    generated_count: Mapped[int] = mapped_column(Integer, default=0)  # How many instances generated
    last_generated_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user = relationship("User")
    source_post = relationship("Post", foreign_keys=[source_post_id])
