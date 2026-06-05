import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import Boolean, DateTime, Integer, String, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from config import settings


def _database_url() -> str:
    url = getattr(settings, "database_url", "") or ""
    if url:
        return url
    db = Path(__file__).resolve().parent / "data" / "inetfix.db"
    return f"sqlite+aiosqlite:///{db.as_posix()}"


class Base(DeclarativeBase):
    pass


class ActivationKey(Base):
    __tablename__ = "activation_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key_value: Mapped[str] = mapped_column(String(19), unique=True, index=True)
    vless_uuid: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    telegram_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    telegram_username: Mapped[str | None] = mapped_column(String(128), nullable=True)
    xui_email: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


engine = create_async_engine(_database_url(), echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    from config import settings
    import bot_models  # noqa: F401 — register bot tables

    db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
    if db_path and db_path != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _ensure_column(conn, "activation_keys", "xui_email", "VARCHAR(128)")


async def _ensure_column(conn, table: str, column: str, col_type: str) -> None:
    from sqlalchemy import text

    def _migrate(sync_conn):
        rows = sync_conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
        names = {row[1] for row in rows}
        if column not in names:
            sync_conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))

    await conn.run_sync(_migrate)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def generate_key_value() -> str:
    import random
    digits = "".join(str(random.randint(0, 9)) for _ in range(16))
    return f"{digits[0:4]} {digits[4:8]} {digits[8:12]} {digits[12:16]}"


def normalize_key(key: str) -> str:
    return key.replace(" ", "").strip()


def format_key(key: str) -> str:
    raw = normalize_key(key)
    if len(raw) != 16:
        return key
    return f"{raw[0:4]} {raw[4:8]} {raw[8:12]} {raw[12:16]}"


async def get_key_by_value(session: AsyncSession, key_value: str) -> ActivationKey | None:
    normalized = normalize_key(key_value)
    result = await session.execute(
        select(ActivationKey).where(ActivationKey.key_value == normalized)
    )
    return result.scalar_one_or_none()


async def get_active_key_for_telegram(session: AsyncSession, telegram_id: int) -> ActivationKey | None:
    now = utcnow()
    result = await session.execute(
        select(ActivationKey)
        .where(
            ActivationKey.telegram_id == telegram_id,
            ActivationKey.is_active.is_(True),
            ActivationKey.expires_at > now,
        )
        .order_by(ActivationKey.created_at.desc())
    )
    return result.scalar_one_or_none()


async def can_issue_new_key(session: AsyncSession, telegram_id: int) -> bool:
    result = await session.execute(
        select(ActivationKey)
        .where(ActivationKey.telegram_id == telegram_id)
        .order_by(ActivationKey.last_issued_at.desc())
        .limit(1)
    )
    last = result.scalar_one_or_none()
    if not last or not last.last_issued_at:
        return True
    delta = utcnow() - last.last_issued_at
    return delta >= timedelta(hours=settings.key_rate_limit_hours)


async def issue_key(
    session: AsyncSession,
    telegram_id: int,
    telegram_username: str | None = None,
    force_new: bool = False,
) -> ActivationKey:
    if not force_new:
        existing = await get_active_key_for_telegram(session, telegram_id)
        if existing:
            existing.last_issued_at = utcnow()
            existing.expires_at = utcnow() + timedelta(days=settings.key_ttl_days)
            await session.commit()
            await session.refresh(existing)
            return existing

    if force_new:
        result = await session.execute(
            select(ActivationKey).where(
                ActivationKey.telegram_id == telegram_id,
                ActivationKey.is_active.is_(True),
            )
        )
        for old in result.scalars().all():
            old.is_active = False

        if not await can_issue_new_key(session, telegram_id):
            raise ValueError("RATE_LIMIT")

    now = utcnow()
    key = ActivationKey(
        key_value=normalize_key(generate_key_value()),
        vless_uuid=str(uuid.uuid4()),
        telegram_id=telegram_id,
        telegram_username=telegram_username,
        is_active=True,
        created_at=now,
        expires_at=now + timedelta(days=settings.key_ttl_days),
        last_issued_at=now,
    )
    session.add(key)
    await session.commit()
    await session.refresh(key)
    return key
