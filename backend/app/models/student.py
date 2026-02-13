"""Student model - central entity for story series content."""

from datetime import datetime, timezone
from sqlalchemy import Integer, String, Text, DateTime, Date, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Student(Base):
    __tablename__ = "students"
    __table_args__ = (
        Index("ix_students_user_id", "user_id"),
        Index("ix_students_country", "country"),
        Index("ix_students_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    country: Mapped[str] = mapped_column(String, nullable=False)  # usa, kanada, australien, neuseeland, irland
    city: Mapped[str | None] = mapped_column(String, nullable=True)
    school_name: Mapped[str | None] = mapped_column(String, nullable=True)
    host_family_name: Mapped[str | None] = mapped_column(String, nullable=True)
    start_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    profile_image_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("assets.id"), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    fun_facts: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array of strings
    status: Mapped[str] = mapped_column(String, default="active")  # active, completed, upcoming
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user = relationship("User", back_populates="students")
    profile_image = relationship("Asset", foreign_keys=[profile_image_id])
    story_arcs = relationship("StoryArc", back_populates="student")
