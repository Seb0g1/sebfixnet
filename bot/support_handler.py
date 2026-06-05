from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from bot_models import SupportTicket
from user_store import async_session, engine
from database import Base

router = Router()

_support_mode: set[int] = set()


async def _ensure_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@router.callback_query(F.data == "support_start")
async def support_start(callback: CallbackQuery):
    _support_mode.add(callback.from_user.id)
    await callback.message.answer(
        "💬 <b>Поддержка Fixnet</b>\n\n"
        "Опишите вашу проблему одним сообщением — мы ответим как можно скорее.",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(F.text & ~F.text.startswith("/"))
async def support_message(message: Message):
    if message.from_user.id not in _support_mode:
        return

    await _ensure_tables()
    async with async_session() as session:
        ticket = SupportTicket(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            message=message.text or "",
            status="open",
            created_at=datetime.now(timezone.utc),
        )
        session.add(ticket)
        await session.commit()

    _support_mode.discard(message.from_user.id)
    await message.answer(
        "✅ Ваш вопрос отправлен в поддержку!\n"
        "Ответ придёт в этот чат. Обычно отвечаем в течение нескольких часов.",
        parse_mode="HTML",
    )
