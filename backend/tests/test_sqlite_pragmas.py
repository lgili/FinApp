from __future__ import annotations

from finlite.config import Settings
from finlite.db.session import get_engine


def test_sqlite_pragmas_enabled(settings: Settings) -> None:
    engine = get_engine(settings)
    with engine.connect() as connection:
        foreign_keys = connection.exec_driver_sql("PRAGMA foreign_keys").scalar()
        journal_mode = connection.exec_driver_sql("PRAGMA journal_mode").scalar()
    assert foreign_keys == 1
    assert str(journal_mode).lower() == "wal"
