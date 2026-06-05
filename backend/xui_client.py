"""3x-ui panel API client for InetFix."""

from __future__ import annotations

import json
import logging
import random
import string
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

from config import settings

logger = logging.getLogger(__name__)


@dataclass
class VlessEndpoint:
    server: str
    port: int
    sni: str
    public_key: str
    short_id: str
    flow: str


class XuiClient:
    def __init__(self) -> None:
        self.base_url = settings.xui_panel_url.rstrip("/")
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                follow_redirects=True,
                timeout=20.0,
            )
            await self._login(self._client)
        return self._client

    async def _login(self, client: httpx.AsyncClient) -> None:
        if not settings.xui_username or not settings.xui_password:
            raise RuntimeError("XUI credentials not configured")
        resp = await client.post(
            "/login",
            data={
                "username": settings.xui_username,
                "password": settings.xui_password,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success"):
            raise RuntimeError(f"3x-ui login failed: {data.get('msg')}")

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def get_inbound(self, inbound_id: int | None = None) -> dict:
        inbound_id = inbound_id or settings.xui_inbound_id
        client = await self._get_client()
        resp = await client.get(f"/panel/api/inbounds/get/{inbound_id}")
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success"):
            raise RuntimeError(f"Failed to get inbound: {data.get('msg')}")
        return data["obj"]

    def parse_vless_endpoint(self, inbound: dict) -> VlessEndpoint:
        stream = json.loads(inbound.get("streamSettings") or "{}")
        reality = stream.get("realitySettings") or {}
        nested = reality.get("settings") or {}
        short_ids = reality.get("shortIds") or [""]
        server = settings.vless_server or self.base_url.split("//", 1)[-1].split("/")[0]

        return VlessEndpoint(
            server=server,
            port=int(inbound.get("port") or settings.vless_port),
            sni=(reality.get("serverNames") or [settings.vless_sni])[0],
            public_key=nested.get("publicKey") or settings.vless_public_key,
            short_id=short_ids[0] if short_ids else settings.vless_short_id,
            flow=settings.vless_flow,
        )

    async def load_vless_endpoint(self) -> VlessEndpoint:
        inbound = await self.get_inbound()
        return self.parse_vless_endpoint(inbound)

    @staticmethod
    def _random_sub_id(length: int = 16) -> str:
        alphabet = string.ascii_lowercase + string.digits
        return "".join(random.choices(alphabet, k=length))

    async def add_client(
        self,
        *,
        client_uuid: str,
        email: str,
        expiry_at: datetime,
        total_gb: int = 0,
        limit_ip: int = 2,
    ) -> None:
        client = await self._get_client()
        expiry_ms = int(expiry_at.replace(tzinfo=timezone.utc).timestamp() * 1000)
        total_bytes = total_gb * 1024 * 1024 * 1024 if total_gb > 0 else 0

        payload = {
            "id": settings.xui_inbound_id,
            "settings": json.dumps(
                {
                    "clients": [
                        {
                            "id": client_uuid,
                            "flow": settings.vless_flow,
                            "email": email,
                            "limitIp": limit_ip,
                            "totalGB": total_bytes,
                            "expiryTime": expiry_ms,
                            "enable": True,
                            "tgId": "",
                            "subId": self._random_sub_id(),
                            "comment": "InetFix",
                            "reset": 0,
                        }
                    ]
                }
            ),
        }

        resp = await client.post("/panel/api/inbounds/addClient", data=payload)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success"):
            raise RuntimeError(f"3x-ui addClient failed: {data.get('msg')}")

        logger.info("Created 3x-ui client %s (%s)", email, client_uuid)

    async def update_client_expiry(
        self,
        *,
        client_uuid: str,
        email: str,
        expiry_at: datetime,
    ) -> None:
        client = await self._get_client()
        expiry_ms = int(expiry_at.replace(tzinfo=timezone.utc).timestamp() * 1000)
        payload = {
            "id": settings.xui_inbound_id,
            "settings": json.dumps(
                {
                    "clients": [
                        {
                            "id": client_uuid,
                            "email": email,
                            "expiryTime": expiry_ms,
                            "enable": True,
                            "flow": settings.vless_flow,
                        }
                    ]
                }
            ),
        }
        resp = await client.post(
            f"/panel/api/inbounds/updateClient/{client_uuid}",
            data=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success"):
            raise RuntimeError(f"3x-ui updateClient failed: {data.get('msg')}")


xui = XuiClient()
