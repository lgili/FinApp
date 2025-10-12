"""
ITransactionRepository - Interface para repositório de transações.

Define contrato para persistência de Transaction entities.
Implementações concretas devem seguir esta interface.

Padrão: Repository Pattern (Domain-Driven Design)
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import Optional
from uuid import UUID

from finlite.domain.entities.transaction import Transaction


class ITransactionRepository(ABC):
    """
    Interface abstrata para repositório de transações.

    Examples:
        >>> # Implementação concreta
        >>> class SQLTransactionRepository(ITransactionRepository):
        ...     def add(self, transaction: Transaction) -> None:
        ...         # Salva no PostgreSQL
        ...         pass
        ...
        >>> # Implementação mock para testes
        >>> class InMemoryTransactionRepository(ITransactionRepository):
        ...     def __init__(self):
        ...         self.transactions = {}
        ...     
        ...     def add(self, transaction: Transaction) -> None:
        ...         self.transactions[transaction.id] = transaction
    """

    @abstractmethod
    def add(self, transaction: Transaction) -> None:
        """
        Adiciona nova transação ao repositório.

        Args:
            transaction: Transação a ser adicionada

        Raises:
            UnbalancedTransactionError: Se transação não balancear
        """
        pass

    @abstractmethod
    def get(self, transaction_id: UUID) -> Transaction:
        """
        Busca transação por ID.

        Args:
            transaction_id: UUID da transação

        Returns:
            Transação encontrada

        Raises:
            TransactionNotFoundError: Se transação não existir
        """
        pass

    @abstractmethod
    def find_by_date_range(
        self,
        start_date: date,
        end_date: date,
        account_id: Optional[UUID] = None,
    ) -> list[Transaction]:
        """
        Busca transações em um período.

        Args:
            start_date: Data inicial (inclusiva)
            end_date: Data final (inclusiva)
            account_id: Filtrar por conta específica (opcional)

        Returns:
            Lista de transações (pode estar vazia)

        Examples:
            >>> from datetime import date
            >>> repo = InMemoryTransactionRepository()
            >>> 
            >>> # Todas as transações de outubro/2025
            >>> transactions = repo.find_by_date_range(
            ...     date(2025, 10, 1),
            ...     date(2025, 10, 31)
            ... )
            >>> 
            >>> # Transações de uma conta específica
            >>> account_id = uuid4()
            >>> transactions = repo.find_by_date_range(
            ...     date(2025, 10, 1),
            ...     date(2025, 10, 31),
            ...     account_id=account_id
            ... )
        """
        pass

    @abstractmethod
    def find_by_account(
        self,
        account_id: UUID,
        limit: Optional[int] = None,
    ) -> list[Transaction]:
        """
        Busca transações de uma conta.

        Args:
            account_id: UUID da conta
            limit: Limite de resultados (opcional)

        Returns:
            Lista de transações (pode estar vazia)
        """
        pass

    @abstractmethod
    def find_by_import_batch(self, batch_id: UUID) -> list[Transaction]:
        """
        Busca transações de um lote de importação.

        Args:
            batch_id: UUID do lote

        Returns:
            Lista de transações (pode estar vazia)
        """
        pass

    @abstractmethod
    def find_by_tags(
        self,
        tags: list[str],
        match_all: bool = False,
    ) -> list[Transaction]:
        """
        Busca transações por tags.

        Args:
            tags: Lista de tags para buscar
            match_all: Se True, transação deve ter TODAS as tags.
                       Se False, basta ter UMA das tags.

        Returns:
            Lista de transações (pode estar vazia)

        Examples:
            >>> # Transações com tag "food" OU "transport"
            >>> transactions = repo.find_by_tags(["food", "transport"])
            >>> 
            >>> # Transações com tag "food" E "essential"
            >>> transactions = repo.find_by_tags(
            ...     ["food", "essential"],
            ...     match_all=True
            ... )
        """
        pass

    @abstractmethod
    def search_description(self, query: str) -> list[Transaction]:
        """
        Busca transações por texto na descrição.

        Args:
            query: Texto para buscar (case-insensitive)

        Returns:
            Lista de transações (pode estar vazia)
        """
        pass

    @abstractmethod
    def list_all(
        self,
        order_by: str = "date",
        descending: bool = True,
        limit: Optional[int] = None,
    ) -> list[Transaction]:
        """
        Lista todas as transações.

        Args:
            order_by: Campo para ordenar ("date", "created_at")
            descending: Se True, ordena decrescente (mais recente primeiro)
            limit: Limite de resultados (opcional)

        Returns:
            Lista de transações (pode estar vazia)
        """
        pass

    @abstractmethod
    def update(self, transaction: Transaction) -> None:
        """
        Atualiza transação existente.

        Args:
            transaction: Transação com dados atualizados

        Raises:
            TransactionNotFoundError: Se transação não existir
        """
        pass

    @abstractmethod
    def delete(self, transaction_id: UUID) -> None:
        """
        Remove transação do repositório.

        Args:
            transaction_id: UUID da transação a remover

        Raises:
            TransactionNotFoundError: Se transação não existir
        """
        pass

    @abstractmethod
    def delete_by_import_batch(self, batch_id: UUID) -> int:
        """
        Remove todas as transações de um lote.

        Útil para reverter importações.

        Args:
            batch_id: UUID do lote

        Returns:
            Número de transações deletadas
        """
        pass

    @abstractmethod
    def count(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        account_id: Optional[UUID] = None,
    ) -> int:
        """
        Conta transações com filtros opcionais.

        Args:
            start_date: Data inicial (inclusiva, opcional)
            end_date: Data final (inclusiva, opcional)
            account_id: Filtrar por conta (opcional)

        Returns:
            Número de transações
        """
        pass
