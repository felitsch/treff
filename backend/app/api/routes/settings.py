"""Settings routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.setting import Setting

router = APIRouter()


@router.get("")
async def get_settings(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get all user settings."""
    result = await db.execute(
        select(Setting).where(Setting.user_id == user_id)
    )
    settings_list = result.scalars().all()
    return {s.key: s.value for s in settings_list}


@router.put("")
async def update_settings(
    settings_data: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update settings."""
    for key, value in settings_data.items():
        result = await db.execute(
            select(Setting).where(Setting.user_id == user_id, Setting.key == key)
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.value = str(value)
        else:
            setting = Setting(user_id=user_id, key=key, value=str(value))
            db.add(setting)

    await db.flush()
    await db.commit()

    # Return updated settings
    result = await db.execute(
        select(Setting).where(Setting.user_id == user_id)
    )
    settings_list = result.scalars().all()
    return {s.key: s.value for s in settings_list}
