"""Video branding template model - Intro/Outro templates with TREFF branding."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from app.core.database import Base


class VideoTemplate(Base):
    """Pre-built intro and outro video sequences with TREFF branding.

    Templates define animated sequences (logo animation, color transitions,
    social handles) that get prepended/appended to user videos via ffmpeg concat.
    """
    __tablename__ = "video_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    template_type = Column(String, nullable=False)  # "intro" or "outro"
    country = Column(String, nullable=True)  # "usa", "kanada", "australien", "neuseeland", "irland", or None for generic
    duration_seconds = Column(Float, nullable=False, default=3.0)
    width = Column(Integer, nullable=False, default=1080)
    height = Column(Integer, nullable=False, default=1920)
    aspect_ratio = Column(String, nullable=False, default="9:16")  # 9:16, 1:1, 16:9
    # Branding config stored as JSON string
    branding_config = Column(Text, nullable=True)
    # Visual config: colors, animation style, etc.
    style = Column(String, nullable=False, default="default")  # default, minimal, bold, elegant
    primary_color = Column(String, nullable=False, default="#4C8BC2")
    secondary_color = Column(String, nullable=False, default="#FDD000")
    # Social handles to display (for outro)
    social_handle_instagram = Column(String, nullable=True, default="@treff_sprachreisen")
    social_handle_tiktok = Column(String, nullable=True, default="@treff_sprachreisen")
    website_url = Column(String, nullable=True, default="www.treff-sprachreisen.de")
    cta_text = Column(String, nullable=True)  # Call-to-action text for outro
    # Template is system default or user-created
    is_default = Column(Boolean, default=True)
    user_id = Column(Integer, nullable=True)  # NULL for system defaults
    # Preview image path (static thumbnail)
    preview_image_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
