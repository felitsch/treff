"""Post model."""

from datetime import datetime, timezone
from typing import Optional
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
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    template_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("templates.id"), nullable=True)
    category: Mapped[str] = mapped_column(String, nullable=False)
    country: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    platform: Mapped[str] = mapped_column(String, nullable=False)  # instagram_feed, instagram_story, tiktok
    status: Mapped[str] = mapped_column(String, default="draft")  # draft, scheduled, reminded, exported, posted
    title: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    slide_data: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # JSON
    caption_instagram: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    caption_tiktok: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hashtags_instagram: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hashtags_tiktok: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cta_text: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    custom_colors: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    custom_fonts: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    tone: Mapped[str] = mapped_column(String, default="jugendlich")  # jugendlich, serioess, witzig, emotional, motivierend, informativ, behind-the-scenes, storytelling, provokant, wholesome
    scheduled_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    scheduled_time: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # HH:MM
    story_arc_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("story_arcs.id"), nullable=True)  # Links teaser posts to story arcs
    episode_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Explicit episode ordering within a story arc (1-based)
    student_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("students.id", ondelete="SET NULL"), nullable=True)  # Links post to a student profile
    linked_post_group_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # UUID grouping sibling posts across platforms
    recurring_rule_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("recurring_post_rules.id", ondelete="SET NULL"), nullable=True)  # Links to recurrence rule
    is_recurring_instance: Mapped[Optional[bool]] = mapped_column(Integer, nullable=True, default=None)  # True if auto-generated from rule
    pillar_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Content pillar ID (e.g. 'erfahrungsberichte', 'laender_spotlight')
    hook_formula: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Hook formula ID from hookFormulas.js (e.g. 'knowledge_gap', 'myth_buster', 'pov')
    # Performance metrics (manually entered social media stats)
    perf_likes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    perf_comments: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    perf_shares: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    perf_saves: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    perf_reach: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    perf_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    exported_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
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
    student = relationship("Student", foreign_keys=[student_id])
    story_arc = relationship("StoryArc", foreign_keys=[story_arc_id])
    story_episode = relationship("StoryEpisode", back_populates="post", uselist=False, foreign_keys="StoryEpisode.post_id")
    slides = relationship("PostSlide", back_populates="post", cascade="all, delete-orphan", order_by="PostSlide.slide_index")
    calendar_entries = relationship("CalendarEntry", back_populates="post", cascade="all, delete-orphan")
    export_records = relationship("ExportHistory", back_populates="post", cascade="all, delete-orphan")
    interactive_elements = relationship("PostInteractiveElement", back_populates="post", cascade="all, delete-orphan")
