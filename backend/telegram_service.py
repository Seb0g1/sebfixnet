"""Telegram Bot API helpers for admin panel."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from config import settings

logger = logging.getLogger(__name__)

API = "https://api.telegram.org/bot{token}"


def _api_url(method: str) -> str:
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN not configured")
    return f"{API.format(token=settings.bot_token)}/{method}"


async def send_message(
    chat_id: int,
    text: str,
    *,
    parse_mode: str = "HTML",
    reply_markup: dict | None = None,
    disable_web_page_preview: bool = False,
) -> dict:
    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": disable_web_page_preview,
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(_api_url("sendMessage"), json=payload)
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(data.get("description", "sendMessage failed"))
        return data["result"]


async def forward_message(chat_id: int, from_chat_id: int | str, message_id: int) -> dict:
    payload = {
        "chat_id": chat_id,
        "from_chat_id": from_chat_id,
        "message_id": message_id,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(_api_url("forwardMessage"), json=payload)
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(data.get("description", "forwardMessage failed"))
        return data["result"]


async def copy_message(chat_id: int, from_chat_id: int | str, message_id: int) -> dict:
    payload = {
        "chat_id": chat_id,
        "from_chat_id": from_chat_id,
        "message_id": message_id,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(_api_url("copyMessage"), json=payload)
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(data.get("description", "copyMessage failed"))
        return data["result"]


def build_inline_keyboard(buttons: list[list[dict]]) -> dict:
    """buttons: [[{text, url?}, {text, callback_data?}], ...]"""
    rows = []
    for row in buttons:
        kb_row = []
        for btn in row:
            item: dict[str, str] = {"text": btn["text"]}
            if btn.get("url"):
                item["url"] = btn["url"]
            elif btn.get("callback_data"):
                item["callback_data"] = btn["callback_data"]
            kb_row.append(item)
        rows.append(kb_row)
    return {"inline_keyboard": rows}


async def broadcast_to_users(
    user_ids: list[int],
    text: str,
    *,
    parse_mode: str = "HTML",
    buttons: list[list[dict]] | None = None,
) -> tuple[int, int]:
    markup = build_inline_keyboard(buttons) if buttons else None
    sent = failed = 0
    for uid in user_ids:
        try:
            await send_message(uid, text, parse_mode=parse_mode, reply_markup=markup)
            sent += 1
        except Exception as exc:
            failed += 1
            logger.warning("Broadcast failed for %s: %s", uid, exc)
    return sent, failed
