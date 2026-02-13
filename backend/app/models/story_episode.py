"""StoryEpisode model - individual episodes within a Story Arc, linked to Posts."""

from datetime import datetime, timezone
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class StoryEpisode(Base):
    __tablename__ = "story_episodes"
    __table_args__ = (
        Index("ix_story_episodes_arc_id", "arc_id"),
        Index("ix_story_episodes_post_id", "post_id"),
        Index("ix_story_episodes_arc_id_episode_number", "arc_id", "episode_number"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    arc_id: Mapped[int] = mapped_column(Integer, ForeignKey("story_arcs.id"), nullable=False)
    post_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("posts.id"), nullable=True)
    episode_number: Mapped[int] = mapped_column(Integer, nullable=False)
    episode_title: Mapped[str] = mapped_column(String, nullable=False)
    teaser_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    cliffhanger_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    previously_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_episode_hint: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, default="planned")  # planned, draft, published
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    arc = relationship("StoryArc", back_populates="episodes")
    post = relationship("Post", back_populates="story_episode", foreign_keys=[post_id])
