"""Seed default user for Vercel ephemeral DB."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User

logger = logging.getLogger(__name__)


async def seed_default_users(session: AsyncSession) -> int:
    """Seed a default user if none exists with the configured email.

    Returns the number of users created (0 or 1).
    """
    existing = await session.execute(
        select(User).where(User.email == settings.DEFAULT_USER_EMAIL)
    )
    if existing.scalar_one_or_none() is not None:
        logger.info("Default user already exists: %s", settings.DEFAULT_USER_EMAIL)
        return 0

    user = User(
        email=settings.DEFAULT_USER_EMAIL,
        password_hash=get_password_hash(settings.DEFAULT_USER_PASSWORD),
        display_name="TREFF Admin",
    )
    session.add(user)
    await session.commit()
    logger.info("Seeded default user: %s", settings.DEFAULT_USER_EMAIL)
    return 1
