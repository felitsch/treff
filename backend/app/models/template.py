"""Template model."""

from datetime import datetime, timezone
from sqlalchemy import Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Template(Base):
    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    platform_format: Mapped[str] = mapped_column(String, nullable=False)  # feed_square, feed_portrait, story, tiktok
    slide_count: Mapped[int] = mapped_column(Integer, default=1)
    html_content: Mapped[str] = mapped_column(Text, nullable=False)
    css_content: Mapped[str] = mapped_column(Text, nullable=False)
    default_colors: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    default_fonts: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    placeholder_fields: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array
    thumbnail_url: Mapped[str | None] = mapped_column(String, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_country_themed: Mapped[bool] = mapped_column(Boolean, default=False)
    country: Mapped[str | None] = mapped_column(String, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    parent_template_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
