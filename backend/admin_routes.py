import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot_models import BotUser, Broadcast, ChannelForwardLog, SupportTicket
from config import settings
from database import ActivationKey, async_session, utcnow
from telegram_service import broadcast_to_users, send_message

router = APIRouter(prefix="/api/admin", tags=["admin"])

_active_tokens: dict[str, datetime] = {}


def _clean_tokens() -> None:
    now = datetime.now(timezone.utc)
    expired = [t for t, exp in _active_tokens.items() if exp < now]
    for t in expired:
        del _active_tokens[t]


def verify_admin(authorization: Annotated[str | None, Header()] = None) -> str:
    _clean_tokens()
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Unauthorized")
    token = authorization[7:]
    if token not in _active_tokens:
        raise HTTPException(401, "Invalid token")
    return token


async def get_session():
    async with async_session() as session:
        yield session


class LoginRequest(BaseModel):
    password: str


class BroadcastRequest(BaseModel):
    text: str
    parse_mode: str = "HTML"
    buttons: list[list[dict]] = Field(default_factory=list)


class ReplyRequest(BaseModel):
    reply: str
    parse_mode: str = "HTML"


@router.post("/login")
async def admin_login(body: LoginRequest):
    if body.password != settings.admin_password:
        raise HTTPException(401, "Wrong password")
    token = secrets.token_urlsafe(32)
    _active_tokens[token] = datetime.now(timezone.utc) + timedelta(hours=12)
    return {"token": token, "expires_in": 43200}


@router.get("/analytics", dependencies=[Depends(verify_admin)])
async def analytics(session: Annotated[AsyncSession, Depends(get_session)]):
    now = utcnow()
    week_ago = now - timedelta(days=7)

    total_users = await session.scalar(select(func.count()).select_from(BotUser))
    new_users = await session.scalar(
        select(func.count()).select_from(BotUser).where(BotUser.created_at >= week_ago)
    )
    total_keys = await session.scalar(select(func.count()).select_from(ActivationKey))
    active_keys = await session.scalar(
        select(func.count())
        .select_from(ActivationKey)
        .where(ActivationKey.is_active.is_(True), ActivationKey.expires_at > now)
    )
    open_tickets = await session.scalar(
        select(func.count())
        .select_from(SupportTicket)
        .where(SupportTicket.status == "open")
    )
    total_broadcasts = await session.scalar(select(func.count()).select_from(Broadcast))
    channel_forwards = await session.scalar(select(func.count()).select_from(ChannelForwardLog))

    return {
        "users": {"total": total_users or 0, "new_7d": new_users or 0},
        "keys": {"total": total_keys or 0, "active": active_keys or 0},
        "support": {"open": open_tickets or 0},
        "broadcasts": total_broadcasts or 0,
        "channel_forwards": channel_forwards or 0,
        "channel": settings.forward_channel,
    }


@router.get("/users", dependencies=[Depends(verify_admin)])
async def list_users(session: Annotated[AsyncSession, Depends(get_session)]):
    result = await session.execute(
        select(BotUser).order_by(BotUser.last_seen_at.desc()).limit(200)
    )
    users = result.scalars().all()
    return [
        {
            "telegram_id": u.telegram_id,
            "username": u.username,
            "first_name": u.first_name,
            "created_at": u.created_at.isoformat(),
            "last_seen_at": u.last_seen_at.isoformat(),
        }
        for u in users
    ]


@router.post("/broadcast", dependencies=[Depends(verify_admin)])
async def create_broadcast(
    body: BroadcastRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    result = await session.execute(
        select(BotUser.telegram_id).where(BotUser.is_blocked.is_(False))
    )
    user_ids = [row[0] for row in result.all()]
    if not user_ids:
        raise HTTPException(400, "No users to broadcast")

    sent, failed = await broadcast_to_users(
        user_ids,
        body.text,
        parse_mode=body.parse_mode,
        buttons=body.buttons or None,
    )

    record = Broadcast(
        text=body.text,
        parse_mode=body.parse_mode,
        buttons_json=json.dumps(body.buttons) if body.buttons else None,
        sent_count=sent,
        failed_count=failed,
        created_at=utcnow(),
    )
    session.add(record)
    await session.commit()

    return {"sent": sent, "failed": failed, "total": len(user_ids)}


@router.get("/broadcasts", dependencies=[Depends(verify_admin)])
async def list_broadcasts(session: Annotated[AsyncSession, Depends(get_session)]):
    result = await session.execute(
        select(Broadcast).order_by(Broadcast.created_at.desc()).limit(50)
    )
    return [
        {
            "id": b.id,
            "text": b.text[:200],
            "sent_count": b.sent_count,
            "failed_count": b.failed_count,
            "created_at": b.created_at.isoformat(),
        }
        for b in result.scalars().all()
    ]


@router.get("/support", dependencies=[Depends(verify_admin)])
async def list_tickets(
    session: Annotated[AsyncSession, Depends(get_session)],
    status: str = "open",
):
    result = await session.execute(
        select(SupportTicket)
        .where(SupportTicket.status == status)
        .order_by(SupportTicket.created_at.desc())
        .limit(100)
    )
    return [
        {
            "id": t.id,
            "telegram_id": t.telegram_id,
            "username": t.username,
            "message": t.message,
            "status": t.status,
            "admin_reply": t.admin_reply,
            "created_at": t.created_at.isoformat(),
            "replied_at": t.replied_at.isoformat() if t.replied_at else None,
        }
        for t in result.scalars().all()
    ]


@router.post("/support/{ticket_id}/reply", dependencies=[Depends(verify_admin)])
async def reply_ticket(
    ticket_id: int,
    body: ReplyRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    ticket = await session.get(SupportTicket, ticket_id)
    if not ticket:
        raise HTTPException(404, "Ticket not found")

    await send_message(ticket.telegram_id, body.reply, parse_mode=body.parse_mode)

    ticket.admin_reply = body.reply
    ticket.status = "answered"
    ticket.replied_at = utcnow()
    await session.commit()

    return {"ok": True}


@router.post("/support/{ticket_id}/close", dependencies=[Depends(verify_admin)])
async def close_ticket(ticket_id: int, session: Annotated[AsyncSession, Depends(get_session)]):
    ticket = await session.get(SupportTicket, ticket_id)
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    ticket.status = "closed"
    await session.commit()
    return {"ok": True}


@router.get("/channel/logs", dependencies=[Depends(verify_admin)])
async def channel_logs(session: Annotated[AsyncSession, Depends(get_session)]):
    result = await session.execute(
        select(ChannelForwardLog).order_by(ChannelForwardLog.created_at.desc()).limit(50)
    )
    return [
        {
            "id": l.id,
            "channel_message_id": l.channel_message_id,
            "forwarded_count": l.forwarded_count,
            "created_at": l.created_at.isoformat(),
        }
        for l in result.scalars().all()
    ]
