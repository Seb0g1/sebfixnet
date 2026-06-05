"""Sync activation key UUIDs into Xray server config."""

import json
from pathlib import Path

from sqlalchemy import select

from config import settings
from database import ActivationKey, async_session, utcnow


XRAY_CONFIG = Path(__file__).resolve().parent.parent / "server" / "xray" / "config.json"


async def sync_xray_clients() -> int:
    """Write all active VLESS UUIDs into xray config.json clients list."""
    if not XRAY_CONFIG.exists():
        return 0

    async with async_session() as session:
        result = await session.execute(
            select(ActivationKey).where(
                ActivationKey.is_active.is_(True),
                ActivationKey.expires_at > utcnow(),
            )
        )
        keys = result.scalars().all()

    clients = [{"id": k.vless_uuid, "flow": settings.vless_flow} for k in keys]

    with open(XRAY_CONFIG, encoding="utf-8") as f:
        config = json.load(f)

    for inbound in config.get("inbounds", []):
        if inbound.get("protocol") == "vless":
            inbound.setdefault("settings", {})["clients"] = clients

    with open(XRAY_CONFIG, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    return len(clients)
