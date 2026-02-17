"""ShotList model - Filming guides for students abroad.

Links to students and optionally to video scripts. Contains structured
shot instructions that students can follow on their phones.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class ShotList(Base):
    """A filming guide / shot list for a student abroad.

    Contains a list of concrete filming instructions (shots) that students
    can follow on their phones. Each shot has a description, example,
    duration hint, orientation tip, and lighting guidance.
    """
    __tablename__ = "shot_lists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Link to student
    student_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("students.id", ondelete="SET NULL"), nullable=True, index=True
    )
    student_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Country context
    country: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Content type classification
    content_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="general"
    )
    # arrival_story, first_day, school_day, host_family, cultural_moment,
    # holiday, school_event, farewell, alumni, general

    # Shots stored as JSON array
    shots: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Each shot: {shot_number, description_for_student, example, duration_hint,
    #             orientation, lighting_tip, content_pillar}

    # Scheduling
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    season: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )
    # active, completed, archived

    # Optional link to video script (V-06)
    video_script_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("video_scripts.id", ondelete="SET NULL"), nullable=True
    )

    # Share link for students (public token)
    share_token: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, unique=True)
    is_shared: Mapped[bool] = mapped_column(Boolean, default=False)

    # Tracking
    shots_completed: Mapped[int] = mapped_column(Integer, default=0)
    shots_total: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
