"""Configuration management for finlite."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or `.env`."""

    data_dir: Path = Field(
        default_factory=lambda: Path("./var/data"), validation_alias="FINLITE_DATA_DIR"
    )
    locale: str = Field(default="pt_BR", validation_alias="FINLITE_LOCALE")
    default_currency: str = Field(default="BRL", validation_alias="FINLITE_DEFAULT_CURRENCY")

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_prefix="FINLITE_",
        case_sensitive=False,
    )

    @property
    def database_path(self) -> Path:
        return self.data_dir / "finlite.db"

    @property
    def database_url(self) -> str:
        # Using absolute path ensures consistent behavior for SQLite URLs.
        return f"sqlite:///{self.database_path.resolve()}"


@lru_cache(1)
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings
