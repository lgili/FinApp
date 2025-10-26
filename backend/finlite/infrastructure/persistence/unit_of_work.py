"""
Unit of Work Pattern - Gerencia transações de banco de dados.

O UnitOfWork coordena repositories e garante atomicidade:
- Agrupa operações em uma transação
- Commit ou rollback conjunto
- Gerencia sessão SQLAlchemy

Referências:
- Martin Fowler: https://martinfowler.com/eaaCatalog/unitOfWork.html
- Cosmic Python: https://www.cosmicpython.com/book/chapter_06_uow.html
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from finlite.domain.repositories.account_repository import IAccountRepository
from finlite.domain.repositories.transaction_repository import ITransactionRepository
from finlite.domain.repositories.card_statement_repository import ICardStatementRepository


class IUnitOfWork(ABC):
    """
    Interface abstrata para Unit of Work.

    Coordena repositories e transações de banco.

    Examples:
        >>> with uow:
        ...     account = uow.accounts.get(account_id)
        ...     account.rename("New Name")
        ...     uow.accounts.update(account)
        ...     uow.commit()  # Atomicamente
    """

    # Repositories disponíveis
    accounts: IAccountRepository
    transactions: ITransactionRepository
    card_statements: ICardStatementRepository

    def __enter__(self) -> IUnitOfWork:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Context manager exit.

        Rollback automático se houver exceção.
        """
        if exc_type is not None:
            self.rollback()

    @abstractmethod
    def commit(self) -> None:
        """
        Comita todas as mudanças na transação.

        Examples:
            >>> with uow:
            ...     # Operações...
            ...     uow.commit()
        """
        ...

    @abstractmethod
    def rollback(self) -> None:
        """
        Reverte todas as mudanças da transação.

        Examples:
            >>> with uow:
            ...     try:
            ...         # Operações...
            ...         uow.commit()
            ...     except Exception:
            ...         uow.rollback()
            ...         raise
        """
        ...


# Type alias para dependency injection
UnitOfWork = Protocol


class AbstractUnitOfWork(IUnitOfWork):
    """
    Base abstrata para implementações de UnitOfWork.

    Fornece estrutura comum para diferentes backends (SQLAlchemy, etc).
    """

    def __enter__(self) -> AbstractUnitOfWork:
        """Inicia transação."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Finaliza transação (commit ou rollback)."""
        if exc_type is not None:
            self.rollback()
        # Não precisa commit automático - deve ser explícito

    def commit(self) -> None:
        """Comita transação."""
        self._commit()

    def rollback(self) -> None:
        """Reverte transação."""
        self._rollback()

    @abstractmethod
    def _commit(self) -> None:
        """Implementação específica de commit."""
        ...

    @abstractmethod
    def _rollback(self) -> None:
        """Implementação específica de rollback."""
        ...
