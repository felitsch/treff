"""BackgroundTask model.

Tracks long-running async operations (AI image generation, bulk exports,
report generation, template rendering, etc.) with real-time status updates.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class BackgroundTask(Base):
    __tablename__ = "background_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    # Task classification
    task_type: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g. ai_image, bulk_export, report_pdf, template_render
    title: Mapped[str] = mapped_column(String(255), nullable=False)  # Human-readable title

    # Status: pending, processing, completed, failed, cancelled
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    progress: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=0.0)  # 0.0 - 1.0

    # Result / Error
    result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON-encoded result
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Error message if failed

    # Timing
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timeout (seconds). 0 = no timeout.
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=300, nullable=False)

    # Callback URL (optional, for webhook notification)
    callback_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
