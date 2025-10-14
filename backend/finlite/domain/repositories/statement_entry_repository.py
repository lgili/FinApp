"""
IStatementEntryRepository - Interface para repositório de statement entries.

Define contrato para persistência de StatementEntry entities.
"""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from finlite.domain.entities.statement_entry import StatementEntry, StatementStatus


class IStatementEntryRepository(ABC):
    """
    Interface abstrata para repositório de statement entries.

    Examples:
        >>> class InMemoryStatementEntryRepository(IStatementEntryRepository):
        ...     def __init__(self):
        ...         self.entries = {}
        ...
        ...     def add(self, entry: StatementEntry) -> None:
        ...         self.entries[entry.id] = entry
    """

    @abstractmethod
    def add(self, entry: StatementEntry) -> None:
        """
        Adiciona novo entry ao repositório.

        Args:
            entry: Entry a ser adicionado

        Raises:
            DuplicateEntryError: Se entry com mesmo batch_id+external_id já existe
        """
        pass

    @abstractmethod
    def get(self, entry_id: UUID) -> StatementEntry:
        """
        Busca entry por ID.

        Args:
            entry_id: UUID do entry

        Returns:
            Entry encontrado

        Raises:
            StatementEntryNotFoundError: Se entry não existir
        """
        pass

    @abstractmethod
    def find_by_batch(self, batch_id: UUID) -> list[StatementEntry]:
        """
        Busca todos entries de um batch.

        Args:
            batch_id: UUID do batch

        Returns:
            Lista de entries (pode ser vazia)
        """
        pass

    @abstractmethod
    def find_by_status(
        self,
        status: StatementStatus,
        batch_id: Optional[UUID] = None,
    ) -> list[StatementEntry]:
        """
        Busca entries por status.

        Args:
            status: Status a filtrar
            batch_id: Filtrar por batch específico (opcional)

        Returns:
            Lista de entries (pode ser vazia)
        """
        pass

    @abstractmethod
    def find_pending(self, limit: Optional[int] = None) -> list[StatementEntry]:
        """
        Busca entries pendentes de processamento (status = IMPORTED).

        Args:
            limit: Limite de resultados (opcional)

        Returns:
            Lista de entries pendentes ordenados por occurred_at
        """
        pass

    @abstractmethod
    def find_by_external_id(self, batch_id: UUID, external_id: str) -> Optional[StatementEntry]:
        """
        Busca entry por batch_id + external_id.

        Args:
            batch_id: UUID do batch
            external_id: ID externo do entry

        Returns:
            Entry encontrado ou None
        """
        pass

    @abstractmethod
    def update(self, entry: StatementEntry) -> None:
        """
        Atualiza entry existente.

        Args:
            entry: Entry a ser atualizado

        Raises:
            StatementEntryNotFoundError: Se entry não existir
        """
        pass

    @abstractmethod
    def delete(self, entry_id: UUID) -> None:
        """
        Remove entry do repositório.

        Args:
            entry_id: UUID do entry

        Raises:
            StatementEntryNotFoundError: Se entry não existir
        """
        pass

    @abstractmethod
    def count_by_status(self, status: StatementStatus, batch_id: Optional[UUID] = None) -> int:
        """
        Conta entries por status.

        Args:
            status: Status a contar
            batch_id: Filtrar por batch específico (opcional)

        Returns:
            Número de entries
        """
        pass

    @abstractmethod
    def exists_external_id(self, batch_id: UUID, external_id: str) -> bool:
        """
        Verifica se já existe entry com external_id no batch.

        Args:
            batch_id: UUID do batch
            external_id: ID externo

        Returns:
            True se existir
        """
        pass
