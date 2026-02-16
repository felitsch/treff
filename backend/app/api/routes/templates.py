"""Template routes.

CRUD operations for HTML/CSS post templates. Supports system defaults,
user-created custom templates, categories, platform formats, and country theming.
"""

import json
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.core.sanitizer import sanitize_html, sanitize_css
from app.core.cache import api_cache, invalidate_cache
from app.models.template import Template


class TemplateCreate(BaseModel):
    """Schema for creating a custom template."""
    name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=100)
    platform_format: str = Field(..., min_length=1, max_length=50)
    slide_count: int = Field(default=1, ge=1)
    html_content: str = Field(default="<div class='template'>\n  <h1>{{title}}</h1>\n  <p>{{content}}</p>\n</div>")
    css_content: str = Field(default=".template { padding: 40px; }")
    default_colors: Optional[str] = None
    default_fonts: Optional[str] = None
    placeholder_fields: str = Field(default='["title", "content"]')
    is_country_themed: bool = False
    country: Optional[str] = None

router = APIRouter()


def template_to_dict(t: Template) -> dict:
    """Convert a Template model to a plain dict to avoid lazy-loading issues."""
    return {
        "id": t.id,
        "name": t.name,
        "category": t.category,
        "platform_format": t.platform_format,
        "slide_count": t.slide_count,
        "html_content": t.html_content,
        "css_content": t.css_content,
        "default_colors": t.default_colors,
        "default_fonts": t.default_fonts,
        "placeholder_fields": t.placeholder_fields,
        "thumbnail_url": t.thumbnail_url,
        "is_default": t.is_default,
        "is_country_themed": t.is_country_themed,
        "country": t.country,
        "version": t.version,
        "parent_template_id": t.parent_template_id,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


@router.get("")
async def list_templates(
    request: Request,
    category: Optional[str] = None,
    platform_format: Optional[str] = None,
    country: Optional[str] = None,
    search: Optional[str] = None,
    ownership: Optional[str] = None,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List all templates with optional filters.

    ownership: 'system' for default templates, 'custom' for user-created, None for all.
    Responses are cached for 1 hour with automatic invalidation on template changes.
    """
    # Build cache key from query params
    cache_params = {
        "category": category,
        "platform_format": platform_format,
        "country": country,
        "search": search,
        "ownership": ownership,
    }
    cache_key = api_cache._build_key("templates", cache_params)

    # Check cache
    entry = api_cache.get(cache_key)
    if entry is not None:
        # Check If-None-Match for 304
        if_none_match = request.headers.get("if-none-match")
        if if_none_match and if_none_match.strip('"') == entry.etag:
            return JSONResponse(
                status_code=304,
                content=None,
                headers={
                    "ETag": f'"{entry.etag}"',
                    "Cache-Control": f"private, max-age={entry.remaining_ttl}",
                    "X-Cache": "HIT",
                },
            )
        return JSONResponse(
            content=entry.value,
            headers={
                "ETag": f'"{entry.etag}"',
                "Cache-Control": f"private, max-age={entry.remaining_ttl}",
                "X-Cache": "HIT",
                "X-Cache-Age": str(entry.age_seconds),
            },
        )

    # Cache miss - query database
    query = select(Template)

    if category:
        query = query.where(Template.category == category)
    if platform_format:
        query = query.where(Template.platform_format == platform_format)
    if country:
        query = query.where(Template.country == country)
    if search:
        query = query.where(Template.name.ilike(f"%{search}%"))
    if ownership == "system":
        query = query.where(Template.is_default == True)
    elif ownership == "custom":
        query = query.where(Template.is_default == False)

    query = query.order_by(Template.category, Template.name)
    result = await db.execute(query)
    templates = result.scalars().all()
    data = [template_to_dict(t) for t in templates]

    # Store in cache
    new_entry = api_cache.set(cache_key, data)
    return JSONResponse(
        content=data,
        headers={
            "ETag": f'"{new_entry.etag}"',
            "Cache-Control": "private, max-age=3600",
            "X-Cache": "MISS",
        },
    )


@router.get("/{template_id}")
async def get_template(
    template_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a single template."""
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template_to_dict(template)


@router.post("", status_code=201)
async def create_template(
    template_data: TemplateCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a custom template."""
    # Sanitize HTML and CSS to prevent XSS
    safe_html = sanitize_html(template_data.html_content)
    safe_css = sanitize_css(template_data.css_content)

    template = Template(
        name=template_data.name,
        category=template_data.category,
        platform_format=template_data.platform_format,
        slide_count=template_data.slide_count,
        html_content=safe_html,
        css_content=safe_css,
        default_colors=template_data.default_colors or json.dumps({
            "primary": "#3B7AB1",
            "secondary": "#FDD000",
            "accent": "#FFFFFF",
            "background": "#1A1A2E"
        }),
        default_fonts=template_data.default_fonts or json.dumps({
            "heading_font": "Montserrat",
            "body_font": "Inter"
        }),
        placeholder_fields=template_data.placeholder_fields,
        is_default=False,  # User-created templates are never default
        is_country_themed=template_data.is_country_themed,
        country=template_data.country,
        version=1,
    )
    db.add(template)
    await db.flush()
    await db.refresh(template)
    result = template_to_dict(template)
    await db.commit()
    invalidate_cache("templates")
    return result


@router.put("/{template_id}")
async def update_template(
    template_id: int,
    template_data: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update a custom template."""
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if template.is_default:
        raise HTTPException(status_code=403, detail="Cannot modify default templates")

    for key, value in template_data.items():
        if hasattr(template, key) and key not in ("id", "is_default", "created_at"):
            # Sanitize HTML and CSS content to prevent XSS
            if key == "html_content" and isinstance(value, str):
                value = sanitize_html(value)
            elif key == "css_content" and isinstance(value, str):
                value = sanitize_css(value)
            setattr(template, key, value)

    await db.flush()
    await db.refresh(template)
    result = template_to_dict(template)
    await db.commit()
    invalidate_cache("templates")
    return result


@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a custom template."""
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if template.is_default:
        raise HTTPException(status_code=403, detail="Cannot delete default templates")

    await db.delete(template)
    await db.commit()
    invalidate_cache("templates")
    return {"message": "Template deleted"}


@router.post("/{template_id}/duplicate", status_code=201)
async def duplicate_template(
    template_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Duplicate a template (system or custom) as a new custom template.

    The duplicate is fully editable regardless of whether the source was
    a system template. The name gets ' (Kopie)' appended, and
    parent_template_id tracks the source.
    """
    result = await db.execute(select(Template).where(Template.id == template_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Template not found")

    duplicate = Template(
        name=f"{source.name} (Kopie)",
        category=source.category,
        platform_format=source.platform_format,
        slide_count=source.slide_count,
        html_content=source.html_content,
        css_content=source.css_content,
        default_colors=source.default_colors,
        default_fonts=source.default_fonts,
        placeholder_fields=source.placeholder_fields,
        thumbnail_url=source.thumbnail_url,
        is_default=False,  # Duplicates are always custom / editable
        is_country_themed=source.is_country_themed,
        country=source.country,
        version=1,
        parent_template_id=source.id,
    )
    db.add(duplicate)
    await db.flush()
    await db.refresh(duplicate)
    result_dict = template_to_dict(duplicate)
    await db.commit()
    invalidate_cache("templates")
    return result_dict


@router.get("/{template_id}/preview")
async def preview_template(
    template_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get template preview thumbnail."""
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"thumbnail_url": template.thumbnail_url, "template_id": template.id}
