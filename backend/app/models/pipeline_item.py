"""PipelineItem model - Student Content Inbox for the Smart Content Pipeline."""

from datetime import datetime, timezone
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PipelineItem(Base):
    __tablename__ = "pipeline_items"
    __table_args__ = (
        Index("ix_pipeline_items_user_id", "user_id"),
        Index("ix_pipeline_items_status", "status"),
        Index("ix_pipeline_items_student_id", "student_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    student_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("students.id", ondelete="SET NULL"), nullable=True)
    asset_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("assets.id", ondelete="SET NULL"), nullable=True)

    # Content analysis results (JSON)
    suggested_post_type: Mapped[str | None] = mapped_column(String, nullable=True)  # instagram_feed, instagram_story, tiktok, carousel
    suggested_caption_seeds: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array of caption seed strings
    suggested_platforms: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array of platform strings
    detected_country: Mapped[str | None] = mapped_column(String, nullable=True)  # usa, kanada, australien, neuseeland, irland
    analysis_summary: Mapped[str | None] = mapped_column(Text, nullable=True)  # AI-generated description of the media content

    # Status tracking
    status: Mapped[str] = mapped_column(String, default="pending")  # pending, analyzed, processing, processed, failed
    result_post_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("posts.id", ondelete="SET NULL"), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Metadata
    source_description: Mapped[str | None] = mapped_column(Text, nullable=True)  # Optional text context from student
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    student = relationship("Student", foreign_keys=[student_id])
    asset = relationship("Asset", foreign_keys=[asset_id])
    result_post = relationship("Post", foreign_keys=[result_post_id])
