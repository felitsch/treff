"""Template Favorites routes — toggle and list favorite templates per user."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.template_favorite import TemplateFavorite
from app.models.template import Template

router = APIRouter()


@router.get("")
async def list_favorites(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Return list of template IDs the current user has favorited."""
    result = await db.execute(
        select(TemplateFavorite.template_id).where(
            TemplateFavorite.user_id == user_id
        )
    )
    ids = [row[0] for row in result.all()]
    return {"favorite_template_ids": ids}


@router.post("/{template_id}")
async def toggle_favorite(
    template_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Toggle favorite status for a template. Returns new favorite state."""
    # Verify template exists
    tmpl = await db.execute(select(Template.id).where(Template.id == template_id))
    if not tmpl.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Template not found")

    # Check if already favorited
    result = await db.execute(
        select(TemplateFavorite).where(
            TemplateFavorite.user_id == user_id,
            TemplateFavorite.template_id == template_id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Un-favorite
        await db.delete(existing)
        await db.commit()
        return {"template_id": template_id, "is_favorite": False}
    else:
        # Favorite
        fav = TemplateFavorite(user_id=user_id, template_id=template_id)
        db.add(fav)
        await db.commit()
        return {"template_id": template_id, "is_favorite": True}
