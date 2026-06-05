from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str
    api_base_url: str = "https://fixnet.sebog1.ru"
    api_secret: str = "change-me-api-secret"
    app_name: str = "Fixnet"
    app_author: str = "Seb0g1"
    download_url: str = "https://fixnet.sebog1.ru/api/v1/download"
    support_username: str = "Seb0g1"
    channel_username: str = "seb0g1site"
    forward_channel: str = "seb0g1site"
    forward_enabled: bool = True
    database_url: str = ""


_settings = BotSettings()
if not _settings.database_url:
    _db = Path(__file__).resolve().parent.parent / "backend" / "data" / "inetfix.db"
    _settings.database_url = f"sqlite+aiosqlite:///{_db.as_posix()}"
settings = _settings
