"""HumorFormat model for predefined humor/meme template structures."""

from datetime import datetime, timezone
from sqlalchemy import Integer, String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class HumorFormat(Base):
    __tablename__ = "humor_formats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    template_structure: Mapped[str] = mapped_column(Text, nullable=False)  # JSON: structure/layout hints
    example_text: Mapped[str] = mapped_column(Text, nullable=False)  # JSON: example content
    platform_fit: Mapped[str] = mapped_column(String, nullable=False, default="both")  # instagram, tiktok, both
    icon: Mapped[str] = mapped_column(String, nullable=True)  # emoji icon for UI
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
