import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from httpx import HTTPStatusError

from api_client import ApiClient
from channel_handler import router as channel_router
from config import settings
from messages import help_text, key_message, welcome_text
from support_handler import router as support_router
from user_store import upsert_user

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=settings.bot_token)
dp = Dispatcher()
api = ApiClient()
RELEASES_DIR = Path(__file__).resolve().parent.parent / "server" / "releases"


def _find_installer() -> Path | None:
    candidates = sorted(
        list(RELEASES_DIR.glob("FixInet*.exe")) + list(RELEASES_DIR.glob("InetFix-Setup*.exe")),
        key=lambda p: p.name,
        reverse=True,
    )
    return candidates[0] if candidates else None


async def send_installer_file(message: Message) -> None:
    installer = _find_installer()
    if not installer:
        return
    try:
        await message.answer_document(
            FSInputFile(installer),
            caption=f"📥 {settings.app_name} Setup",
        )
    except Exception:
        logger.exception("Failed to send installer")


def main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚡ Подключить", callback_data="connect")],
            [
                InlineKeyboardButton(text="📥 Скачать", url=settings.download_url),
                InlineKeyboardButton(text="❓ Помощь", callback_data="help"),
            ],
            [InlineKeyboardButton(text="💬 Поддержка", callback_data="support_start")],
        ]
    )


def key_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📥 Скачать приложение", url=settings.download_url)],
            [
                InlineKeyboardButton(text="🔄 Новый ключ", callback_data="new_key"),
                InlineKeyboardButton(text="❓ Помощь", callback_data="help"),
            ],
            [InlineKeyboardButton(text="💬 Поддержка", callback_data="support_start")],
        ]
    )


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await upsert_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
    )
    await message.answer(
        welcome_text(),
        parse_mode="HTML",
        reply_markup=main_keyboard(),
    )


@dp.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(help_text(), parse_mode="HTML", reply_markup=main_keyboard())


@dp.callback_query(F.data == "help")
async def cb_help(callback: CallbackQuery) -> None:
    await callback.message.answer(help_text(), parse_mode="HTML")
    await callback.answer()


@dp.callback_query(F.data.in_({"connect", "new_key"}))
async def cb_connect(callback: CallbackQuery) -> None:
    force_new = callback.data == "new_key"
    await callback.answer("Генерируем ключ..." if force_new else "Подключаем...")

    try:
        data = await api.issue_key(
            telegram_id=callback.from_user.id,
            telegram_username=callback.from_user.username,
            force_new=force_new,
        )
    except HTTPStatusError as exc:
        if exc.response.status_code == 429:
            await callback.message.answer(
                "⏳ Новый ключ можно получить раз в 24 часа.\n"
                "Используйте предыдущий ключ или напишите в поддержку.",
                reply_markup=main_keyboard(),
            )
            return
        logger.exception("API error")
        await callback.message.answer(
            "❌ Сервер временно недоступен. Попробуйте позже.",
            reply_markup=main_keyboard(),
        )
        return

    await callback.message.answer(
        key_message(data["key"], data["expires_at"]),
        parse_mode="HTML",
        reply_markup=key_keyboard(),
    )
    await send_installer_file(callback.message)


async def main() -> None:
    dp.include_router(support_router)
    dp.include_router(channel_router)
    logger.info("Starting %s bot (By %s)", settings.app_name, settings.app_author)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
