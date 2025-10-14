"""
Application configuration module.

Manages configuration via environment variables and defaults.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Environment variables can be set in .env file or system environment.

    Examples:
        >>> settings = get_settings()
        >>> print(settings.database_path)
        PosixPath('/Users/user/.finlite/finlite.db')
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database configuration
    finlite_data_dir: Path = Field(
        default_factory=lambda: Path.home() / ".finlite",
        description="Directory for application data",
    )
    database_filename: str = Field(
        default="finlite.db",
        description="SQLite database filename",
    )

    # Application settings
    default_currency: str = Field(
        default="USD",
        description="Default currency (ISO 4217 code)",
    )
    locale: str = Field(
        default="en_US",
        description="Locale for formatting",
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )

    @property
    def database_path(self) -> Path:
        """Full path to SQLite database file."""
        return self.finlite_data_dir / self.database_filename

    @property
    def database_url(self) -> str:
        """SQLAlchemy database URL."""
        return f"sqlite:///{self.database_path}"

    @property
    def data_dir(self) -> Path:
        """Data directory path (alias for finlite_data_dir)."""
        return self.finlite_data_dir

    def ensure_data_dir(self) -> None:
        """Create data directory if it doesn't exist."""
        self.finlite_data_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Settings are loaded from environment variables and .env file.
    The instance is cached for performance.

    Returns:
        Settings instance

    Examples:
        >>> settings = get_settings()
        >>> settings.ensure_data_dir()
    """
    settings = Settings()
    settings.ensure_data_dir()
    return settings
