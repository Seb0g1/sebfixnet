import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import (
    async_session,
    format_key,
    get_key_by_value,
    init_db,
    issue_key,
    normalize_key,
    utcnow,
)
from admin_routes import router as admin_router
from singbox_config import build_singbox_config, load_services
from xui_client import xui
from xui_provision import provision_key_in_xui, refresh_existing_key_in_xui

ROOT = Path(__file__).resolve().parent.parent


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    if settings.xui_enabled and settings.xui_username:
        try:
            endpoint = await xui.load_vless_endpoint()
            settings.vless_server = endpoint.server
            settings.vless_port = endpoint.port
            settings.vless_sni = endpoint.sni
            settings.vless_public_key = endpoint.public_key
            settings.vless_short_id = endpoint.short_id
            settings.vless_flow = endpoint.flow
        except Exception:
            pass
    yield
    await xui.close()


app = FastAPI(
    title="Fixnet API",
    description="Backend for Fixnet (By Seb0g1)",
    version="1.1.0",
    lifespan=lifespan,
)

app.include_router(admin_router)

if (ROOT / "website").exists():
    app.mount("/site", StaticFiles(directory=ROOT / "website"), name="site")
if (ROOT / "admin").exists():
    app.mount("/admin", StaticFiles(directory=ROOT / "admin"), name="admin")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_session():
    async with async_session() as session:
        yield session


def verify_api_key(x_api_key: Annotated[str | None, Header()] = None) -> None:
    if x_api_key != settings.api_secret:
        raise HTTPException(status_code=401, detail="Invalid API key")


class IssueKeyRequest(BaseModel):
    telegram_id: int
    telegram_username: str | None = None
    force_new: bool = False


class IssueKeyResponse(BaseModel):
    key: str
    expires_at: str
    download_url: str
    vless_uuid: str


class ValidateKeyRequest(BaseModel):
    key: str


class ValidateKeyResponse(BaseModel):
    valid: bool
    key: str
    plan: str = "FREE"
    expires_at: str
    author: str


class ConfigRequest(BaseModel):
    mode: str = Field(default="combined", pattern="^(combined|full)$")
    services: list[str] = Field(default_factory=lambda: ["telegram", "discord", "youtube"])


@app.get("/")
async def landing_page():
    index = ROOT / "website" / "index.html"
    if index.exists():
        return HTMLResponse(index.read_text(encoding="utf-8"))
    return {"app": settings.app_name, "site": settings.site_url}


@app.get("/admin")
async def admin_page():
    return RedirectResponse("/admin/index.html")


@app.get("/api/v1/health")
async def health():
    return {"status": "ok", "app": settings.app_name, "author": settings.app_author}


@app.get("/api/v1/services")
async def list_services():
    return load_services()


@app.post("/api/v1/keys/issue", response_model=IssueKeyResponse, dependencies=[Depends(verify_api_key)])
async def api_issue_key(
    body: IssueKeyRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    try:
        record = await issue_key(
            session,
            telegram_id=body.telegram_id,
            telegram_username=body.telegram_username,
            force_new=body.force_new,
        )
    except ValueError as exc:
        if str(exc) == "RATE_LIMIT":
            raise HTTPException(
                status_code=429,
                detail=f"New key available once per {settings.key_rate_limit_hours} hours",
            ) from exc
        raise

    try:
        if body.force_new or not record.xui_email:
            email = await provision_key_in_xui(record)
        else:
            email = await refresh_existing_key_in_xui(record)
        record.xui_email = email
        await session.commit()
        await session.refresh(record)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to provision client in 3x-ui: {exc}",
        ) from exc

    return IssueKeyResponse(
        key=format_key(record.key_value),
        expires_at=record.expires_at.isoformat(),
        download_url=settings.download_url,
        vless_uuid=record.vless_uuid,
    )


@app.post("/api/v1/keys/validate", response_model=ValidateKeyResponse)
async def api_validate_key(
    body: ValidateKeyRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    record = await get_key_by_value(session, body.key)
    if not record or not record.is_active or record.expires_at <= utcnow():
        raise HTTPException(status_code=404, detail="Invalid or expired key")

    return ValidateKeyResponse(
        valid=True,
        key=format_key(record.key_value),
        expires_at=record.expires_at.isoformat(),
        author=settings.app_author,
    )


@app.get("/api/v1/config/{key}")
async def api_get_config(
    key: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    mode: str = Query(default="combined"),
    services: str = Query(default="telegram,discord,youtube"),
):
    record = await get_key_by_value(session, key)
    if not record or not record.is_active or record.expires_at <= utcnow():
        raise HTTPException(status_code=404, detail="Invalid or expired key")

    service_list = [s.strip() for s in services.split(",") if s.strip()]
    config = build_singbox_config(
        vless_uuid=record.vless_uuid,
        mode=mode,
        selected_services=service_list,
    )

    return JSONResponse(
        content={
            "key": format_key(record.key_value),
            "mode": mode,
            "services": service_list,
            "vless": {
                "server": settings.vless_server,
                "port": settings.vless_port,
                "uuid": record.vless_uuid,
                "sni": settings.vless_sni,
                "public_key": settings.vless_public_key,
                "short_id": settings.vless_short_id,
                "flow": settings.vless_flow,
            },
            "singbox": config,
        }
    )


@app.post("/api/v1/config")
async def api_post_config(
    body: ConfigRequest,
    key: str = Query(...),
    session: Annotated[AsyncSession, Depends(get_session)] = ...,
):
    record = await get_key_by_value(session, key)
    if not record or not record.is_active or record.expires_at <= utcnow():
        raise HTTPException(status_code=404, detail="Invalid or expired key")

    config = build_singbox_config(
        vless_uuid=record.vless_uuid,
        mode=body.mode,
        selected_services=body.services,
    )
    return {"singbox": config}


@app.get("/api/v1/download")
async def api_download():
    releases = settings.releases_dir
    if not releases.exists():
        releases = Path("/app/releases")
    if releases.exists():
        installers = sorted(releases.glob("InetFix-Setup*.exe"), reverse=True)
        if installers:
            return FileResponse(
                installers[0],
                media_type="application/octet-stream",
                filename=installers[0].name,
            )
        zips = sorted(releases.glob("InetFix-Portable*.zip"), reverse=True)
        if zips:
            return FileResponse(
                zips[0],
                media_type="application/zip",
                filename="InetFix-Setup-1.0.0.zip",
            )
    raise HTTPException(
        status_code=404,
        detail="Installer not found. Run app/scripts/package-portable.ps1",
    )


@app.get("/api/v1/stats", dependencies=[Depends(verify_api_key)])
async def api_stats(session: Annotated[AsyncSession, Depends(get_session)]):
    from sqlalchemy import func, select
    from database import ActivationKey

    total = await session.scalar(select(func.count()).select_from(ActivationKey))
    active = await session.scalar(
        select(func.count())
        .select_from(ActivationKey)
        .where(ActivationKey.is_active.is_(True), ActivationKey.expires_at > utcnow())
    )
    return {"total_keys": total or 0, "active_keys": active or 0}
