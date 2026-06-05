"""Provision InetFix keys in 3x-ui panel."""

import logging

from config import settings
from database import ActivationKey, utcnow
from xui_client import xui

logger = logging.getLogger(__name__)


def xui_email_for(record: ActivationKey) -> str:
    if record.xui_email:
        return record.xui_email
    suffix = record.key_value[:8]
    tg = record.telegram_id or 0
    return f"inetfix-{tg}-{suffix}"


async def provision_key_in_xui(record: ActivationKey) -> str:
    if not settings.xui_enabled:
        return xui_email_for(record)

    email = xui_email_for(record)
    try:
        await xui.add_client(
            client_uuid=record.vless_uuid,
            email=email,
            expiry_at=record.expires_at,
        )
    except Exception as exc:
        logger.warning("addClient failed for %s, trying update: %s", email, exc)
        await xui.update_client_expiry(
            client_uuid=record.vless_uuid,
            email=email,
            expiry_at=record.expires_at,
        )

    return email


async def refresh_existing_key_in_xui(record: ActivationKey) -> str:
    if not settings.xui_enabled:
        return xui_email_for(record)

    email = xui_email_for(record)
    try:
        await xui.update_client_expiry(
            client_uuid=record.vless_uuid,
            email=email,
            expiry_at=record.expires_at,
        )
    except Exception as exc:
        logger.warning("updateClient failed for %s, creating new: %s", email, exc)
        await xui.add_client(
            client_uuid=record.vless_uuid,
            email=email,
            expiry_at=record.expires_at,
        )
    return email
