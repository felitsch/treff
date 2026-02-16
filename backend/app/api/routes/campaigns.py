"""Campaign Management routes — CRUD + AI-powered post plan generation."""

import json
import logging
from datetime import date, timedelta, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.campaign import Campaign
from app.models.campaign_post import CampaignPost
from app.models.post import Post

router = APIRouter()
logger = logging.getLogger(__name__)


# ── Pydantic Schemas ──────────────────────────────────────────────────

class CampaignCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    goal: Optional[str] = None  # awareness, engagement, conversion, traffic
    start_date: Optional[str] = None  # ISO date
    end_date: Optional[str] = None  # ISO date
    platforms: Optional[list[str]] = None  # ["instagram_feed","tiktok"]
    status: Optional[str] = "draft"

class CampaignUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    goal: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    platforms: Optional[list[str]] = None
    status: Optional[str] = None

class CampaignResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: Optional[str] = None
    goal: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    platforms: Optional[list[str]] = None
    status: str
    post_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ── Helpers ───────────────────────────────────────────────────────────

VALID_GOALS = {"awareness", "engagement", "conversion", "traffic"}
VALID_STATUSES = {"draft", "active", "completed"}
VALID_PLATFORMS = {"instagram_feed", "instagram_story", "tiktok"}


def campaign_to_dict(c: Campaign) -> dict:
    """Convert Campaign model to response dict."""
    platforms = None
    if c.platforms:
        try:
            platforms = json.loads(c.platforms)
        except (json.JSONDecodeError, TypeError):
            platforms = []
    return {
        "id": c.id,
        "user_id": c.user_id,
        "title": c.title,
        "description": c.description,
        "goal": c.goal,
        "start_date": c.start_date,
        "end_date": c.end_date,
        "platforms": platforms,
        "status": c.status,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


def campaign_post_to_dict(cp: CampaignPost) -> dict:
    """Convert CampaignPost model to response dict."""
    return {
        "id": cp.id,
        "campaign_id": cp.campaign_id,
        "post_id": cp.post_id,
        "order": cp.order,
        "scheduled_date": cp.scheduled_date,
        "status": cp.status,
        "created_at": cp.created_at.isoformat() if cp.created_at else None,
    }


# ── CONTENT PILLARS for AI generation ────────────────────────────────

CONTENT_PILLARS = {
    "awareness": [
        {"category": "laender_spotlight", "label": "Laender-Spotlight"},
        {"category": "erfahrungsbericht", "label": "Erfahrungsbericht"},
        {"category": "behind_the_scenes", "label": "Behind the Scenes"},
        {"category": "infografik", "label": "Infografik"},
    ],
    "engagement": [
        {"category": "quiz_umfrage", "label": "Quiz / Umfrage"},
        {"category": "meme_humor", "label": "Meme / Humor"},
        {"category": "this_or_that", "label": "This or That"},
        {"category": "erfahrungsbericht", "label": "Erfahrungsbericht"},
    ],
    "conversion": [
        {"category": "fristen_cta", "label": "Fristen & CTA"},
        {"category": "preis_vergleich", "label": "Preis-Vergleich"},
        {"category": "eltern_info", "label": "Eltern-Info"},
        {"category": "faq", "label": "FAQ"},
    ],
    "traffic": [
        {"category": "blog_teaser", "label": "Blog-Teaser"},
        {"category": "webinar_event", "label": "Webinar / Event"},
        {"category": "story_teaser", "label": "Story-Teaser"},
        {"category": "laender_spotlight", "label": "Laender-Spotlight"},
    ],
}

COUNTRIES = ["usa", "kanada", "australien", "neuseeland", "irland"]


# ── POST /api/campaigns — Create new campaign ────────────────────────

@router.post("", status_code=201)
async def create_campaign(
    data: CampaignCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a new marketing campaign."""
    # Validate goal
    if data.goal and data.goal not in VALID_GOALS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid goal. Must be one of: {', '.join(sorted(VALID_GOALS))}"
        )

    # Validate status
    status_val = data.status or "draft"
    if status_val not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(sorted(VALID_STATUSES))}"
        )

    # Validate platforms
    if data.platforms:
        invalid = set(data.platforms) - VALID_PLATFORMS
        if invalid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid platforms: {', '.join(invalid)}. Must be: {', '.join(sorted(VALID_PLATFORMS))}"
            )

    # Validate dates
    if data.start_date:
        try:
            date.fromisoformat(data.start_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Use ISO date (YYYY-MM-DD).")
    if data.end_date:
        try:
            date.fromisoformat(data.end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use ISO date (YYYY-MM-DD).")

    campaign = Campaign(
        user_id=user_id,
        title=data.title,
        description=data.description,
        goal=data.goal,
        start_date=data.start_date,
        end_date=data.end_date,
        platforms=json.dumps(data.platforms) if data.platforms else None,
        status=status_val,
    )
    db.add(campaign)
    await db.flush()
    await db.refresh(campaign)
    await db.commit()

    result = campaign_to_dict(campaign)
    result["post_count"] = 0
    return result


# ── GET /api/campaigns — List all campaigns ──────────────────────────

@router.get("")
async def list_campaigns(
    status: Optional[str] = Query(None),
    goal: Optional[str] = Query(None),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List all campaigns for the current user, with optional status/goal filters."""
    where = [Campaign.user_id == user_id]
    if status:
        if status not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status filter: {status}")
        where.append(Campaign.status == status)
    if goal:
        if goal not in VALID_GOALS:
            raise HTTPException(status_code=400, detail=f"Invalid goal filter: {goal}")
        where.append(Campaign.goal == goal)

    query = select(Campaign).where(*where).order_by(Campaign.created_at.desc())
    result = await db.execute(query)
    campaigns = result.scalars().all()

    # Enrich with post counts
    response = []
    for c in campaigns:
        c_dict = campaign_to_dict(c)
        count_result = await db.execute(
            select(func.count(CampaignPost.id)).where(CampaignPost.campaign_id == c.id)
        )
        c_dict["post_count"] = count_result.scalar() or 0
        response.append(c_dict)

    return response


# ── GET /api/campaigns/:id — Campaign detail with posts ──────────────

@router.get("/{campaign_id}")
async def get_campaign(
    campaign_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a single campaign with all its associated posts."""
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.user_id == user_id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    c_dict = campaign_to_dict(campaign)

    # Get campaign posts with linked post info
    cp_result = await db.execute(
        select(CampaignPost)
        .where(CampaignPost.campaign_id == campaign_id)
        .order_by(CampaignPost.order)
    )
    campaign_posts = cp_result.scalars().all()

    posts_list = []
    for cp in campaign_posts:
        cp_dict = campaign_post_to_dict(cp)

        # Get linked post details if available
        if cp.post_id:
            post_result = await db.execute(
                select(Post).where(Post.id == cp.post_id)
            )
            post = post_result.scalar_one_or_none()
            if post:
                cp_dict["post_title"] = post.title
                cp_dict["post_status"] = post.status
                cp_dict["post_category"] = post.category
                cp_dict["post_platform"] = post.platform
                cp_dict["post_country"] = post.country
                cp_dict["post_scheduled_date"] = post.scheduled_date.isoformat() if post.scheduled_date else None
            else:
                cp_dict["post_title"] = None
                cp_dict["post_status"] = None
                cp_dict["post_category"] = None
                cp_dict["post_platform"] = None
                cp_dict["post_country"] = None
                cp_dict["post_scheduled_date"] = None
        else:
            cp_dict["post_title"] = None
            cp_dict["post_status"] = None
            cp_dict["post_category"] = None
            cp_dict["post_platform"] = None
            cp_dict["post_country"] = None
            cp_dict["post_scheduled_date"] = None

        posts_list.append(cp_dict)

    c_dict["posts"] = posts_list
    c_dict["post_count"] = len(posts_list)

    return c_dict


# ── PUT /api/campaigns/:id — Update campaign ─────────────────────────

@router.put("/{campaign_id}")
async def update_campaign(
    campaign_id: int,
    data: CampaignUpdate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update campaign details."""
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.user_id == user_id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Validate goal
    if data.goal is not None and data.goal not in VALID_GOALS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid goal. Must be one of: {', '.join(sorted(VALID_GOALS))}"
        )

    # Validate status
    if data.status is not None and data.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(sorted(VALID_STATUSES))}"
        )

    # Validate platforms
    if data.platforms is not None:
        invalid = set(data.platforms) - VALID_PLATFORMS
        if invalid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid platforms: {', '.join(invalid)}. Must be: {', '.join(sorted(VALID_PLATFORMS))}"
            )

    # Update fields
    if data.title is not None:
        campaign.title = data.title
    if data.description is not None:
        campaign.description = data.description
    if data.goal is not None:
        campaign.goal = data.goal
    if data.start_date is not None:
        campaign.start_date = data.start_date
    if data.end_date is not None:
        campaign.end_date = data.end_date
    if data.platforms is not None:
        campaign.platforms = json.dumps(data.platforms)
    if data.status is not None:
        campaign.status = data.status

    await db.flush()
    await db.refresh(campaign)
    await db.commit()

    c_dict = campaign_to_dict(campaign)
    count_result = await db.execute(
        select(func.count(CampaignPost.id)).where(CampaignPost.campaign_id == campaign.id)
    )
    c_dict["post_count"] = count_result.scalar() or 0

    return c_dict


# ── DELETE /api/campaigns/:id — Delete campaign ──────────────────────

@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a campaign and its campaign_posts entries (linked posts are kept)."""
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.user_id == user_id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    await db.delete(campaign)
    await db.commit()
    return {"message": "Campaign deleted", "id": campaign_id}


# ── POST /api/campaigns/:id/generate — AI post plan generation ───────

@router.post("/{campaign_id}/generate")
async def generate_campaign_posts(
    campaign_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """AI-powered: generate a post plan based on campaign goal, timeframe and content pillars.

    Creates CampaignPost entries (no actual Posts yet) with suggested categories,
    platforms, countries, and scheduled dates spread across the campaign period.
    """
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.user_id == user_id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Determine campaign parameters
    goal = campaign.goal or "awareness"
    pillars = CONTENT_PILLARS.get(goal, CONTENT_PILLARS["awareness"])

    # Parse platforms
    platforms = []
    if campaign.platforms:
        try:
            platforms = json.loads(campaign.platforms)
        except (json.JSONDecodeError, TypeError):
            pass
    if not platforms:
        platforms = ["instagram_feed"]

    # Parse date range
    try:
        start = date.fromisoformat(campaign.start_date) if campaign.start_date else date.today()
    except ValueError:
        start = date.today()

    try:
        end = date.fromisoformat(campaign.end_date) if campaign.end_date else start + timedelta(days=14)
    except ValueError:
        end = start + timedelta(days=14)

    if end <= start:
        end = start + timedelta(days=14)

    # Calculate number of posts: roughly one every 2 days, min 3, max 20
    total_days = (end - start).days
    num_posts = max(3, min(20, total_days // 2))

    # Delete existing campaign posts before regenerating
    existing_cps = await db.execute(
        select(CampaignPost).where(CampaignPost.campaign_id == campaign_id)
    )
    for cp in existing_cps.scalars().all():
        await db.delete(cp)
    await db.flush()

    # Generate post plan
    generated_posts = []
    for i in range(num_posts):
        # Spread dates evenly across the campaign period
        if num_posts > 1:
            day_offset = int(i * total_days / (num_posts - 1))
        else:
            day_offset = 0
        post_date = start + timedelta(days=day_offset)

        # Cycle through content pillars
        pillar = pillars[i % len(pillars)]

        # Cycle through platforms
        platform = platforms[i % len(platforms)]

        # Distribute countries evenly
        country = COUNTRIES[i % len(COUNTRIES)]

        cp = CampaignPost(
            campaign_id=campaign_id,
            order=i + 1,
            scheduled_date=post_date.isoformat(),
            status="planned",
        )
        db.add(cp)
        generated_posts.append({
            "order": i + 1,
            "scheduled_date": post_date.isoformat(),
            "suggested_category": pillar["category"],
            "suggested_category_label": pillar["label"],
            "suggested_platform": platform,
            "suggested_country": country,
            "status": "planned",
        })

    await db.flush()
    await db.commit()

    # Re-fetch to get IDs
    cp_result = await db.execute(
        select(CampaignPost)
        .where(CampaignPost.campaign_id == campaign_id)
        .order_by(CampaignPost.order)
    )
    campaign_posts = cp_result.scalars().all()

    # Merge IDs into generated_posts
    for idx, cp in enumerate(campaign_posts):
        if idx < len(generated_posts):
            generated_posts[idx]["id"] = cp.id
            generated_posts[idx]["campaign_post_id"] = cp.id

    return {
        "campaign_id": campaign_id,
        "goal": goal,
        "total_posts": num_posts,
        "date_range": {"start": start.isoformat(), "end": end.isoformat()},
        "posts": generated_posts,
    }
