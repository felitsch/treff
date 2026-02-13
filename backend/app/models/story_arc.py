"""StoryArc model - multi-part story series about a student or theme."""

from datetime import datetime, timezone
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class StoryArc(Base):
    __tablename__ = "story_arcs"
    __table_args__ = (
        Index("ix_story_arcs_user_id", "user_id"),
        Index("ix_story_arcs_student_id", "student_id"),
        Index("ix_story_arcs_country", "country"),
        Index("ix_story_arcs_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    student_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("students.id"), nullable=True)
    country: Mapped[str | None] = mapped_column(String, nullable=True)  # usa, kanada, australien, neuseeland, irland
    status: Mapped[str] = mapped_column(String, default="draft")  # draft, active, paused, completed
    planned_episodes: Mapped[int] = mapped_column(Integer, default=8)
    current_episode: Mapped[int] = mapped_column(Integer, default=0)
    cover_image_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("assets.id"), nullable=True)
    tone: Mapped[str] = mapped_column(String, default="jugendlich")  # jugendlich, serioess
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user = relationship("User", back_populates="story_arcs")
    student = relationship("Student", back_populates="story_arcs")
    cover_image = relationship("Asset", foreign_keys=[cover_image_id])
