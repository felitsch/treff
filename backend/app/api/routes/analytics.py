"""Analytics routes."""

from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.post import Post
from app.models.asset import Asset
from app.models.calendar_entry import CalendarEntry
from app.models.content_suggestion import ContentSuggestion
from app.models.setting import Setting

router = APIRouter()


@router.get("/overview")
async def get_overview(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get analytics overview: total posts, this week, this month."""
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

    return {
        "total_posts": total,
        "posts_this_week": posts_this_week,
        "posts_this_month": posts_this_month,
    }


@router.get("/dashboard")
async def get_dashboard_data(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get all dashboard data in a single API call."""
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

    return {
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
