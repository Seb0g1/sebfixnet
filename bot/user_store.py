"""Track bot users in shared database."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from bot_models import BotUser  # noqa: E402
from config import settings as backend_settings  # noqa: E402

engine = create_async_engine(backend_settings.database_url, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


def utcnow():
    return datetime.now(timezone.utc)


async def upsert_user(telegram_id: int, username: str | None, first_name: str | None) -> None:
    from database import Base  # noqa: E402

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        result = await session.execute(
            select(BotUser).where(BotUser.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        now = utcnow()
        if user:
            user.username = username
            user.first_name = first_name
            user.last_seen_at = now
        else:
            session.add(BotUser(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                created_at=now,
                last_seen_at=now,
            ))
        await session.commit()


async def get_all_user_ids() -> list[int]:
    async with async_session() as session:
        result = await session.execute(
            select(BotUser.telegram_id).where(BotUser.is_blocked.is_(False))
        )
        return [row[0] for row in result.all()]
