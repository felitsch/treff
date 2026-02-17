"""Analytics routes.

Dashboard analytics: category distribution, platform breakdown, country mix,
posting frequency, template usage, content mix balance, and goal tracking.
"""

import csv
import io
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.core.cache import api_cache
from app.models.post import Post
from app.models.asset import Asset
from app.models.calendar_entry import CalendarEntry
from app.models.content_suggestion import ContentSuggestion
from app.models.setting import Setting
from app.models.campaign import Campaign
from app.models.campaign_post import CampaignPost
from app.models.pipeline_item import PipelineItem
from app.models.student import Student

router = APIRouter()


@router.get("/overview")
async def get_overview(
    request: Request,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get analytics overview: total posts, this week, this month.
    Cached for 5 minutes."""
    cache_key = api_cache._build_key("overview", {"user_id": user_id})
    entry = api_cache.get(cache_key)
    if entry is not None:
        if_none_match = request.headers.get("if-none-match")
        if if_none_match and if_none_match.strip('"') == entry.etag:
            return JSONResponse(status_code=304, content=None, headers={
                "ETag": f'"{entry.etag}"', "Cache-Control": f"private, max-age={entry.remaining_ttl}", "X-Cache": "HIT",
            })
        return JSONResponse(content=entry.value, headers={
            "ETag": f'"{entry.etag}"', "Cache-Control": f"private, max-age={entry.remaining_ttl}",
            "X-Cache": "HIT", "X-Cache-Age": str(entry.age_seconds),
        })

    now = datetime.now(timezone.utc)
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    total_result = await db.execute(
        select(func.count(Post.id)).where(Post.user_id == user_id)
    )
    total = total_result.scalar() or 0

    week_result = await db.execute(
        select(func.count(Post.id)).where(
            Post.user_id == user_id,
            Post.created_at >= week_start,
        )
    )
    posts_this_week = week_result.scalar() or 0

    month_result = await db.execute(
        select(func.count(Post.id)).where(
            Post.user_id == user_id,
            Post.created_at >= month_start,
        )
    )
    posts_this_month = month_result.scalar() or 0

    data = {
        "total_posts": total,
        "posts_this_week": posts_this_week,
        "posts_this_month": posts_this_month,
    }
    new_entry = api_cache.set(cache_key, data)
    return JSONResponse(content=data, headers={
        "ETag": f'"{new_entry.etag}"', "Cache-Control": "private, max-age=300", "X-Cache": "MISS",
    })


@router.get("/dashboard")
async def get_dashboard_data(
    request: Request,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get all dashboard data in a single API call. Cached for 5 minutes."""
    cache_key = api_cache._build_key("dashboard", {"user_id": user_id})
    entry = api_cache.get(cache_key)
    if entry is not None:
        if_none_match = request.headers.get("if-none-match")
        if if_none_match and if_none_match.strip('"') == entry.etag:
            return JSONResponse(status_code=304, content=None, headers={
                "ETag": f'"{entry.etag}"', "Cache-Control": f"private, max-age={entry.remaining_ttl}", "X-Cache": "HIT",
            })
        return JSONResponse(content=entry.value, headers={
            "ETag": f'"{entry.etag}"', "Cache-Control": f"private, max-age={entry.remaining_ttl}",
            "X-Cache": "HIT", "X-Cache-Age": str(entry.age_seconds),
        })

    now = datetime.now(timezone.utc)
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

    # Quick stats
    total_result = await db.execute(
        select(func.count(Post.id)).where(Post.user_id == user_id)
    )
    total_posts = total_result.scalar() or 0

    week_result = await db.execute(
        select(func.count(Post.id)).where(
            Post.user_id == user_id,
            Post.created_at >= week_start,
        )
    )
    posts_this_week = week_result.scalar() or 0

    scheduled_result = await db.execute(
        select(func.count(Post.id)).where(
            Post.user_id == user_id,
            Post.status == "scheduled",
        )
    )
    scheduled_posts = scheduled_result.scalar() or 0

    # Drafts count
    drafts_result = await db.execute(
        select(func.count(Post.id)).where(
            Post.user_id == user_id,
            Post.status == "draft",
        )
    )
    draft_posts = drafts_result.scalar() or 0

    asset_result = await db.execute(
        select(func.count(Asset.id)).where(Asset.user_id == user_id)
    )
    total_assets = asset_result.scalar() or 0

    # Recent posts (last 8) with thumbnail info
    recent_result = await db.execute(
        select(Post)
        .where(Post.user_id == user_id)
        .order_by(Post.created_at.desc())
        .limit(8)
    )
    recent_posts_raw = recent_result.scalars().all()

    import json as _json

    recent_posts = []
    for p in recent_posts_raw:
        # Extract first slide thumbnail from slide_data
        thumbnail_url = None
        try:
            slides = _json.loads(p.slide_data) if p.slide_data else []
            if slides and isinstance(slides, list) and len(slides) > 0:
                first_slide = slides[0]
                thumbnail_url = first_slide.get("background_image") or first_slide.get("image_url") or first_slide.get("thumbnail")
        except (ValueError, TypeError, KeyError):
            pass

        recent_posts.append({
            "id": p.id,
            "title": p.title,
            "category": p.category,
            "platform": p.platform,
            "status": p.status,
            "country": p.country,
            "thumbnail_url": thumbnail_url,
            "slide_count": len(_json.loads(p.slide_data)) if p.slide_data else 0,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        })

    # Mini calendar: scheduled posts for the next 7 days
    today = now.date()
    next_week = today + timedelta(days=7)
    calendar_result = await db.execute(
        select(CalendarEntry).where(
            CalendarEntry.scheduled_date >= today,
            CalendarEntry.scheduled_date <= next_week,
        )
    )
    calendar_entries_raw = calendar_result.scalars().all()
    calendar_entries = [
        {
            "id": e.id,
            "post_id": e.post_id,
            "scheduled_date": e.scheduled_date.isoformat() if e.scheduled_date else None,
            "scheduled_time": e.scheduled_time,
            "notes": e.notes,
        }
        for e in calendar_entries_raw
    ]

    # Content suggestions (pending, latest 5)
    suggestions_result = await db.execute(
        select(ContentSuggestion)
        .where(ContentSuggestion.status == "pending")
        .order_by(ContentSuggestion.created_at.desc())
        .limit(5)
    )
    suggestions_raw = suggestions_result.scalars().all()
    suggestions = [
        {
            "id": s.id,
            "suggestion_type": s.suggestion_type,
            "title": s.title,
            "description": s.description,
            "suggested_category": s.suggested_category,
            "suggested_country": s.suggested_country,
            "suggested_date": s.suggested_date.isoformat() if s.suggested_date else None,
            "suggested_format": getattr(s, "suggested_format", None),
            "reason": s.reason,
            "status": s.status,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in suggestions_raw
    ]

    data = {
        "stats": {
            "posts_this_week": posts_this_week,
            "scheduled_posts": scheduled_posts,
            "draft_posts": draft_posts,
            "total_assets": total_assets,
            "total_posts": total_posts,
        },
        "recent_posts": recent_posts,
        "calendar_entries": calendar_entries,
        "suggestions": suggestions,
    }
    new_entry = api_cache.set(cache_key, data)
    return JSONResponse(content=data, headers={
        "ETag": f'"{new_entry.etag}"', "Cache-Control": "private, max-age=300", "X-Cache": "MISS",
    })


@router.get("/frequency")
async def get_frequency(
    period: str = "week",
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get posting frequency over time.

    Args:
        period: Time period for aggregation.
            - "week": Last 7 days, grouped by day
            - "month": Last 30 days, grouped by day
            - "quarter": Last 90 days, grouped by week
            - "year": Last 365 days, grouped by month
    """
    now = datetime.now(timezone.utc)

    # Determine date range and grouping
    if period == "week":
        start_date = now - timedelta(days=6)
        days_count = 7
    elif period == "month":
        start_date = now - timedelta(days=29)
        days_count = 30
    elif period == "quarter":
        start_date = now - timedelta(days=89)
        days_count = 90
    elif period == "year":
        start_date = now - timedelta(days=364)
        days_count = 365
    else:
        start_date = now - timedelta(days=6)
        days_count = 7

    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

    # Query posts in the date range
    result = await db.execute(
        select(Post.created_at).where(
            Post.user_id == user_id,
            Post.created_at >= start_date,
        )
    )
    post_dates = [row[0] for row in result.all()]

    # Build data points
    data = []

    if period in ("week", "month"):
        # Group by day
        for i in range(days_count):
            day = (start_date + timedelta(days=i)).date()
            count = sum(1 for d in post_dates if d.date() == day)
            data.append({
                "label": day.strftime("%d.%m."),
                "date": day.isoformat(),
                "count": count,
            })
    elif period == "quarter":
        # Group by week (13 weeks)
        for week_num in range(13):
            week_start = start_date + timedelta(weeks=week_num)
            week_end = week_start + timedelta(days=6)
            count = sum(
                1 for d in post_dates
                if week_start.date() <= d.date() <= week_end.date()
            )
            data.append({
                "label": f"KW {week_start.strftime('%d.%m.')}",
                "date": week_start.date().isoformat(),
                "count": count,
            })
    elif period == "year":
        # Group by month (12 months)
        for month_offset in range(12):
            month_start_date = now - timedelta(days=364) + timedelta(days=month_offset * 30)
            # Use actual month boundaries
            m = (now.month - 11 + month_offset) % 12
            if m == 0:
                m = 12
            y = now.year if (now.month - 11 + month_offset) > 0 else now.year - 1
            month_names = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
                           "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
            count = sum(
                1 for d in post_dates
                if d.month == m and d.year == y
            )
            data.append({
                "label": month_names[m - 1],
                "date": f"{y}-{m:02d}-01",
                "count": count,
            })

    return {"period": period, "data": data}


@router.get("/categories")
async def get_categories(
    request: Request,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get category distribution. Cached for 15 minutes."""
    cache_key = api_cache._build_key("categories", {"user_id": user_id})
    entry = api_cache.get(cache_key)
    if entry is not None:
        return JSONResponse(content=entry.value, headers={
            "ETag": f'"{entry.etag}"', "Cache-Control": f"private, max-age={entry.remaining_ttl}",
            "X-Cache": "HIT", "X-Cache-Age": str(entry.age_seconds),
        })

    result = await db.execute(
        select(Post.category, func.count(Post.id))
        .where(Post.user_id == user_id)
        .group_by(Post.category)
    )
    data = [{"category": row[0], "count": row[1]} for row in result.all()]
    new_entry = api_cache.set(cache_key, data)
    return JSONResponse(content=data, headers={
        "ETag": f'"{new_entry.etag}"', "Cache-Control": "private, max-age=900", "X-Cache": "MISS",
    })


@router.get("/platforms")
async def get_platforms(
    request: Request,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get platform distribution. Cached for 15 minutes."""
    cache_key = api_cache._build_key("platforms", {"user_id": user_id})
    entry = api_cache.get(cache_key)
    if entry is not None:
        return JSONResponse(content=entry.value, headers={
            "ETag": f'"{entry.etag}"', "Cache-Control": f"private, max-age={entry.remaining_ttl}",
            "X-Cache": "HIT", "X-Cache-Age": str(entry.age_seconds),
        })

    result = await db.execute(
        select(Post.platform, func.count(Post.id))
        .where(Post.user_id == user_id)
        .group_by(Post.platform)
    )
    data = [{"platform": row[0], "count": row[1]} for row in result.all()]
    new_entry = api_cache.set(cache_key, data)
    return JSONResponse(content=data, headers={
        "ETag": f'"{new_entry.etag}"', "Cache-Control": "private, max-age=900", "X-Cache": "MISS",
    })


@router.get("/countries")
async def get_countries(
    request: Request,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get country distribution. Cached for 15 minutes."""
    cache_key = api_cache._build_key("countries", {"user_id": user_id})
    entry = api_cache.get(cache_key)
    if entry is not None:
        return JSONResponse(content=entry.value, headers={
            "ETag": f'"{entry.etag}"', "Cache-Control": f"private, max-age={entry.remaining_ttl}",
            "X-Cache": "HIT", "X-Cache-Age": str(entry.age_seconds),
        })

    result = await db.execute(
        select(Post.country, func.count(Post.id))
        .where(Post.user_id == user_id, Post.country.isnot(None))
        .group_by(Post.country)
    )
    data = [{"country": row[0], "count": row[1]} for row in result.all()]
    new_entry = api_cache.set(cache_key, data)
    return JSONResponse(content=data, headers={
        "ETag": f'"{new_entry.etag}"', "Cache-Control": "private, max-age=900", "X-Cache": "MISS",
    })


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
    """Get weekly/monthly targets vs actual.

    Reads target values from user settings (posts_per_week, posts_per_month).
    Falls back to defaults (4/week, 16/month) if no settings exist.
    """
    now = datetime.now(timezone.utc)
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Read user-configured targets from settings
    settings_result = await db.execute(
        select(Setting).where(
            Setting.user_id == user_id,
            Setting.key.in_(["posts_per_week", "posts_per_month"]),
        )
    )
    user_settings = {s.key: s.value for s in settings_result.scalars().all()}

    # Parse targets with defaults
    try:
        weekly_target = int(user_settings.get("posts_per_week", "4"))
    except (ValueError, TypeError):
        weekly_target = 4

    try:
        monthly_target = int(user_settings.get("posts_per_month", "16"))
    except (ValueError, TypeError):
        monthly_target = 16

    week_result = await db.execute(
        select(func.count(Post.id)).where(
            Post.user_id == user_id,
            Post.created_at >= week_start,
        )
    )
    weekly_actual = week_result.scalar() or 0

    month_result = await db.execute(
        select(func.count(Post.id)).where(
            Post.user_id == user_id,
            Post.created_at >= month_start,
        )
    )
    monthly_actual = month_result.scalar() or 0

    return {
        "weekly_target": weekly_target,
        "weekly_actual": weekly_actual,
        "monthly_target": monthly_target,
        "monthly_actual": monthly_actual,
    }


@router.get("/content-mix")
async def get_content_mix(
    period: str = "week",
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get content mix analysis for donut/bar charts, warnings, and recommendations.

    Args:
        period: 'week' or 'month' (default: 'week')

    Returns:
        categories: distribution by category
        platforms: distribution by platform/format
        countries: distribution by country
        days_of_week: posts per day of week (Mo-So)
        has_story_arc: count of posts that belong to a story arc
        total: total posts in period
        warnings: list of imbalance warnings
        recommendations: list of content recommendations
    """
    import json as json_module

    now = datetime.now(timezone.utc)

    if period == "month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        period_label = "diesen Monat"
    else:
        # Current week (Mon-Sun)
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        period_label = "diese Woche"

    # Fetch all posts in the period
    result = await db.execute(
        select(Post).where(
            Post.user_id == user_id,
            Post.created_at >= start,
        )
    )
    posts = result.scalars().all()
    total = len(posts)

    # Category distribution
    cat_counts = {}
    for p in posts:
        cat = p.category or "unbekannt"
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
    categories = [{"category": k, "count": v} for k, v in sorted(cat_counts.items(), key=lambda x: -x[1])]

    # Platform distribution
    plat_counts = {}
    for p in posts:
        plat = p.platform or "unbekannt"
        plat_counts[plat] = plat_counts.get(plat, 0) + 1
    platforms = [{"platform": k, "count": v} for k, v in sorted(plat_counts.items(), key=lambda x: -x[1])]

    # Country distribution
    country_counts = {}
    for p in posts:
        if p.country:
            country_counts[p.country] = country_counts.get(p.country, 0) + 1
    countries = [{"country": k, "count": v} for k, v in sorted(country_counts.items(), key=lambda x: -x[1])]

    # Posts per day of week (0=Monday, 6=Sunday)
    day_names_de = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
    day_counts = [0] * 7
    for p in posts:
        if p.scheduled_date:
            dow = p.scheduled_date.weekday()  # 0=Monday
            day_counts[dow] += 1
        elif p.created_at:
            dow = p.created_at.weekday()
            day_counts[dow] += 1
    days_of_week = [{"day": day_names_de[i], "day_index": i, "count": day_counts[i]} for i in range(7)]

    # Story arc posts count
    arc_count = sum(1 for p in posts if p.story_arc_id)
    single_count = total - arc_count

    # Read user target-mix settings
    settings_result = await db.execute(
        select(Setting).where(
            Setting.user_id == user_id,
            Setting.key.in_([
                "posts_per_week", "posts_per_month",
                "target_mix_categories", "target_mix_platforms", "target_mix_countries",
            ]),
        )
    )
    user_settings = {s.key: s.value for s in settings_result.scalars().all()}

    # Parse target mix (JSON strings)
    target_categories = {}
    target_platforms = {}
    target_countries = {}
    try:
        target_categories = json_module.loads(user_settings.get("target_mix_categories", "{}"))
    except (json_module.JSONDecodeError, TypeError):
        pass
    try:
        target_platforms = json_module.loads(user_settings.get("target_mix_platforms", "{}"))
    except (json_module.JSONDecodeError, TypeError):
        pass
    try:
        target_countries = json_module.loads(user_settings.get("target_mix_countries", "{}"))
    except (json_module.JSONDecodeError, TypeError):
        pass

    # Generate warnings
    warnings = []

    # All known countries
    all_countries = ["usa", "canada", "australia", "newzealand", "ireland"]
    all_platforms = ["instagram_feed", "instagram_story", "tiktok"]
    platform_labels = {
        "instagram_feed": "Instagram Feed",
        "instagram_story": "Instagram Story",
        "tiktok": "TikTok",
    }
    country_labels = {
        "usa": "USA",
        "canada": "Kanada",
        "australia": "Australien",
        "newzealand": "Neuseeland",
        "ireland": "Irland",
    }

    if total > 0:
        # Warn about missing platforms
        for plat in all_platforms:
            if plat not in plat_counts:
                warnings.append({
                    "type": "missing_platform",
                    "severity": "warning",
                    "message": f"Kein {platform_labels.get(plat, plat)}-Post {period_label}",
                    "icon": "⚠️",
                })

        # Warn about missing countries
        covered_countries = set(country_counts.keys())
        missing_countries = [c for c in all_countries if c not in covered_countries]
        if missing_countries and total >= 3:
            names = ", ".join(country_labels.get(c, c) for c in missing_countries[:3])
            warnings.append({
                "type": "missing_countries",
                "severity": "info",
                "message": f"Keine Posts fuer: {names}",
                "icon": "🌍",
            })

        # Warn about too many consecutive series posts (story arcs)
        if arc_count > 0 and single_count == 0 and total >= 3:
            warnings.append({
                "type": "arc_heavy",
                "severity": "warning",
                "message": f"Nur Serien-Posts {period_label} - mehr Einzelposts einplanen",
                "icon": "📖",
            })

        # Warn about category concentration (one category >60%)
        for cat_entry in categories:
            pct = (cat_entry["count"] / total) * 100
            if pct > 60 and total >= 3:
                cat_label_map = {
                    "laender_spotlight": "Laender-Spotlight",
                    "erfahrungsberichte": "Erfahrungsberichte",
                    "infografiken": "Infografiken",
                    "fristen_cta": "Fristen/CTA",
                    "tipps_tricks": "Tipps & Tricks",
                    "faq": "FAQ",
                    "foto_posts": "Foto-Posts",
                    "reel_tiktok_thumbnails": "Reels/TikTok",
                    "story_posts": "Story-Posts",
                    "story_teaser": "Story-Teaser",
                }
                warnings.append({
                    "type": "category_heavy",
                    "severity": "warning",
                    "message": f"{cat_label_map.get(cat_entry['category'], cat_entry['category'])} macht {int(pct)}% aus",
                    "icon": "📊",
                })
                break  # Only warn for the top one

        # Warn if days are very uneven
        active_days = [d for d in day_counts if d > 0]
        if len(active_days) > 0 and total >= 5:
            max_day = max(day_counts)
            if max_day >= total * 0.6:
                peak_idx = day_counts.index(max_day)
                warnings.append({
                    "type": "day_concentration",
                    "severity": "info",
                    "message": f"{int(max_day / total * 100)}% der Posts am {day_names_de[peak_idx]}",
                    "icon": "📅",
                })

    # Generate recommendations
    recommendations = []
    if total == 0:
        recommendations.append({
            "type": "start",
            "message": f"Erstelle deinen ersten Post fuer {period_label}!",
            "icon": "🚀",
        })
    else:
        # Recommend missing country
        if missing_countries:
            country_name = country_labels.get(missing_countries[0], missing_countries[0])
            recommendations.append({
                "type": "country",
                "message": f"Plane einen {country_name}-Post ein",
                "icon": "🌍",
            })

        # Recommend missing platform
        missing_plats = [p for p in all_platforms if p not in plat_counts]
        if missing_plats:
            plat_name = platform_labels.get(missing_plats[0], missing_plats[0])
            recommendations.append({
                "type": "platform",
                "message": f"Erstelle einen {plat_name}-Post",
                "icon": "📱",
            })

        # Recommend posting on empty days
        empty_weekdays = [day_names_de[i] for i in range(5) if day_counts[i] == 0]  # Mon-Fri
        if empty_weekdays and len(empty_weekdays) <= 3:
            recommendations.append({
                "type": "day",
                "message": f"Schlage vor: {empty_weekdays[0]} einen Post einzuplanen",
                "icon": "📅",
            })

        # Recommend more variety if heavy on one category
        if categories and total >= 3:
            top_cat = categories[0]
            pct = (top_cat["count"] / total) * 100
            if pct > 50:
                other_cats = {
                    "laender_spotlight": "Tipps & Tricks",
                    "erfahrungsberichte": "Infografiken",
                    "infografiken": "Erfahrungsberichte",
                    "fristen_cta": "Laender-Spotlight",
                    "tipps_tricks": "FAQ",
                    "faq": "Foto-Posts",
                    "foto_posts": "Reels",
                    "reel_tiktok_thumbnails": "Laender-Spotlight",
                    "story_posts": "Infografiken",
                    "story_teaser": "Erfahrungsberichte",
                }
                suggestion = other_cats.get(top_cat["category"], "andere Kategorien")
                recommendations.append({
                    "type": "variety",
                    "message": f"Mehr Abwechslung: {suggestion} ausprobieren",
                    "icon": "🎨",
                })

    return {
        "period": period,
        "period_label": period_label,
        "total": total,
        "categories": categories,
        "platforms": platforms,
        "countries": countries,
        "days_of_week": days_of_week,
        "story_arc_posts": arc_count,
        "single_posts": single_count,
        "warnings": warnings,
        "recommendations": recommendations,
        "target_mix": {
            "categories": target_categories,
            "platforms": target_platforms,
            "countries": target_countries,
        },
    }


@router.put("/performance/{post_id}")
async def update_performance(
    post_id: int,
    data: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update performance metrics for a specific post (manually entered).

    Body:
    - likes: int (optional)
    - comments: int (optional)
    - shares: int (optional)
    - saves: int (optional)
    - reach: int (optional)
    """
    result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Post not found")

    # Update only provided fields
    field_map = {
        "likes": "perf_likes",
        "comments": "perf_comments",
        "shares": "perf_shares",
        "saves": "perf_saves",
        "reach": "perf_reach",
    }
    for key, col in field_map.items():
        if key in data:
            val = data[key]
            if val is not None:
                val = max(0, int(val))
            setattr(post, col, val)

    post.perf_updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(post)

    # Calculate engagement rate
    likes = post.perf_likes or 0
    comments = post.perf_comments or 0
    shares = post.perf_shares or 0
    reach = post.perf_reach or 0
    engagement_rate = round(((likes + comments + shares) / reach) * 100, 2) if reach > 0 else None

    return {
        "id": post.id,
        "perf_likes": post.perf_likes,
        "perf_comments": post.perf_comments,
        "perf_shares": post.perf_shares,
        "perf_saves": post.perf_saves,
        "perf_reach": post.perf_reach,
        "perf_updated_at": post.perf_updated_at.isoformat() if post.perf_updated_at else None,
        "engagement_rate": engagement_rate,
    }


@router.get("/performance/{post_id}")
async def get_performance(
    post_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get performance metrics for a specific post."""
    result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Post not found")

    likes = post.perf_likes or 0
    comments = post.perf_comments or 0
    shares = post.perf_shares or 0
    reach = post.perf_reach or 0
    engagement_rate = round(((likes + comments + shares) / reach) * 100, 2) if reach > 0 else None

    return {
        "id": post.id,
        "title": post.title,
        "perf_likes": post.perf_likes,
        "perf_comments": post.perf_comments,
        "perf_shares": post.perf_shares,
        "perf_saves": post.perf_saves,
        "perf_reach": post.perf_reach,
        "perf_updated_at": post.perf_updated_at.isoformat() if post.perf_updated_at else None,
        "engagement_rate": engagement_rate,
    }


@router.get("/top-posts")
async def get_top_posts(
    sort_by: Optional[str] = Query(default="engagement_rate", pattern="^(engagement_rate|likes|comments|shares|saves|reach)$"),
    limit: int = Query(default=10, ge=1, le=50),
    period: Optional[str] = Query(default=None, pattern="^(week|month|quarter|year)$"),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get top-performing posts ranked by engagement rate or specific metric.

    Args:
        sort_by: Metric to sort by (engagement_rate, likes, comments, shares, saves, reach)
        limit: Number of posts to return (max 50)
        period: Optional time period filter (week, month, quarter, year)
    """
    now = datetime.now(timezone.utc)
    conditions = [Post.user_id == user_id]

    # At least one performance metric must be set
    conditions.append(
        (Post.perf_likes.isnot(None)) |
        (Post.perf_comments.isnot(None)) |
        (Post.perf_shares.isnot(None)) |
        (Post.perf_reach.isnot(None))
    )

    # Apply period filter
    if period:
        period_map = {
            "week": timedelta(days=7),
            "month": timedelta(days=30),
            "quarter": timedelta(days=90),
            "year": timedelta(days=365),
        }
        start_date = now - period_map.get(period, timedelta(days=30))
        conditions.append(Post.created_at >= start_date)

    result = await db.execute(
        select(Post).where(*conditions)
    )
    posts = result.scalars().all()

    # Build ranked list with computed engagement rate
    import json as _json
    ranked = []
    for p in posts:
        likes = p.perf_likes or 0
        comments = p.perf_comments or 0
        shares = p.perf_shares or 0
        saves = p.perf_saves or 0
        reach = p.perf_reach or 0
        eng_rate = round(((likes + comments + shares) / reach) * 100, 2) if reach > 0 else 0.0

        # Get thumbnail
        thumbnail_url = None
        try:
            slides = _json.loads(p.slide_data) if p.slide_data else []
            if slides and isinstance(slides, list) and len(slides) > 0:
                first_slide = slides[0]
                thumbnail_url = first_slide.get("background_image") or first_slide.get("image_url") or first_slide.get("thumbnail")
        except (ValueError, TypeError, KeyError):
            pass

        ranked.append({
            "id": p.id,
            "title": p.title,
            "category": p.category,
            "platform": p.platform,
            "country": p.country,
            "status": p.status,
            "thumbnail_url": thumbnail_url,
            "perf_likes": p.perf_likes,
            "perf_comments": p.perf_comments,
            "perf_shares": p.perf_shares,
            "perf_saves": p.perf_saves,
            "perf_reach": p.perf_reach,
            "engagement_rate": eng_rate,
            "perf_updated_at": p.perf_updated_at.isoformat() if p.perf_updated_at else None,
            "posted_at": p.posted_at.isoformat() if p.posted_at else None,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        })

    # Sort by chosen metric
    sort_map = {
        "engagement_rate": lambda x: x["engagement_rate"],
        "likes": lambda x: x["perf_likes"] or 0,
        "comments": lambda x: x["perf_comments"] or 0,
        "shares": lambda x: x["perf_shares"] or 0,
        "saves": lambda x: x["perf_saves"] or 0,
        "reach": lambda x: x["perf_reach"] or 0,
    }
    sort_fn = sort_map.get(sort_by, sort_map["engagement_rate"])
    ranked.sort(key=sort_fn, reverse=True)

    return {
        "posts": ranked[:limit],
        "total_with_metrics": len(ranked),
        "sort_by": sort_by,
    }


@router.get("/performance-trend")
async def get_performance_trend(
    period: str = Query(default="month", pattern="^(week|month|quarter|year)$"),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated performance metrics over time for trend analysis.

    Returns data points with aggregated likes, comments, shares, saves, reach,
    and average engagement rate for each time bucket.
    """
    now = datetime.now(timezone.utc)
    period_map = {
        "week": (timedelta(days=7), 7),
        "month": (timedelta(days=30), 30),
        "quarter": (timedelta(days=90), 13),
        "year": (timedelta(days=365), 12),
    }
    delta, num_buckets = period_map.get(period, (timedelta(days=30), 30))
    start_date = now - delta

    result = await db.execute(
        select(Post).where(
            Post.user_id == user_id,
            Post.created_at >= start_date,
            (Post.perf_likes.isnot(None)) |
            (Post.perf_comments.isnot(None)) |
            (Post.perf_shares.isnot(None)) |
            (Post.perf_reach.isnot(None)),
        )
    )
    posts = result.scalars().all()

    data = []
    if period in ("week", "month"):
        # Day-level buckets
        for i in range(num_buckets):
            day = (start_date + timedelta(days=i)).date()
            day_posts = [p for p in posts if p.created_at.date() == day]
            likes = sum(p.perf_likes or 0 for p in day_posts)
            comments = sum(p.perf_comments or 0 for p in day_posts)
            shares = sum(p.perf_shares or 0 for p in day_posts)
            saves = sum(p.perf_saves or 0 for p in day_posts)
            reach = sum(p.perf_reach or 0 for p in day_posts)
            eng_rate = round(((likes + comments + shares) / reach) * 100, 2) if reach > 0 else 0
            data.append({
                "label": day.strftime("%d.%m."),
                "date": day.isoformat(),
                "post_count": len(day_posts),
                "likes": likes,
                "comments": comments,
                "shares": shares,
                "saves": saves,
                "reach": reach,
                "engagement_rate": eng_rate,
            })
    elif period == "quarter":
        # Week-level buckets
        for w in range(num_buckets):
            w_start = start_date + timedelta(weeks=w)
            w_end = w_start + timedelta(days=6)
            w_posts = [p for p in posts if w_start.date() <= p.created_at.date() <= w_end.date()]
            likes = sum(p.perf_likes or 0 for p in w_posts)
            comments = sum(p.perf_comments or 0 for p in w_posts)
            shares = sum(p.perf_shares or 0 for p in w_posts)
            saves = sum(p.perf_saves or 0 for p in w_posts)
            reach = sum(p.perf_reach or 0 for p in w_posts)
            eng_rate = round(((likes + comments + shares) / reach) * 100, 2) if reach > 0 else 0
            data.append({
                "label": f"KW {w_start.strftime('%d.%m.')}",
                "date": w_start.date().isoformat(),
                "post_count": len(w_posts),
                "likes": likes,
                "comments": comments,
                "shares": shares,
                "saves": saves,
                "reach": reach,
                "engagement_rate": eng_rate,
            })
    elif period == "year":
        # Month-level buckets
        for m_offset in range(num_buckets):
            m = (now.month - 11 + m_offset) % 12
            if m == 0:
                m = 12
            y = now.year if (now.month - 11 + m_offset) > 0 else now.year - 1
            m_posts = [p for p in posts if p.created_at.month == m and p.created_at.year == y]
            likes = sum(p.perf_likes or 0 for p in m_posts)
            comments = sum(p.perf_comments or 0 for p in m_posts)
            shares = sum(p.perf_shares or 0 for p in m_posts)
            saves = sum(p.perf_saves or 0 for p in m_posts)
            reach = sum(p.perf_reach or 0 for p in m_posts)
            eng_rate = round(((likes + comments + shares) / reach) * 100, 2) if reach > 0 else 0
            month_names = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
                           "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
            data.append({
                "label": month_names[m - 1],
                "date": f"{y}-{m:02d}-01",
                "post_count": len(m_posts),
                "likes": likes,
                "comments": comments,
                "shares": shares,
                "saves": saves,
                "reach": reach,
                "engagement_rate": eng_rate,
            })

    return {"period": period, "data": data}


@router.get("/performance-reminder")
async def get_performance_reminder(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get posts from last week that have no performance metrics entered yet.

    Returns posts that were posted 7-14 days ago with no metrics,
    as a reminder to enter social media performance data.
    """
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)

    result = await db.execute(
        select(Post).where(
            Post.user_id == user_id,
            Post.status == "posted",
            Post.posted_at >= two_weeks_ago,
            Post.posted_at <= week_ago,
            Post.perf_likes.is_(None),
            Post.perf_reach.is_(None),
        ).order_by(Post.posted_at.desc())
    )
    posts = result.scalars().all()

    return {
        "posts": [
            {
                "id": p.id,
                "title": p.title,
                "category": p.category,
                "platform": p.platform,
                "posted_at": p.posted_at.isoformat() if p.posted_at else None,
            }
            for p in posts
        ],
        "count": len(posts),
        "message": f"{len(posts)} Posts warten auf Metriken-Eingabe" if posts else "Alle Posts haben Metriken",
    }


@router.get("/performance-export")
async def export_performance_csv(
    period: Optional[str] = Query(default=None, pattern="^(week|month|quarter|year)$"),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Export post performance data as CSV file.

    Args:
        period: Optional time period filter (week, month, quarter, year)
    """
    now = datetime.now(timezone.utc)
    conditions = [Post.user_id == user_id]

    if period:
        period_map = {
            "week": timedelta(days=7),
            "month": timedelta(days=30),
            "quarter": timedelta(days=90),
            "year": timedelta(days=365),
        }
        start_date = now - period_map.get(period, timedelta(days=30))
        conditions.append(Post.created_at >= start_date)

    result = await db.execute(
        select(Post).where(*conditions).order_by(Post.created_at.desc())
    )
    posts = result.scalars().all()

    # Build CSV
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow([
        "ID", "Titel", "Kategorie", "Plattform", "Land", "Status",
        "Likes", "Kommentare", "Shares", "Saves", "Reichweite",
        "Engagement Rate (%)", "Erstellt", "Gepostet", "Metriken aktualisiert"
    ])

    for p in posts:
        likes = p.perf_likes or 0
        comments = p.perf_comments or 0
        shares = p.perf_shares or 0
        reach = p.perf_reach or 0
        eng_rate = round(((likes + comments + shares) / reach) * 100, 2) if reach > 0 else ""
        writer.writerow([
            p.id,
            p.title or "",
            p.category or "",
            p.platform or "",
            p.country or "",
            p.status or "",
            p.perf_likes if p.perf_likes is not None else "",
            p.perf_comments if p.perf_comments is not None else "",
            p.perf_shares if p.perf_shares is not None else "",
            p.perf_saves if p.perf_saves is not None else "",
            p.perf_reach if p.perf_reach is not None else "",
            eng_rate,
            p.created_at.strftime("%Y-%m-%d %H:%M") if p.created_at else "",
            p.posted_at.strftime("%Y-%m-%d %H:%M") if p.posted_at else "",
            p.perf_updated_at.strftime("%Y-%m-%d %H:%M") if p.perf_updated_at else "",
        ])

    output.seek(0)
    filename = f"treff_performance_{now.strftime('%Y%m%d')}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/heatmap")
async def get_heatmap(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get posting activity heatmap data for the last 12 months.

    Returns daily post counts in a format suitable for a GitHub-style
    contribution heatmap (52 weeks x 7 days grid).

    Response includes:
    - days: list of {date, count, titles} for each day with posts
    - streak: current and longest consecutive posting streak
    - total_posts: total posts in the 12-month window
    - total_days_with_posts: number of days that have at least one post
    """
    now = datetime.now(timezone.utc)
    # Go back ~12 months (52 weeks = 364 days)
    start_date = now - timedelta(days=364)
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

    # Query all posts in the date range
    result = await db.execute(
        select(Post.created_at, Post.title).where(
            Post.user_id == user_id,
            Post.created_at >= start_date,
        ).order_by(Post.created_at)
    )
    rows = result.all()

    # Build daily counts dict
    daily_counts = {}
    daily_titles = {}
    for created_at, title in rows:
        day_str = created_at.date().isoformat()
        daily_counts[day_str] = daily_counts.get(day_str, 0) + 1
        if day_str not in daily_titles:
            daily_titles[day_str] = []
        if title and len(daily_titles[day_str]) < 5:
            daily_titles[day_str].append(title)

    # Build complete day list for the grid
    days = []
    today = now.date()
    # Start from the Monday of the week 52 weeks ago
    grid_start = (today - timedelta(days=364))
    # Align to Monday
    grid_start = grid_start - timedelta(days=grid_start.weekday())

    for i in range(371):  # 53 weeks * 7 days (to cover full range)
        day = grid_start + timedelta(days=i)
        if day > today:
            break
        day_str = day.isoformat()
        count = daily_counts.get(day_str, 0)
        entry = {
            "date": day_str,
            "count": count,
            "weekday": day.weekday(),  # 0=Mon, 6=Sun
        }
        if count > 0 and day_str in daily_titles:
            entry["titles"] = daily_titles[day_str]
        days.append(entry)

    # Calculate streaks
    current_streak = 0
    longest_streak = 0
    temp_streak = 0

    # Walk backwards from today for current streak
    for i in range(365):
        check_day = (today - timedelta(days=i)).isoformat()
        if daily_counts.get(check_day, 0) > 0:
            current_streak += 1
        else:
            break

    # Walk forward from start for longest streak
    for i in range(365):
        check_day = (grid_start + timedelta(days=i)).isoformat()
        if daily_counts.get(check_day, 0) > 0:
            temp_streak += 1
            longest_streak = max(longest_streak, temp_streak)
        else:
            temp_streak = 0

    total_posts = sum(daily_counts.values())
    total_days_with_posts = len([d for d in daily_counts.values() if d > 0])

    return {
        "days": days,
        "streak": {
            "current": current_streak,
            "longest": longest_streak,
        },
        "total_posts": total_posts,
        "total_days_with_posts": total_days_with_posts,
        "grid_start": grid_start.isoformat(),
        "grid_end": today.isoformat(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/analytics/dashboard-widgets
# Aggregated data for Dashboard 6-Widget-Architektur
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/dashboard-widgets")
async def get_dashboard_widgets(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated data for dashboard widgets: content queue, student inbox,
    performance pulse, and active campaigns."""
    import json as _json
    from calendar import monthrange
    from sqlalchemy import and_

    now = datetime.now(timezone.utc)
    today = now.date()

    # ── 1. Content Queue: next 5 scheduled posts ──
    queue_query = (
        select(Post)
        .where(
            Post.user_id == user_id,
            Post.status == "scheduled",
            Post.scheduled_date.isnot(None),
            Post.scheduled_date >= today.isoformat(),
        )
        .order_by(Post.scheduled_date.asc(), Post.scheduled_time.asc())
        .limit(5)
    )
    queue_result = await db.execute(queue_query)
    queue_posts = queue_result.scalars().all()

    content_queue = []
    for p in queue_posts:
        thumbnail_url = None
        try:
            slides = _json.loads(p.slide_data) if p.slide_data else []
            if slides and isinstance(slides, list) and len(slides) > 0:
                first_slide = slides[0]
                thumbnail_url = first_slide.get("background_image") or first_slide.get("image_url") or first_slide.get("thumbnail")
        except (ValueError, TypeError, KeyError):
            pass

        content_queue.append({
            "id": p.id,
            "title": p.title or "Ohne Titel",
            "category": p.category,
            "platform": p.platform,
            "country": p.country,
            "status": p.status,
            "scheduled_date": p.scheduled_date if isinstance(p.scheduled_date, str) else (p.scheduled_date.isoformat() if p.scheduled_date else None),
            "scheduled_time": p.scheduled_time,
            "thumbnail_url": thumbnail_url,
        })

    # ── 2. Student Inbox: pending/analyzed items ──
    inbox_query = (
        select(PipelineItem)
        .where(
            PipelineItem.user_id == user_id,
            PipelineItem.status.in_(["pending", "analyzed"]),
        )
        .order_by(PipelineItem.created_at.desc())
        .limit(5)
    )
    inbox_result = await db.execute(inbox_query)
    inbox_items = inbox_result.scalars().all()

    student_inbox = []
    for item in inbox_items:
        student_name = None
        asset_thumbnail = None
        if item.student_id:
            s_result = await db.execute(
                select(Student.name, Student.country).where(Student.id == item.student_id)
            )
            s_row = s_result.first()
            if s_row:
                student_name = s_row[0]
                student_country = s_row[1]
            else:
                student_country = None
        else:
            student_country = None

        student_inbox.append({
            "id": item.id,
            "student_name": student_name or "Unbekannt",
            "student_country": student_country,
            "status": item.status,
            "suggested_post_type": item.suggested_post_type,
            "analysis_summary": item.analysis_summary,
            "detected_country": item.detected_country,
            "source_description": item.source_description,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        })

    # Total pending inbox count
    inbox_count_result = await db.execute(
        select(func.count(PipelineItem.id)).where(
            PipelineItem.user_id == user_id,
            PipelineItem.status.in_(["pending", "analyzed"]),
        )
    )
    inbox_total = inbox_count_result.scalar() or 0

    # ── 3. Performance Pulse: posting frequency last 4 weeks ──
    weeks_data = []
    for week_offset in range(3, -1, -1):  # 3 weeks ago -> this week
        week_start = now - timedelta(days=now.weekday() + (week_offset * 7))
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)

        count_result = await db.execute(
            select(func.count(Post.id)).where(
                Post.user_id == user_id,
                Post.created_at >= week_start,
                Post.created_at <= week_end,
            )
        )
        count = count_result.scalar() or 0

        week_label = f"KW {week_start.isocalendar()[1]}"
        weeks_data.append({
            "label": week_label,
            "count": count,
            "week_start": week_start.date().isoformat(),
        })

    # Get posting goal from settings
    goal_result = await db.execute(
        select(Setting).where(
            Setting.user_id == user_id,
            Setting.key == "posts_per_week",
        )
    )
    goal_setting = goal_result.scalar_one_or_none()
    posts_per_week_goal = int(goal_setting.value) if goal_setting and goal_setting.value else 3

    # Trend direction
    if len(weeks_data) >= 2:
        last_week = weeks_data[-1]["count"]
        prev_week = weeks_data[-2]["count"]
        if last_week > prev_week:
            trend = "up"
        elif last_week < prev_week:
            trend = "down"
        else:
            trend = "stable"
    else:
        trend = "stable"

    performance_pulse = {
        "weeks": weeks_data,
        "goal": posts_per_week_goal,
        "trend": trend,
        "current_week_count": weeks_data[-1]["count"] if weeks_data else 0,
    }

    # ── 4. Active Campaigns: with progress ──
    campaigns_query = (
        select(Campaign)
        .where(
            Campaign.user_id == user_id,
            Campaign.status.in_(["active", "draft"]),
        )
        .order_by(Campaign.updated_at.desc())
        .limit(5)
    )
    campaigns_result = await db.execute(campaigns_query)
    campaigns = campaigns_result.scalars().all()

    active_campaigns = []
    for c in campaigns:
        # Count total campaign posts and completed ones
        total_result = await db.execute(
            select(func.count(CampaignPost.id)).where(CampaignPost.campaign_id == c.id)
        )
        total_posts_count = total_result.scalar() or 0

        # Count posts that are already created (have post_id) and posted/exported
        completed_result = await db.execute(
            select(func.count(CampaignPost.id)).where(
                CampaignPost.campaign_id == c.id,
                CampaignPost.post_id.isnot(None),
            )
        )
        completed_posts = completed_result.scalar() or 0

        platforms = None
        if c.platforms:
            try:
                platforms = _json.loads(c.platforms)
            except (ValueError, TypeError):
                platforms = []

        active_campaigns.append({
            "id": c.id,
            "title": c.title,
            "description": c.description,
            "goal": c.goal,
            "status": c.status,
            "start_date": c.start_date,
            "end_date": c.end_date,
            "platforms": platforms,
            "total_posts": total_posts_count,
            "completed_posts": completed_posts,
        })

    return {
        "content_queue": content_queue,
        "student_inbox": {
            "items": student_inbox,
            "total": inbox_total,
        },
        "performance_pulse": performance_pulse,
        "active_campaigns": active_campaigns,
    }
