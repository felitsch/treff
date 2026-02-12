"""Post model."""

from datetime import datetime, timezone
from sqlalchemy import Integer, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Post(Base):
    __tablename__ = "posts"
    __table_args__ = (
        Index("ix_posts_user_id", "user_id"),
        Index("ix_posts_user_id_created_at", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    template_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("templates.id"), nullable=True)
    category: Mapped[str] = mapped_column(String, nullable=False)
    country: Mapped[str | None] = mapped_column(String, nullable=True)
    platform: Mapped[str] = mapped_column(String, nullable=False)  # instagram_feed, instagram_story, tiktok
    status: Mapped[str] = mapped_column(String, default="draft")  # draft, scheduled, reminded, exported, posted
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    slide_data: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # JSON
    caption_instagram: Mapped[str | None] = mapped_column(Text, nullable=True)
    caption_tiktok: Mapped[str | None] = mapped_column(Text, nullable=True)
    hashtags_instagram: Mapped[str | None] = mapped_column(Text, nullable=True)
    hashtags_tiktok: Mapped[str | None] = mapped_column(Text, nullable=True)
    cta_text: Mapped[str | None] = mapped_column(String, nullable=True)
    custom_colors: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    custom_fonts: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    tone: Mapped[str] = mapped_column(String, default="jugendlich")  # jugendlich, serioess
    scheduled_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    scheduled_time: Mapped[str | None] = mapped_column(String, nullable=True)  # HH:MM
    exported_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user = relationship("User", back_populates="posts")
    slides = relationship("PostSlide", back_populates="post", cascade="all, delete-orphan", order_by="PostSlide.slide_index")
    calendar_entries = relationship("CalendarEntry", back_populates="post", cascade="all, delete-orphan")
    export_records = relationship("ExportHistory", back_populates="post", cascade="all, delete-orphan")
