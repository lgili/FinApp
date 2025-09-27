"""Database engine and session management."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from finlite.config import Settings, get_settings
from finlite.logging import get_logger

LOGGER = get_logger(__name__)

_ENGINE: Engine | None = None
_SESSION_FACTORY: sessionmaker[Session] | None = None


def _ensure_engine(settings: Settings | None = None) -> Engine:
    global _ENGINE, _SESSION_FACTORY
    if _ENGINE is not None:
        return _ENGINE
    resolved_settings = settings or get_settings()
    database_url = resolved_settings.database_url
    LOGGER.debug("Creating engine for %s", database_url)
    engine = create_engine(database_url, future=True, echo=False)

    if database_url.startswith("sqlite"):
        _configure_sqlite(engine)

    _ENGINE = engine
    _SESSION_FACTORY = sessionmaker(engine, expire_on_commit=False, future=True)
    return engine


def _configure_sqlite(engine: Engine) -> None:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):  # type: ignore[no-untyped-def]
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()


def get_engine(settings: Settings | None = None) -> Engine:
    return _ensure_engine(settings)


def get_session_factory(settings: Settings | None = None) -> sessionmaker[Session]:
    _ensure_engine(settings)
    assert _SESSION_FACTORY is not None  # defensive, _ensure_engine populates it
    return _SESSION_FACTORY


@contextmanager
def session_scope(settings: Settings | None = None) -> Generator[Session, None, None]:
    session_factory = get_session_factory(settings)
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def reset_engine() -> None:
    """Dispose the global engine/session factory. Intended for tests."""
    global _ENGINE, _SESSION_FACTORY
    if _ENGINE is not None:
        _ENGINE.dispose()
    _ENGINE = None
    _SESSION_FACTORY = None
