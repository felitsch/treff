"""ExportHistory model."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ExportHistory(Base):
    __tablename__ = "export_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("posts.id"), nullable=False)
    platform: Mapped[str] = mapped_column(String, nullable=False)
    format: Mapped[str] = mapped_column(String, nullable=False)  # png, zip
    file_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    resolution: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # 1080, 2160
    slide_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    exported_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    post = relationship("Post", back_populates="export_records")
