import httpx

from config import settings


class ApiClient:
    def __init__(self) -> None:
        self.base = settings.api_base_url.rstrip("/")
        self.headers = {"X-API-Key": settings.api_secret}

    async def issue_key(
        self,
        telegram_id: int,
        telegram_username: str | None = None,
        force_new: bool = False,
    ) -> dict:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{self.base}/api/v1/keys/issue",
                headers=self.headers,
                json={
                    "telegram_id": telegram_id,
                    "telegram_username": telegram_username,
                    "force_new": force_new,
                },
            )
            response.raise_for_status()
            return response.json()
