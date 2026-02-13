"""Hook model for tracking generated attention-grabber hooks."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from app.core.database import Base


class Hook(Base):
    """Stores generated hooks for analysis of which hook types perform best."""

    __tablename__ = "hooks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=True, index=True)
    hook_text = Column(Text, nullable=False)
    hook_type = Column(String(50), nullable=False)  # frage, statistik, emotion, provokation, story_opener
    topic = Column(String(200), nullable=True)
    country = Column(String(50), nullable=True)
    tone = Column(String(50), nullable=True)
    platform = Column(String(50), nullable=True)
    selected = Column(Integer, default=0)  # 1 if this hook was chosen by the user
    source = Column(String(50), default="rule_based")  # gemini or rule_based
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
