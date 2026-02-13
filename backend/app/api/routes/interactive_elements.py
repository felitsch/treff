"""Interactive Elements routes for Instagram Story elements (polls, quizzes, sliders, questions)."""

import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.post import Post
from app.models.interactive_element import PostInteractiveElement

router = APIRouter()


VALID_ELEMENT_TYPES = {"poll", "quiz", "slider", "question"}


class InteractiveElementCreate(BaseModel):
    slide_index: int = 0
    element_type: str  # poll, quiz, slider, question
    question_text: str
    options: list[str] | None = None  # For poll/quiz
    correct_answer: int | None = None  # For quiz (index into options)
    emoji: str | None = None  # For slider
    position_x: float = Field(default=50.0, ge=0, le=100)
    position_y: float = Field(default=50.0, ge=0, le=100)


class InteractiveElementUpdate(BaseModel):
    slide_index: int | None = None
    element_type: str | None = None
    question_text: str | None = None
    options: list[str] | None = None
    correct_answer: int | None = None
    emoji: str | None = None
    position_x: float | None = Field(default=None, ge=0, le=100)
    position_y: float | None = Field(default=None, ge=0, le=100)


def element_to_dict(el: PostInteractiveElement) -> dict:
    """Convert a PostInteractiveElement to a plain dict."""
    options = None
    if el.options:
        try:
            options = json.loads(el.options)
        except (json.JSONDecodeError, TypeError):
            options = []
    return {
        "id": el.id,
        "post_id": el.post_id,
        "slide_index": el.slide_index,
        "element_type": el.element_type,
        "question_text": el.question_text,
        "options": options,
        "correct_answer": el.correct_answer,
        "emoji": el.emoji,
        "position_x": el.position_x,
        "position_y": el.position_y,
    }


@router.get("/{post_id}/interactive-elements")
async def get_interactive_elements(
    post_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get all interactive elements for a post."""
    # Verify post belongs to user
    post_result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user_id)
    )
    if not post_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Post not found")

    result = await db.execute(
        select(PostInteractiveElement)
        .where(PostInteractiveElement.post_id == post_id)
        .order_by(PostInteractiveElement.slide_index, PostInteractiveElement.id)
    )
    elements = result.scalars().all()
    return [element_to_dict(el) for el in elements]


@router.post("/{post_id}/interactive-elements", status_code=201)
async def create_interactive_element(
    post_id: int,
    data: InteractiveElementCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Add an interactive element to a post."""
    # Verify post belongs to user
    post_result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user_id)
    )
    if not post_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Post not found")

    if data.element_type not in VALID_ELEMENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid element_type. Must be one of: {', '.join(VALID_ELEMENT_TYPES)}",
        )

    # Validate type-specific fields
    if data.element_type in ("poll", "quiz") and (
        not data.options or len(data.options) < 2
    ):
        raise HTTPException(
            status_code=400,
            detail="Poll and Quiz elements require at least 2 options.",
        )

    if data.element_type == "quiz" and data.correct_answer is None:
        raise HTTPException(
            status_code=400,
            detail="Quiz elements require a correct_answer index.",
        )

    options_json = json.dumps(data.options) if data.options else None

    element = PostInteractiveElement(
        post_id=post_id,
        slide_index=data.slide_index,
        element_type=data.element_type,
        question_text=data.question_text,
        options=options_json,
        correct_answer=data.correct_answer,
        emoji=data.emoji,
        position_x=data.position_x,
        position_y=data.position_y,
    )
    db.add(element)
    await db.flush()
    await db.refresh(element)
    response = element_to_dict(element)
    await db.commit()
    return response


@router.put("/{post_id}/interactive-elements/{element_id}")
async def update_interactive_element(
    post_id: int,
    element_id: int,
    data: InteractiveElementUpdate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update an interactive element."""
    # Verify post belongs to user
    post_result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user_id)
    )
    if not post_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Post not found")

    result = await db.execute(
        select(PostInteractiveElement).where(
            PostInteractiveElement.id == element_id,
            PostInteractiveElement.post_id == post_id,
        )
    )
    element = result.scalar_one_or_none()
    if not element:
        raise HTTPException(status_code=404, detail="Interactive element not found")

    # Update fields if provided
    update_data = data.model_dump(exclude_unset=True)

    if "element_type" in update_data:
        if update_data["element_type"] not in VALID_ELEMENT_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid element_type. Must be one of: {', '.join(VALID_ELEMENT_TYPES)}",
            )
        element.element_type = update_data["element_type"]

    if "question_text" in update_data:
        element.question_text = update_data["question_text"]
    if "slide_index" in update_data:
        element.slide_index = update_data["slide_index"]
    if "correct_answer" in update_data:
        element.correct_answer = update_data["correct_answer"]
    if "emoji" in update_data:
        element.emoji = update_data["emoji"]
    if "position_x" in update_data:
        element.position_x = update_data["position_x"]
    if "position_y" in update_data:
        element.position_y = update_data["position_y"]
    if "options" in update_data:
        element.options = (
            json.dumps(update_data["options"]) if update_data["options"] else None
        )

    await db.flush()
    await db.refresh(element)
    response = element_to_dict(element)
    await db.commit()
    return response


@router.delete("/{post_id}/interactive-elements/{element_id}")
async def delete_interactive_element(
    post_id: int,
    element_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete an interactive element from a post."""
    # Verify post belongs to user
    post_result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user_id)
    )
    if not post_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Post not found")

    result = await db.execute(
        select(PostInteractiveElement).where(
            PostInteractiveElement.id == element_id,
            PostInteractiveElement.post_id == post_id,
        )
    )
    element = result.scalar_one_or_none()
    if not element:
        raise HTTPException(status_code=404, detail="Interactive element not found")

    await db.delete(element)
    await db.commit()
    return {"message": "Interactive element deleted"}


@router.put("/{post_id}/interactive-elements")
async def bulk_update_interactive_elements(
    post_id: int,
    elements_data: list[dict],
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Replace all interactive elements for a post (bulk update)."""
    # Verify post belongs to user
    post_result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user_id)
    )
    if not post_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Post not found")

    # Delete existing elements
    result = await db.execute(
        select(PostInteractiveElement).where(
            PostInteractiveElement.post_id == post_id
        )
    )
    existing = result.scalars().all()
    for el in existing:
        await db.delete(el)

    # Create new elements
    new_elements = []
    for el_data in elements_data:
        element_type = el_data.get("element_type", "poll")
        if element_type not in VALID_ELEMENT_TYPES:
            continue

        options = el_data.get("options")
        options_json = json.dumps(options) if options else None

        element = PostInteractiveElement(
            post_id=post_id,
            slide_index=el_data.get("slide_index", 0),
            element_type=element_type,
            question_text=el_data.get("question_text", ""),
            options=options_json,
            correct_answer=el_data.get("correct_answer"),
            emoji=el_data.get("emoji"),
            position_x=el_data.get("position_x", 50.0),
            position_y=el_data.get("position_y", 50.0),
        )
        db.add(element)
        new_elements.append(element)

    await db.flush()
    for el in new_elements:
        await db.refresh(el)
    response = [element_to_dict(el) for el in new_elements]
    await db.commit()
    return response
