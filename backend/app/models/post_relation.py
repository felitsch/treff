"""PostRelation model - Many-to-Many relationship between posts for cross-post linking."""

from datetime import datetime, timezone
from sqlalchemy import Integer, String, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PostRelation(Base):
    """Links two posts together with a relationship type.

    Used for:
    - Feed posts teasing Story series ("Schau in unsere Stories!")
    - Story posts referencing feed content
    - Thematic cross-references between posts
    - Sequel/continuation links between episodes
    """
    __tablename__ = "post_relations"
    __table_args__ = (
        Index("ix_post_relations_source_id", "source_post_id"),
        Index("ix_post_relations_target_id", "target_post_id"),
        UniqueConstraint("source_post_id", "target_post_id", name="uq_post_relation_pair"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_post_id: Mapped[int] = mapped_column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    target_post_id: Mapped[int] = mapped_column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    relation_type: Mapped[str] = mapped_column(
        String, nullable=False, default="cross_reference"
    )  # story_teaser, cross_reference, sequel, related
    note: Mapped[str | None] = mapped_column(String, nullable=True)  # Optional user note about the relationship
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    source_post = relationship("Post", foreign_keys=[source_post_id])
    target_post = relationship("Post", foreign_keys=[target_post_id])
