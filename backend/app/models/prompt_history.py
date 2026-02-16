"""PromptHistory model for storing AI prompt calls, results, and favorites."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey
from app.core.database import Base


class PromptHistory(Base):
    """Stores every AI prompt call with its input, output, and metadata.

    Enables users to review past AI generations, mark successful prompts
    as favorites, and reuse them in future content creation workflows.
    """

    __tablename__ = "prompt_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Prompt type: text, image, hashtags, optimization, video_script
    prompt_type = Column(String(50), nullable=False, index=True)

    # The prompt/input sent to the AI
    prompt_text = Column(Text, nullable=False)

    # Options/parameters sent along (JSON string)
    options = Column(Text, nullable=True)

    # The AI result/output
    result_text = Column(Text, nullable=True)

    # Token usage / cost estimation
    tokens_used = Column(Integer, nullable=True)
    estimated_cost = Column(Float, nullable=True)  # in EUR cents

    # AI model used
    model = Column(String(100), nullable=True)

    # Favorite flag
    is_favorite = Column(Boolean, default=False, nullable=False, index=True)

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
