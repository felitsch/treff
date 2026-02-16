"""PostInteractiveElement model for Instagram Story interactive elements."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Integer, String, Text, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PostInteractiveElement(Base):
    __tablename__ = "post_interactive_elements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    slide_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    element_type: Mapped[str] = mapped_column(
        String, nullable=False
    )  # poll, quiz, slider, question
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON array of option strings (for poll/quiz)
    correct_answer: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Index of correct answer (for quiz)
    emoji: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )  # Emoji for slider element
    position_x: Mapped[float] = mapped_column(Float, nullable=False, default=50.0)  # % from left
    position_y: Mapped[float] = mapped_column(Float, nullable=False, default=50.0)  # % from top

    # Relationships
    post = relationship("Post", back_populates="interactive_elements")
