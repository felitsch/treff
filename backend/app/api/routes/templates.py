"""Template routes."""

import json
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_id
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
    category: Optional[str] = None,
    platform_format: Optional[str] = None,
    country: Optional[str] = None,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List all templates with optional filters."""
    query = select(Template)

    if category:
        query = query.where(Template.category == category)
    if platform_format:
        query = query.where(Template.platform_format == platform_format)
    if country:
        query = query.where(Template.country == country)

    query = query.order_by(Template.category, Template.name)
    result = await db.execute(query)
    templates = result.scalars().all()
    return [template_to_dict(t) for t in templates]


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
    template = Template(
        name=template_data.name,
        category=template_data.category,
        platform_format=template_data.platform_format,
        slide_count=template_data.slide_count,
        html_content=template_data.html_content,
        css_content=template_data.css_content,
        default_colors=template_data.default_colors or json.dumps({
            "primary": "#4C8BC2",
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
            setattr(template, key, value)

    await db.flush()
    await db.refresh(template)
    result = template_to_dict(template)
    await db.commit()
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
    return {"message": "Template deleted"}


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
