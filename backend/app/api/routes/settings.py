"""Settings routes.

Application settings (brand colors, API keys, posting goals) per user.
"""

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
    # Single SELECT for all existing settings (avoids N+1 per-key queries)
    result = await db.execute(
        select(Setting).where(Setting.user_id == user_id)
    )
    existing_map = {s.key: s for s in result.scalars().all()}

    for key, value in settings_data.items():
        if key in existing_map:
            existing_map[key].value = str(value)
        else:
            new_setting = Setting(user_id=user_id, key=key, value=str(value))
            db.add(new_setting)
            existing_map[key] = new_setting

    await db.commit()

    return {k: s.value for k, s in existing_map.items()}
