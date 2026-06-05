from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_secret: str = "change-me-api-secret"
    database_url: str = ""  # auto-set below

    # 3x-ui panel (Netherlands)
    xui_panel_url: str = "https://bot.sebog1.ru/xbNquwImId"
    xui_username: str = ""
    xui_password: str = ""
    xui_inbound_id: int = 1
    xui_enabled: bool = True

    # VLESS / REALITY (auto-filled from 3x-ui inbound on startup)
    vless_server: str = "bot.sebog1.ru"
    vless_port: int = 8443
    vless_sni: str = "www.amazon.com"
    vless_public_key: str = ""
    vless_short_id: str = ""
    vless_flow: str = "xtls-rprx-vision"

    # Telegram bot
    bot_token: str = ""
    forward_channel: str = "seb0g1site"
    forward_enabled: bool = True

    # Admin panel
    admin_password: str = "change-me-admin"
    site_url: str = "https://fixnet.sebog1.ru"

    # App metadata
    app_name: str = "FixInet.ez"
    app_author: str = "Seb0g1"
    download_url: str = "https://fixnet.sebog1.ru/api/v1/download"
    support_username: str = "Seb0g1"
    channel_username: str = "seb0g1site"

    key_ttl_days: int = 30
    key_rate_limit_hours: int = 24

    services_path: Path = Path(__file__).resolve().parent.parent / "shared" / "services.json"
    releases_dir: Path = Path(__file__).resolve().parent.parent / "server" / "releases"


_settings = Settings()
if not _settings.database_url:
    _db = Path(__file__).resolve().parent / "data" / "inetfix.db"
    _settings.database_url = f"sqlite+aiosqlite:///{_db.as_posix()}"
settings = _settings
