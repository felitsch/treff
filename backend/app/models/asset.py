"""Asset model."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    original_filename: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    file_type: Mapped[str] = mapped_column(String, nullable=False)  # image/jpeg, image/png, image/webp, video/mp4, video/quicktime, video/webm
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source: Mapped[str] = mapped_column(String, default="upload")  # upload, ai_generated, stock_unsplash, stock_pexels, system
    ai_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # country, logo, background, photo, icon, video
    country: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    file_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Base64-encoded file bytes (Vercel persistence)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Video-specific fields
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # path to auto-generated thumbnail from first frame

    # Multi-size image thumbnails (auto-generated on upload)
    thumbnail_small: Mapped[Optional[str]] = mapped_column(String, nullable=True)   # 150px wide
    thumbnail_medium: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # 400px wide
    thumbnail_large: Mapped[Optional[str]] = mapped_column(String, nullable=True)   # 800px wide

    # EXIF metadata (extracted from images)
    exif_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string with EXIF info

    # Garbage collection / last usage tracking
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    marked_unused: Mapped[Optional[bool]] = mapped_column(Integer, nullable=True, default=None)  # True if flagged by garbage collection

    # Relationships
    user = relationship("User", back_populates="assets")
