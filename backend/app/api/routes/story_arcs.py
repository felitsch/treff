"""Story Arc routes - CRUD for multi-part story series."""

import logging
from typing import Optional
from datetime import date, timedelta, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.story_arc import StoryArc
from app.models.story_episode import StoryEpisode
from app.models.post import Post
from app.models.content_suggestion import ContentSuggestion
from app.models.student import Student

router = APIRouter()
logger = logging.getLogger(__name__)


def story_arc_to_dict(arc: StoryArc) -> dict:
    """Convert a StoryArc model to a plain dict to avoid lazy-loading issues."""
    return {
        "id": arc.id,
        "user_id": arc.user_id,
        "title": arc.title,
        "subtitle": arc.subtitle,
        "description": arc.description,
        "student_id": arc.student_id,
        "country": arc.country,
        "status": arc.status,
        "planned_episodes": arc.planned_episodes,
        "current_episode": arc.current_episode,
        "cover_image_id": arc.cover_image_id,
        "tone": arc.tone,
        "created_at": arc.created_at.isoformat() if arc.created_at else None,
        "updated_at": arc.updated_at.isoformat() if arc.updated_at else None,
    }


async def _auto_suggest_story_teaser(arc: StoryArc, db: AsyncSession) -> Optional[dict]:
    """Auto-generate a content suggestion for a feed teaser when a story arc becomes active.

    Creates a 'story_teaser' type suggestion pointing users to create a feed post
    that promotes the new story series in their Instagram Stories.
    """
    # Look up student name if linked
    student_name = None
    if arc.student_id:
        result = await db.execute(
            select(Student).where(Student.id == arc.student_id)
        )
        student = result.scalar_one_or_none()
        if student:
            student_name = student.name

    # Build suggestion title and description
    title_parts = [f"Story-Teaser: {arc.title}"]
    if student_name:
        title_parts.append(f"mit {student_name}")
    suggestion_title = " ".join(title_parts)

    desc_parts = [
        f"Neue Story-Serie '{arc.title}' startet!",
    ]
    if student_name:
        desc_parts.append(f"Erstelle einen Feed-Teaser-Post fuer {student_name}s Abenteuer.")
    else:
        desc_parts.append("Erstelle einen Feed-Teaser-Post, der auf die Story-Serie hinweist.")
    desc_parts.append("Schau in unsere Stories! Verwende das Story-Teaser Template.")

    suggestion = ContentSuggestion(
        suggestion_type="story_teaser",
        title=suggestion_title,
        description=" ".join(desc_parts),
        suggested_category="story_teaser",
        suggested_country=arc.country,
        suggested_date=date.today(),
        reason=f"Story-Arc '{arc.title}' wurde aktiviert - Feed-Teaser empfohlen",
        status="pending",
    )
    db.add(suggestion)
    logger.info(f"Auto-suggested story teaser for arc '{arc.title}' (id={arc.id})")
    return {
        "suggestion_created": True,
        "suggestion_title": suggestion_title,
    }


@router.get("")
async def list_story_arcs(
    student_id: Optional[int] = None,
    country: Optional[str] = None,
    status: Optional[str] = None,
    enriched: bool = False,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List story arcs with optional filters: student_id, country, status.

    Set enriched=true to include student_name, episode counts (published/total),
    and cover_image_url for card-based overview displays.
    """
    where_clauses = [StoryArc.user_id == user_id]

    if student_id is not None:
        where_clauses.append(StoryArc.student_id == student_id)
    if country:
        where_clauses.append(StoryArc.country == country)
    if status:
        valid_statuses = {"draft", "active", "paused", "completed"}
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(sorted(valid_statuses))}"
            )
        where_clauses.append(StoryArc.status == status)

    query = select(StoryArc).where(*where_clauses).order_by(StoryArc.created_at.desc())
    result = await db.execute(query)
    arcs = result.scalars().all()

    if not enriched:
        return [story_arc_to_dict(a) for a in arcs]

    # Enriched mode: add student_name, episode stats, cover_image_url
    enriched_arcs = []
    for arc in arcs:
        arc_dict = story_arc_to_dict(arc)

        # Get student name
        if arc.student_id:
            student_result = await db.execute(
                select(Student.name).where(Student.id == arc.student_id)
            )
            student_name = student_result.scalar_one_or_none()
            arc_dict["student_name"] = student_name
        else:
            arc_dict["student_name"] = None

        # Count episodes and published episodes
        total_eps_result = await db.execute(
            select(func.count(StoryEpisode.id)).where(StoryEpisode.arc_id == arc.id)
        )
        total_episodes = total_eps_result.scalar() or 0

        published_eps_result = await db.execute(
            select(func.count(StoryEpisode.id)).where(
                StoryEpisode.arc_id == arc.id,
                StoryEpisode.status == "published",
            )
        )
        published_episodes = published_eps_result.scalar() or 0

        arc_dict["total_episodes"] = total_episodes
        arc_dict["published_episodes"] = published_episodes

        # Get cover image URL if available
        if arc.cover_image_id:
            from app.models.asset import Asset
            asset_result = await db.execute(
                select(Asset.file_path).where(Asset.id == arc.cover_image_id)
            )
            file_path = asset_result.scalar_one_or_none()
            arc_dict["cover_image_url"] = f"/api/assets/file/{file_path}" if file_path else None
        else:
            arc_dict["cover_image_url"] = None

        enriched_arcs.append(arc_dict)

    return enriched_arcs


@router.get("/{arc_id}")
async def get_story_arc(
    arc_id: int,
    include_episodes: bool = False,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a single story arc by ID.

    Set include_episodes=true to include full episode list with linked post info.
    """
    result = await db.execute(
        select(StoryArc).where(StoryArc.id == arc_id, StoryArc.user_id == user_id)
    )
    arc = result.scalar_one_or_none()
    if not arc:
        raise HTTPException(status_code=404, detail="Story arc not found")

    arc_dict = story_arc_to_dict(arc)

    # Add student name
    if arc.student_id:
        student_result = await db.execute(
            select(Student.name).where(Student.id == arc.student_id)
        )
        arc_dict["student_name"] = student_result.scalar_one_or_none()
    else:
        arc_dict["student_name"] = None

    # Add cover image URL
    if arc.cover_image_id:
        from app.models.asset import Asset
        asset_result = await db.execute(
            select(Asset.file_path).where(Asset.id == arc.cover_image_id)
        )
        file_path = asset_result.scalar_one_or_none()
        arc_dict["cover_image_url"] = f"/api/assets/file/{file_path}" if file_path else None
    else:
        arc_dict["cover_image_url"] = None

    if include_episodes:
        # Get all episodes sorted by episode_number
        eps_result = await db.execute(
            select(StoryEpisode)
            .where(StoryEpisode.arc_id == arc.id)
            .order_by(StoryEpisode.episode_number)
        )
        episodes = eps_result.scalars().all()

        episodes_list = []
        for ep in episodes:
            ep_dict = {
                "id": ep.id,
                "arc_id": ep.arc_id,
                "post_id": ep.post_id,
                "episode_number": ep.episode_number,
                "episode_title": ep.episode_title,
                "teaser_text": ep.teaser_text,
                "cliffhanger_text": ep.cliffhanger_text,
                "previously_text": ep.previously_text,
                "next_episode_hint": ep.next_episode_hint,
                "status": ep.status,
                "created_at": ep.created_at.isoformat() if ep.created_at else None,
                "updated_at": ep.updated_at.isoformat() if ep.updated_at else None,
            }
            # Get linked post info if available
            if ep.post_id:
                post_result = await db.execute(
                    select(Post).where(Post.id == ep.post_id)
                )
                post = post_result.scalar_one_or_none()
                if post:
                    ep_dict["post_title"] = post.title
                    ep_dict["post_status"] = post.status
                    ep_dict["post_scheduled_date"] = post.scheduled_date.isoformat() if post.scheduled_date else None
                    ep_dict["post_platform"] = post.platform
            episodes_list.append(ep_dict)

        arc_dict["episodes"] = episodes_list

        # Add episode counts
        arc_dict["total_episodes"] = len(episodes_list)
        arc_dict["published_episodes"] = sum(1 for e in episodes_list if e["status"] == "published")

    return arc_dict


@router.post("", status_code=201)
async def create_story_arc(
    arc_data: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a new story arc."""
    # Validate required field
    if not arc_data.get("title"):
        raise HTTPException(status_code=400, detail="Title is required")

    # Validate status if provided
    if "status" in arc_data:
        valid_statuses = {"draft", "active", "paused", "completed"}
        if arc_data["status"] not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(sorted(valid_statuses))}"
            )

    # Validate tone if provided
    if "tone" in arc_data:
        valid_tones = {"jugendlich", "serioess"}
        if arc_data["tone"] not in valid_tones:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid tone. Must be one of: {', '.join(sorted(valid_tones))}"
            )

    # Filter to only allowed fields
    allowed_fields = {
        "title", "subtitle", "description", "student_id", "country",
        "status", "planned_episodes", "current_episode", "cover_image_id", "tone",
    }
    filtered_data = {k: v for k, v in arc_data.items() if k in allowed_fields}

    arc = StoryArc(user_id=user_id, **filtered_data)
    db.add(arc)
    await db.flush()
    await db.refresh(arc)
    response = story_arc_to_dict(arc)

    # Auto-suggest feed teaser when arc is created with status "active"
    suggestion_info = None
    if arc.status == "active":
        suggestion_info = await _auto_suggest_story_teaser(arc, db)

    await db.commit()

    if suggestion_info:
        response["teaser_suggestion"] = suggestion_info

    return response


@router.put("/{arc_id}")
async def update_story_arc(
    arc_id: int,
    arc_data: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing story arc."""
    result = await db.execute(
        select(StoryArc).where(StoryArc.id == arc_id, StoryArc.user_id == user_id)
    )
    arc = result.scalar_one_or_none()
    if not arc:
        raise HTTPException(status_code=404, detail="Story arc not found")

    # Validate status if provided
    if "status" in arc_data:
        valid_statuses = {"draft", "active", "paused", "completed"}
        if arc_data["status"] not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(sorted(valid_statuses))}"
            )

    # Validate tone if provided
    if "tone" in arc_data:
        valid_tones = {"jugendlich", "serioess"}
        if arc_data["tone"] not in valid_tones:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid tone. Must be one of: {', '.join(sorted(valid_tones))}"
            )

    # Track previous status for auto-suggestion
    previous_status = arc.status

    # Update allowed fields
    allowed_fields = {
        "title", "subtitle", "description", "student_id", "country",
        "status", "planned_episodes", "current_episode", "cover_image_id", "tone",
    }
    for key, value in arc_data.items():
        if key in allowed_fields and hasattr(arc, key):
            setattr(arc, key, value)

    await db.flush()
    await db.refresh(arc)
    response = story_arc_to_dict(arc)

    # Auto-suggest feed teaser when arc transitions to "active"
    suggestion_info = None
    if arc.status == "active" and previous_status != "active":
        suggestion_info = await _auto_suggest_story_teaser(arc, db)

    await db.commit()

    if suggestion_info:
        response["teaser_suggestion"] = suggestion_info

    return response


@router.delete("/{arc_id}")
async def delete_story_arc(
    arc_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a story arc."""
    result = await db.execute(
        select(StoryArc).where(StoryArc.id == arc_id, StoryArc.user_id == user_id)
    )
    arc = result.scalar_one_or_none()
    if not arc:
        raise HTTPException(status_code=404, detail="Story arc not found")

    await db.delete(arc)
    await db.commit()
    return {"message": "Story arc deleted"}


@router.post("/wizard", status_code=201)
async def create_story_arc_wizard(
    wizard_data: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a story arc with episodes and optional calendar placeholders in one step.

    Request body:
    {
        "title": str (required),
        "subtitle": str,
        "description": str,
        "student_id": int,
        "country": str,
        "tone": str,
        "planned_episodes": int,
        "cover_image_id": int,
        "status": str (default "draft"),
        "episodes": [{"title": "...", "description": "..."}],
        "schedule_frequency": str ("daily", "twice_weekly", "weekly", "biweekly"),
        "schedule_start_date": str (ISO date),
        "create_calendar_placeholders": bool (default false)
    }
    """
    # Validate required field
    if not wizard_data.get("title"):
        raise HTTPException(status_code=400, detail="Title is required")

    # Validate status if provided
    status = wizard_data.get("status", "draft")
    valid_statuses = {"draft", "active", "paused", "completed"}
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(sorted(valid_statuses))}"
        )

    # Validate tone if provided
    tone = wizard_data.get("tone", "jugendlich")
    valid_tones = {"jugendlich", "serioess"}
    if tone not in valid_tones:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tone. Must be one of: {', '.join(sorted(valid_tones))}"
        )

    # Create the Story Arc
    arc = StoryArc(
        user_id=user_id,
        title=wizard_data["title"],
        subtitle=wizard_data.get("subtitle"),
        description=wizard_data.get("description"),
        student_id=wizard_data.get("student_id"),
        country=wizard_data.get("country"),
        status=status,
        planned_episodes=wizard_data.get("planned_episodes", 8),
        cover_image_id=wizard_data.get("cover_image_id"),
        tone=tone,
    )
    db.add(arc)
    await db.flush()
    await db.refresh(arc)

    # Create episodes
    episodes_data = wizard_data.get("episodes", [])
    created_episodes = []

    for i, ep_data in enumerate(episodes_data):
        episode = StoryEpisode(
            arc_id=arc.id,
            episode_number=i + 1,
            episode_title=ep_data.get("title", f"Episode {i + 1}"),
            teaser_text=ep_data.get("description"),
            status="planned",
        )
        db.add(episode)
        created_episodes.append(episode)

    # Update arc current_episode count
    arc.current_episode = len(created_episodes)

    # Create calendar placeholders if requested
    created_posts = []
    if wizard_data.get("create_calendar_placeholders") and wizard_data.get("schedule_start_date"):
        frequency = wizard_data.get("schedule_frequency", "weekly")
        try:
            start_date = date.fromisoformat(wizard_data["schedule_start_date"])
        except (ValueError, TypeError):
            start_date = date.today() + timedelta(days=1)

        # Calculate dates based on frequency
        day_gaps = {
            "daily": 1,
            "twice_weekly": 3,  # ~2x per week = every 3-4 days
            "weekly": 7,
            "biweekly": 14,
        }
        gap = day_gaps.get(frequency, 7)

        for i, ep_data in enumerate(episodes_data):
            scheduled_date = start_date + timedelta(days=i * gap)
            post = Post(
                user_id=user_id,
                title=f"{arc.title} - {ep_data.get('title', f'Episode {i + 1}')}",
                status="draft",
                category="story_teaser",
                country=wizard_data.get("country", ""),
                platform="instagram_story",
                scheduled_date=scheduled_date,
                scheduled_time="18:00",
                story_arc_id=arc.id,
                episode_number=i + 1,
                student_id=wizard_data.get("student_id"),
            )
            db.add(post)
            created_posts.append(post)

    await db.flush()

    # Link posts to episodes
    for i, post in enumerate(created_posts):
        await db.refresh(post)
        if i < len(created_episodes):
            await db.refresh(created_episodes[i])
            created_episodes[i].post_id = post.id

    # Auto-suggest feed teaser when arc is created as active
    suggestion_info = None
    if arc.status == "active":
        suggestion_info = await _auto_suggest_story_teaser(arc, db)

    await db.commit()

    response = story_arc_to_dict(arc)
    response["episodes"] = [
        {
            "id": ep.id,
            "episode_number": ep.episode_number,
            "episode_title": ep.episode_title,
            "teaser_text": ep.teaser_text,
            "status": ep.status,
        }
        for ep in created_episodes
    ]
    response["calendar_posts_created"] = len(created_posts)
    if suggestion_info:
        response["teaser_suggestion"] = suggestion_info

    return response
