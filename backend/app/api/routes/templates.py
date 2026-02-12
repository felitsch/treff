"""Template routes."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.template import Template

router = APIRouter()


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

    result = await db.execute(query)
    return result.scalars().all()


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
    return template


@router.post("", status_code=201)
async def create_template(
    template_data: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a custom template."""
    template = Template(**template_data)
    db.add(template)
    await db.flush()
    await db.refresh(template)
    return template


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
        if hasattr(template, key):
            setattr(template, key, value)

    await db.flush()
    await db.refresh(template)
    return template


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
