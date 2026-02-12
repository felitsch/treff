"""PostSlide model."""

from sqlalchemy import Integer, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PostSlide(Base):
    __tablename__ = "post_slides"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    slide_index: Mapped[int] = mapped_column(Integer, nullable=False)
    headline: Mapped[str | None] = mapped_column(Text, nullable=True)
    subheadline: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    bullet_points: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array
    quote_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    quote_author: Mapped[str | None] = mapped_column(String, nullable=True)
    cta_text: Mapped[str | None] = mapped_column(String, nullable=True)
    image_asset_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("assets.id"), nullable=True)
    background_type: Mapped[str | None] = mapped_column(String, nullable=True)  # color, image, ai_generated
    background_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    custom_css_overrides: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    # Relationships
    post = relationship("Post", back_populates="slides")
