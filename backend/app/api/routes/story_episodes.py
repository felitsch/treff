"""Story Episode routes - CRUD for episodes within a Story Arc."""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.story_arc import StoryArc
from app.models.story_episode import StoryEpisode
from app.models.post import Post

router = APIRouter()
logger = logging.getLogger(__name__)

VALID_STATUSES = {"planned", "draft", "published"}


def episode_to_dict(episode: StoryEpisode) -> dict:
    """Convert a StoryEpisode model to a plain dict."""
    return {
        "id": episode.id,
        "arc_id": episode.arc_id,
        "post_id": episode.post_id,
        "episode_number": episode.episode_number,
        "episode_title": episode.episode_title,
        "teaser_text": episode.teaser_text,
        "cliffhanger_text": episode.cliffhanger_text,
        "previously_text": episode.previously_text,
        "next_episode_hint": episode.next_episode_hint,
        "status": episode.status,
        "created_at": episode.created_at.isoformat() if episode.created_at else None,
        "updated_at": episode.updated_at.isoformat() if episode.updated_at else None,
    }


async def _verify_arc_ownership(arc_id: int, user_id: int, db: AsyncSession) -> StoryArc:
    """Verify that the story arc exists and belongs to the current user."""
    result = await db.execute(
        select(StoryArc).where(StoryArc.id == arc_id, StoryArc.user_id == user_id)
    )
    arc = result.scalar_one_or_none()
    if not arc:
        raise HTTPException(status_code=404, detail="Story arc not found")
    return arc


async def _get_next_episode_number(arc_id: int, db: AsyncSession) -> int:
    """Get the next available episode number for a story arc."""
    result = await db.execute(
        select(func.max(StoryEpisode.episode_number)).where(
            StoryEpisode.arc_id == arc_id
        )
    )
    max_number = result.scalar_one_or_none()
    return (max_number or 0) + 1


@router.get("/{arc_id}/episodes")
async def list_episodes(
    arc_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List all episodes for a story arc, sorted by episode_number."""
    await _verify_arc_ownership(arc_id, user_id, db)

    result = await db.execute(
        select(StoryEpisode)
        .where(StoryEpisode.arc_id == arc_id)
        .order_by(StoryEpisode.episode_number)
    )
    episodes = result.scalars().all()
    return [episode_to_dict(ep) for ep in episodes]


@router.get("/{arc_id}/episodes/{episode_id}")
async def get_episode(
    arc_id: int,
    episode_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a single episode by ID."""
    await _verify_arc_ownership(arc_id, user_id, db)

    result = await db.execute(
        select(StoryEpisode).where(
            StoryEpisode.id == episode_id,
            StoryEpisode.arc_id == arc_id,
        )
    )
    episode = result.scalar_one_or_none()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    return episode_to_dict(episode)


@router.post("/{arc_id}/episodes", status_code=201)
async def create_episode(
    arc_id: int,
    episode_data: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a new episode in a story arc.

    Required: episode_title
    Optional: post_id, episode_number (auto-assigned if not provided),
              teaser_text, cliffhanger_text, previously_text, next_episode_hint, status
    """
    arc = await _verify_arc_ownership(arc_id, user_id, db)

    # Validate required field
    if not episode_data.get("episode_title"):
        raise HTTPException(status_code=400, detail="episode_title is required")

    # Validate status if provided
    if "status" in episode_data:
        if episode_data["status"] not in VALID_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(sorted(VALID_STATUSES))}"
            )

    # Validate post_id if provided - ensure post exists and belongs to user
    post_id = episode_data.get("post_id")
    if post_id is not None:
        result = await db.execute(
            select(Post).where(Post.id == post_id, Post.user_id == user_id)
        )
        post = result.scalar_one_or_none()
        if not post:
            raise HTTPException(status_code=400, detail="Post not found or does not belong to you")

    # Auto-assign episode_number if not provided
    episode_number = episode_data.get("episode_number")
    if episode_number is None:
        episode_number = await _get_next_episode_number(arc_id, db)

    # Filter to allowed fields
    allowed_fields = {
        "episode_title", "teaser_text", "cliffhanger_text",
        "previously_text", "next_episode_hint", "status",
    }
    filtered_data = {k: v for k, v in episode_data.items() if k in allowed_fields}

    episode = StoryEpisode(
        arc_id=arc_id,
        post_id=post_id,
        episode_number=episode_number,
        **filtered_data,
    )
    db.add(episode)

    # Update current_episode on the arc if this is a new highest episode
    if episode_number > arc.current_episode:
        arc.current_episode = episode_number

    await db.flush()
    await db.refresh(episode)

    # Also update the linked post's story_arc_id and episode_number if post_id is set
    if post_id is not None:
        result = await db.execute(
            select(Post).where(Post.id == post_id)
        )
        linked_post = result.scalar_one_or_none()
        if linked_post:
            linked_post.story_arc_id = arc_id
            linked_post.episode_number = episode_number

    await db.commit()

    logger.info(f"Created episode '{episode.episode_title}' (#{episode_number}) in arc {arc_id}")
    return episode_to_dict(episode)


@router.put("/{arc_id}/episodes/{episode_id}")
async def update_episode(
    arc_id: int,
    episode_id: int,
    episode_data: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing episode."""
    await _verify_arc_ownership(arc_id, user_id, db)

    result = await db.execute(
        select(StoryEpisode).where(
            StoryEpisode.id == episode_id,
            StoryEpisode.arc_id == arc_id,
        )
    )
    episode = result.scalar_one_or_none()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    # Validate status if provided
    if "status" in episode_data:
        if episode_data["status"] not in VALID_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(sorted(VALID_STATUSES))}"
            )

    # Validate post_id if provided
    if "post_id" in episode_data and episode_data["post_id"] is not None:
        result = await db.execute(
            select(Post).where(Post.id == episode_data["post_id"], Post.user_id == user_id)
        )
        post = result.scalar_one_or_none()
        if not post:
            raise HTTPException(status_code=400, detail="Post not found or does not belong to you")

    # Update allowed fields
    allowed_fields = {
        "episode_title", "teaser_text", "cliffhanger_text",
        "previously_text", "next_episode_hint", "status",
        "post_id", "episode_number",
    }
    for key, value in episode_data.items():
        if key in allowed_fields and hasattr(episode, key):
            setattr(episode, key, value)

    # If post_id changed, update the linked post's story_arc_id and episode_number
    new_post_id = episode_data.get("post_id")
    if "post_id" in episode_data and new_post_id is not None:
        result = await db.execute(
            select(Post).where(Post.id == new_post_id)
        )
        linked_post = result.scalar_one_or_none()
        if linked_post:
            linked_post.story_arc_id = arc_id
            linked_post.episode_number = episode.episode_number

    await db.flush()
    await db.refresh(episode)
    await db.commit()

    logger.info(f"Updated episode {episode_id} in arc {arc_id}")
    return episode_to_dict(episode)


@router.delete("/{arc_id}/episodes/{episode_id}")
async def delete_episode(
    arc_id: int,
    episode_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete an episode from a story arc."""
    await _verify_arc_ownership(arc_id, user_id, db)

    result = await db.execute(
        select(StoryEpisode).where(
            StoryEpisode.id == episode_id,
            StoryEpisode.arc_id == arc_id,
        )
    )
    episode = result.scalar_one_or_none()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    # Clear story_arc_id and episode_number on linked post if any
    if episode.post_id:
        result = await db.execute(
            select(Post).where(Post.id == episode.post_id)
        )
        linked_post = result.scalar_one_or_none()
        if linked_post:
            linked_post.story_arc_id = None
            linked_post.episode_number = None

    await db.delete(episode)
    await db.commit()

    logger.info(f"Deleted episode {episode_id} from arc {arc_id}")
    return {"message": "Episode deleted"}
