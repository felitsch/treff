"""Analytics routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.post import Post

router = APIRouter()


@router.get("/overview")
async def get_overview(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get analytics overview: total posts, this week, this month."""
    total_result = await db.execute(
        select(func.count(Post.id)).where(Post.user_id == user_id)
    )
    total = total_result.scalar() or 0

    return {
        "total_posts": total,
        "posts_this_week": 0,  # TODO: Calculate
        "posts_this_month": 0,  # TODO: Calculate
    }


@router.get("/frequency")
async def get_frequency(
    period: str = "week",
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get posting frequency over time."""
    # TODO: Implement time-based aggregation
    return {"period": period, "data": []}


@router.get("/categories")
async def get_categories(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get category distribution."""
    result = await db.execute(
        select(Post.category, func.count(Post.id))
        .where(Post.user_id == user_id)
        .group_by(Post.category)
    )
    return [{"category": row[0], "count": row[1]} for row in result.all()]


@router.get("/platforms")
async def get_platforms(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get platform distribution."""
    result = await db.execute(
        select(Post.platform, func.count(Post.id))
        .where(Post.user_id == user_id)
        .group_by(Post.platform)
    )
    return [{"platform": row[0], "count": row[1]} for row in result.all()]


@router.get("/countries")
async def get_countries(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get country distribution."""
    result = await db.execute(
        select(Post.country, func.count(Post.id))
        .where(Post.user_id == user_id, Post.country.isnot(None))
        .group_by(Post.country)
    )
    return [{"country": row[0], "count": row[1]} for row in result.all()]


@router.get("/templates")
async def get_template_usage(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get most used templates."""
    result = await db.execute(
        select(Post.template_id, func.count(Post.id))
        .where(Post.user_id == user_id, Post.template_id.isnot(None))
        .group_by(Post.template_id)
        .order_by(func.count(Post.id).desc())
    )
    return [{"template_id": row[0], "count": row[1]} for row in result.all()]


@router.get("/goals")
async def get_goals(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get weekly/monthly targets vs actual."""
    # TODO: Read goals from settings
    return {
        "weekly_target": 4,
        "weekly_actual": 0,
        "monthly_target": 16,
        "monthly_actual": 0,
    }
