"""VideoScript model for storing generated video scripts for Reels and TikTok."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from app.core.database import Base


class VideoScript(Base):
    """Stores AI-generated video scripts with scene-by-scene breakdown.

    Each script contains timing, hook, voiceover text, visual descriptions,
    and CTAs for Instagram Reels and TikTok videos.
    """

    __tablename__ = "video_scripts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=True, index=True)

    # Script metadata
    title = Column(String(200), nullable=False)
    platform = Column(String(50), nullable=False)  # reels, tiktok, story
    duration_seconds = Column(Integer, nullable=False)  # 15, 30, 60, 90
    hook_formula = Column(String(100), nullable=True)  # Hook formula ID from social-content.json

    # Content context
    topic = Column(String(300), nullable=True)
    country = Column(String(50), nullable=True)
    category = Column(String(100), nullable=True)
    buyer_journey_stage = Column(String(50), nullable=True)  # awareness, consideration, decision
    tone = Column(String(50), default="jugendlich")

    # Generated content (JSON arrays/text)
    scenes = Column(Text, nullable=False)  # JSON array of scene objects
    voiceover_full = Column(Text, nullable=True)  # Combined voiceover text
    visual_notes = Column(Text, nullable=True)  # General visual direction
    cta_type = Column(String(50), nullable=True)  # CTA strategy type

    # Generation metadata
    source = Column(String(50), default="rule_based")  # gemini or rule_based

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
