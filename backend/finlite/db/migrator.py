"""Helpers to interact with Alembic migrations programmatically."""

from __future__ import annotations

from pathlib import Path

from alembic.config import Config as AlembicConfig

from alembic import command
from finlite.config import Settings, get_settings


def _alembic_cfg(settings: Settings | None = None) -> AlembicConfig:
    resolved_settings = settings or get_settings()
    base_path = Path(__file__).resolve().parents[2]
    cfg = AlembicConfig(str(base_path / "alembic.ini"))
    cfg.set_main_option("script_location", str(base_path / "alembic"))
    cfg.set_main_option("sqlalchemy.url", resolved_settings.database_url)
    return cfg


def upgrade_head(settings: Settings | None = None) -> None:
    command.upgrade(_alembic_cfg(settings), "head")


def downgrade_base(settings: Settings | None = None) -> None:
    command.downgrade(_alembic_cfg(settings), "base")
