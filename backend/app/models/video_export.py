"""VideoExport model - tracks video export jobs with progress."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class VideoExport(Base):
    __tablename__ = "video_exports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("assets.id"), nullable=False)

    # Export settings
    aspect_ratio: Mapped[str] = mapped_column(String, nullable=False)  # 9:16, 1:1, 4:5
    platform: Mapped[str] = mapped_column(String, default="instagram")  # instagram, tiktok
    quality: Mapped[int] = mapped_column(Integer, default=75)  # 1-100 quality slider
    max_duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Platform limit

    # Focus point for smart cropping (percentage 0-100)
    focus_x: Mapped[float] = mapped_column(Float, default=50.0)
    focus_y: Mapped[float] = mapped_column(Float, default=50.0)

    # Output info
    output_filename: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    output_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    output_file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    output_width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    output_height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    output_duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Progress tracking
    status: Mapped[str] = mapped_column(String, default="pending")  # pending, processing, done, error
    progress: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Batch group ID (for batch exports)
    batch_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
