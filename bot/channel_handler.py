import logging
from datetime import datetime, timezone

from aiogram import Bot, Router
from aiogram.types import Message
from sqlalchemy import select

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from bot_models import BotUser, ChannelForwardLog
from config import settings
from user_store import async_session, engine, get_all_user_ids
from database import Base

logger = logging.getLogger(__name__)
router = Router()


async def _ensure_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@router.channel_post()
async def forward_channel_post(message: Message, bot: Bot):
    if not settings.forward_enabled:
        return

    channel = settings.forward_channel.lstrip("@")
    if message.chat.username and message.chat.username.lower() != channel.lower():
        return

    await _ensure_tables()
    user_ids = await get_all_user_ids()
    if not user_ids:
        return

    sent = 0
    for uid in user_ids:
        try:
            await bot.copy_message(
                chat_id=uid,
                from_chat_id=message.chat.id,
                message_id=message.message_id,
            )
            sent += 1
        except Exception as exc:
            logger.debug("Forward to %s failed: %s", uid, exc)

    async with async_session() as session:
        session.add(ChannelForwardLog(
            channel_message_id=message.message_id,
            forwarded_count=sent,
            created_at=datetime.now(timezone.utc),
        ))
        await session.commit()

    logger.info("Channel post %s forwarded to %s users", message.message_id, sent)
