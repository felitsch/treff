"""Post relations routes - Cross-post linking between Feed and Stories."""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, func

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.post import Post
from app.models.post_relation import PostRelation
from app.models.story_arc import StoryArc
from app.models.story_episode import StoryEpisode

logger = logging.getLogger(__name__)

router = APIRouter()

VALID_RELATION_TYPES = {"story_teaser", "cross_reference", "sequel", "related"}


def relation_to_dict(rel: PostRelation) -> dict:
    """Convert a PostRelation model to a plain dict."""
    return {
        "id": rel.id,
        "source_post_id": rel.source_post_id,
        "target_post_id": rel.target_post_id,
        "relation_type": rel.relation_type,
        "note": rel.note,
        "created_at": rel.created_at.isoformat() if rel.created_at else None,
    }


def post_summary(post: Post) -> dict:
    """Return a compact summary of a post for display in relation lists."""
    return {
        "id": post.id,
        "title": post.title,
        "category": post.category,
        "platform": post.platform,
        "status": post.status,
        "country": post.country,
        "story_arc_id": post.story_arc_id,
        "episode_number": post.episode_number,
        "scheduled_date": post.scheduled_date.isoformat() if post.scheduled_date else None,
        "created_at": post.created_at.isoformat() if post.created_at else None,
    }


@router.get("/{post_id}/relations")
async def get_post_relations(
    post_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get all relations for a post (both as source and target)."""
    # Verify post exists and belongs to user
    result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Get relations where this post is source or target
    result = await db.execute(
        select(PostRelation).where(
            or_(
                PostRelation.source_post_id == post_id,
                PostRelation.target_post_id == post_id,
            )
        ).order_by(PostRelation.created_at.desc())
    )
    relations = result.scalars().all()

    # Collect all related post IDs
    related_ids = set()
    for rel in relations:
        related_ids.add(rel.source_post_id)
        related_ids.add(rel.target_post_id)
    related_ids.discard(post_id)

    # Fetch related posts
    related_posts = {}
    if related_ids:
        result = await db.execute(
            select(Post).where(Post.id.in_(related_ids), Post.user_id == user_id)
        )
        for p in result.scalars().all():
            related_posts[p.id] = post_summary(p)

    # Build enriched relations list
    enriched = []
    for rel in relations:
        other_id = rel.target_post_id if rel.source_post_id == post_id else rel.source_post_id
        direction = "outgoing" if rel.source_post_id == post_id else "incoming"
        enriched.append({
            **relation_to_dict(rel),
            "direction": direction,
            "related_post": related_posts.get(other_id),
        })

    return {
        "post_id": post_id,
        "relations": enriched,
        "count": len(enriched),
    }


@router.post("/{post_id}/relations", status_code=201)
async def create_post_relation(
    post_id: int,
    data: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a relation between two posts.

    Body:
    - target_post_id: int - The post to link to
    - relation_type: str - One of: story_teaser, cross_reference, sequel, related
    - note: str (optional) - A note about the relationship
    """
    target_post_id = data.get("target_post_id")
    relation_type = data.get("relation_type", "cross_reference")
    note = data.get("note")

    if not target_post_id:
        raise HTTPException(status_code=400, detail="target_post_id is required")

    if target_post_id == post_id:
        raise HTTPException(status_code=400, detail="Cannot link a post to itself")

    if relation_type not in VALID_RELATION_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid relation_type. Must be one of: {', '.join(sorted(VALID_RELATION_TYPES))}"
        )

    # Verify both posts exist and belong to user
    result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user_id)
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source post not found")

    result = await db.execute(
        select(Post).where(Post.id == target_post_id, Post.user_id == user_id)
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Target post not found")

    # Check for duplicate relation (in either direction)
    result = await db.execute(
        select(PostRelation).where(
            or_(
                and_(
                    PostRelation.source_post_id == post_id,
                    PostRelation.target_post_id == target_post_id,
                ),
                and_(
                    PostRelation.source_post_id == target_post_id,
                    PostRelation.target_post_id == post_id,
                ),
            )
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Relation already exists between these posts")

    relation = PostRelation(
        source_post_id=post_id,
        target_post_id=target_post_id,
        relation_type=relation_type,
        note=note,
    )
    db.add(relation)
    await db.flush()
    await db.refresh(relation)
    result_dict = relation_to_dict(relation)
    result_dict["source_post"] = post_summary(source)
    result_dict["target_post"] = post_summary(target)
    await db.commit()
    return result_dict


@router.delete("/{post_id}/relations/{relation_id}")
async def delete_post_relation(
    post_id: int,
    relation_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a relation between two posts."""
    # Verify post belongs to user
    result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Post not found")

    # Find the relation (must involve this post)
    result = await db.execute(
        select(PostRelation).where(
            PostRelation.id == relation_id,
            or_(
                PostRelation.source_post_id == post_id,
                PostRelation.target_post_id == post_id,
            ),
        )
    )
    relation = result.scalar_one_or_none()
    if not relation:
        raise HTTPException(status_code=404, detail="Relation not found")

    await db.delete(relation)
    await db.commit()
    return {"message": "Relation deleted", "id": relation_id}


@router.post("/{post_id}/suggest-relations")
async def suggest_post_relations(
    post_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Suggest related posts for cross-linking.

    Auto-suggests:
    1. Posts in the same story arc (for story_teaser links)
    2. Feed posts when current is a story (and vice versa)
    3. Posts with the same student
    4. Posts with the same country and category
    """
    result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Get already-linked post IDs to exclude
    result = await db.execute(
        select(PostRelation).where(
            or_(
                PostRelation.source_post_id == post_id,
                PostRelation.target_post_id == post_id,
            )
        )
    )
    existing_rels = result.scalars().all()
    linked_ids = {post_id}
    for rel in existing_rels:
        linked_ids.add(rel.source_post_id)
        linked_ids.add(rel.target_post_id)

    suggestions = []

    # 1. Story-Arc related: If post belongs to an arc, suggest other arc posts and feed teasers
    if post.story_arc_id:
        result = await db.execute(
            select(Post).where(
                Post.user_id == user_id,
                Post.story_arc_id == post.story_arc_id,
                Post.id.notin_(linked_ids),
            ).order_by(Post.episode_number.asc()).limit(10)
        )
        arc_posts = result.scalars().all()
        for p in arc_posts:
            suggestions.append({
                "post": post_summary(p),
                "suggested_type": "sequel",
                "reason": f"Gleiche Story-Serie (Episode {p.episode_number or '?'})",
            })

        # Suggest feed posts as teasers for this story
        result = await db.execute(
            select(Post).where(
                Post.user_id == user_id,
                Post.platform == "instagram_feed",
                Post.id.notin_(linked_ids),
                Post.story_arc_id == None,  # Feed posts not already in a series
            ).order_by(Post.created_at.desc()).limit(5)
        )
        feed_posts = result.scalars().all()
        for p in feed_posts:
            suggestions.append({
                "post": post_summary(p),
                "suggested_type": "story_teaser",
                "reason": "Feed-Post als Teaser fuer Story-Serie",
            })

    # 2. Cross-platform: If this is a story, suggest feed posts (and vice versa)
    if post.platform == "instagram_story":
        result = await db.execute(
            select(Post).where(
                Post.user_id == user_id,
                Post.platform == "instagram_feed",
                Post.id.notin_(linked_ids),
                Post.country == post.country if post.country else True,
            ).order_by(Post.created_at.desc()).limit(5)
        )
        feed_posts = result.scalars().all()
        for p in feed_posts:
            if p.id not in {s["post"]["id"] for s in suggestions}:
                suggestions.append({
                    "post": post_summary(p),
                    "suggested_type": "cross_reference",
                    "reason": "Feed-Post zum gleichen Thema",
                })
    elif post.platform == "instagram_feed":
        result = await db.execute(
            select(Post).where(
                Post.user_id == user_id,
                Post.platform == "instagram_story",
                Post.id.notin_(linked_ids),
                Post.country == post.country if post.country else True,
            ).order_by(Post.created_at.desc()).limit(5)
        )
        story_posts = result.scalars().all()
        for p in story_posts:
            if p.id not in {s["post"]["id"] for s in suggestions}:
                suggestions.append({
                    "post": post_summary(p),
                    "suggested_type": "cross_reference",
                    "reason": "Story-Post zum gleichen Thema",
                })

    # 3. Same student (if student_id is set)
    if post.student_id:
        result = await db.execute(
            select(Post).where(
                Post.user_id == user_id,
                Post.student_id == post.student_id,
                Post.id.notin_(linked_ids),
            ).order_by(Post.created_at.desc()).limit(5)
        )
        student_posts = result.scalars().all()
        seen_ids = {s["post"]["id"] for s in suggestions}
        for p in student_posts:
            if p.id not in seen_ids:
                suggestions.append({
                    "post": post_summary(p),
                    "suggested_type": "related",
                    "reason": "Gleicher Student",
                })

    # 4. Same country + category
    if post.country:
        result = await db.execute(
            select(Post).where(
                Post.user_id == user_id,
                Post.country == post.country,
                Post.category == post.category,
                Post.id.notin_(linked_ids),
            ).order_by(Post.created_at.desc()).limit(5)
        )
        similar_posts = result.scalars().all()
        seen_ids = {s["post"]["id"] for s in suggestions}
        for p in similar_posts:
            if p.id not in seen_ids:
                suggestions.append({
                    "post": post_summary(p),
                    "suggested_type": "related",
                    "reason": f"Gleiche Kategorie & Land ({post.country})",
                })

    return {
        "post_id": post_id,
        "suggestions": suggestions[:15],  # Limit to 15 suggestions
        "count": min(len(suggestions), 15),
    }
