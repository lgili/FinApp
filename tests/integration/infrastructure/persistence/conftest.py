"""
Pytest fixtures for infrastructure integration tests.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from finlite.infrastructure.persistence.sqlalchemy.models import Base
from finlite.infrastructure.persistence.sqlalchemy.repositories.account_repository import (
    SqlAlchemyAccountRepository
)


@pytest.fixture(scope="function")
def in_memory_engine():
    """Create an in-memory SQLite engine for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def session_factory(in_memory_engine):
    """Create a session factory for testing."""
    return sessionmaker(bind=in_memory_engine)


@pytest.fixture(scope="function")
def session(session_factory) -> Session:
    """Create a database session for direct ORM access in tests."""
    session = session_factory()
    yield session
    session.close()


class SimpleUnitOfWork:
    """Simplified UnitOfWork for testing AccountRepository only."""
    
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.session = None
        self.accounts = None
    
    def __enter__(self):
        self.session = self.session_factory()
        self.accounts = SqlAlchemyAccountRepository(self.session)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            # Sem exceções, mas NÃO fazemos commit automático
            pass
        else:
            self.session.rollback()
        self.session.close()
    
    def commit(self):
        """Commit the current transaction."""
        self.session.commit()
    
    def rollback(self):
        """Rollback the current transaction."""
        self.session.rollback()


@pytest.fixture(scope="function")
def uow(session_factory):
    """Create a simplified Unit of Work instance for testing AccountRepository."""
    return SimpleUnitOfWork(session_factory)
