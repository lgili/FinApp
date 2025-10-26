"""
SqlAlchemyUnitOfWork - Implementação do UnitOfWork com SQLAlchemy.

Gerencia sessão SQLAlchemy e repositories concretos.
"""

from __future__ import annotations

from typing import Callable

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from finlite.infrastructure.persistence.sqlalchemy.repositories import (
    SqlAlchemyAccountRepository,
    SqlAlchemyCardStatementRepository,
    SqlAlchemyTransactionRepository,
)
from finlite.infrastructure.persistence.unit_of_work import AbstractUnitOfWork


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    """
    Unit of Work implementado com SQLAlchemy.

    Gerencia sessão SQLAlchemy e fornece repositories.

    Examples:
        >>> # Com session factory
        >>> engine = create_engine("sqlite:///:memory:")
        >>> session_factory = sessionmaker(bind=engine)
        >>> uow = SqlAlchemyUnitOfWork(session_factory)
        >>>
        >>> # Usando como context manager
        >>> with uow:
        ...     account = Account.create("Assets:Checking", AccountType.ASSET, "BRL")
        ...     uow.accounts.add(account)
        ...     uow.commit()
        >>>
        >>> # Verificar
        >>> with uow:
        ...     found = uow.accounts.get(account.id)
        ...     assert found is not None
    """

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        """
        Inicializa UnitOfWork com session factory.

        Args:
            session_factory: Callable que retorna Session (sessionmaker)

        Examples:
            >>> from sqlalchemy.orm import sessionmaker
            >>> session_factory = sessionmaker(bind=engine)
            >>> uow = SqlAlchemyUnitOfWork(session_factory)
        """
        self.session_factory = session_factory
        self.session: Session | None = None

    def __enter__(self) -> SqlAlchemyUnitOfWork:
        """
        Inicia transação.

        Cria nova sessão e inicializa repositories.
        """
        self.session = self.session_factory()

        # Inicializa repositories com a sessão
        self.accounts = SqlAlchemyAccountRepository(self.session)
        self.transactions = SqlAlchemyTransactionRepository(self.session)
        self.card_statements = SqlAlchemyCardStatementRepository(self.session)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Finaliza transação.

        Rollback automático se houver exceção.
        Fecha sessão sempre.
        """
        try:
            if exc_type is not None:
                self.rollback()
        finally:
            if self.session:
                self.session.close()
                self.session = None

    def _commit(self) -> None:
        """Comita transação SQLAlchemy."""
        if self.session is None:
            raise RuntimeError("UnitOfWork not entered (use 'with' statement)")
        self.session.commit()

    def _rollback(self) -> None:
        """Reverte transação SQLAlchemy."""
        if self.session is None:
            raise RuntimeError("UnitOfWork not entered (use 'with' statement)")
        self.session.rollback()

    @staticmethod
    def create_for_testing(engine: Engine | None = None) -> SqlAlchemyUnitOfWork:
        """
        Factory para criar UnitOfWork para testes.

        Args:
            engine: Engine SQLAlchemy (padrão: in-memory SQLite)

        Returns:
            UnitOfWork configurado para testes

        Examples:
            >>> # In-memory SQLite
            >>> uow = SqlAlchemyUnitOfWork.create_for_testing()
            >>>
            >>> # Custom engine
            >>> engine = create_engine("sqlite:///test.db")
            >>> uow = SqlAlchemyUnitOfWork.create_for_testing(engine)
        """
        if engine is None:
            # In-memory SQLite para testes
            engine = create_engine(
                "sqlite:///:memory:",
                echo=False,  # Desabilita logs SQL
            )

        # Cria tabelas
        from finlite.infrastructure.persistence.sqlalchemy.models import Base

        Base.metadata.create_all(engine)

        # Cria session factory
        session_factory = sessionmaker(bind=engine, expire_on_commit=False)

        return SqlAlchemyUnitOfWork(session_factory)
