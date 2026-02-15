"""Video Overlay model for storing overlay configurations on videos."""

from datetime import datetime, timezone
from sqlalchemy import Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class VideoOverlay(Base):
    __tablename__ = "video_overlays"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("assets.id"), nullable=False)  # Video asset
    name: Mapped[str] = mapped_column(String, nullable=False, default="Unbenanntes Overlay")

    # JSON array of overlay layers: [{type, text, x, y, width, height, fontSize, fontFamily, color, bgColor, opacity, startTime, endTime, animation, ...}]
    layers: Mapped[str] = mapped_column(Text, nullable=False, default="[]")

    # Rendered output path (after ffmpeg processing)
    rendered_path: Mapped[str | None] = mapped_column(String, nullable=True)
    render_status: Mapped[str] = mapped_column(String, default="pending")  # pending, rendering, done, error
    render_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    rendered_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # Base64-encoded rendered PNG (Vercel persistence)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user = relationship("User", backref="video_overlays")
    asset = relationship("Asset", backref="video_overlays")
