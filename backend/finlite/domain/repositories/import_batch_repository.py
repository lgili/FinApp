"""
IImportBatchRepository - Interface para repositório de lotes de importação.

Define contrato para persistência de ImportBatch entities.
"""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from finlite.domain.entities.import_batch import ImportBatch, ImportSource, ImportStatus


class IImportBatchRepository(ABC):
    """
    Interface abstrata para repositório de lotes de importação.

    Examples:
        >>> class InMemoryImportBatchRepository(IImportBatchRepository):
        ...     def __init__(self):
        ...         self.batches = {}
        ...     
        ...     def add(self, batch: ImportBatch) -> None:
        ...         self.batches[batch.id] = batch
    """

    @abstractmethod
    def add(self, batch: ImportBatch) -> None:
        """
        Adiciona novo lote ao repositório.

        Args:
            batch: Lote a ser adicionado

        Raises:
            DuplicateImportError: Se lote com mesmo source/filename já existe
        """
        pass

    @abstractmethod
    def get(self, batch_id: UUID) -> ImportBatch:
        """
        Busca lote por ID.

        Args:
            batch_id: UUID do lote

        Returns:
            Lote encontrado

        Raises:
            ImportBatchNotFoundError: Se lote não existir
        """
        pass

    @abstractmethod
    def find_by_source(
        self,
        source: ImportSource,
        status: Optional[ImportStatus] = None,
    ) -> list[ImportBatch]:
        """
        Busca lotes por fonte.

        Args:
            source: Fonte de importação (NUBANK_CSV, OFX, etc)
            status: Filtrar por status (opcional)

        Returns:
            Lista de lotes (pode estar vazia)
        """
        pass

    @abstractmethod
    def find_by_filename(self, filename: str) -> Optional[ImportBatch]:
        """
        Busca lote por nome de arquivo.

        Útil para evitar duplicatas.

        Args:
            filename: Nome do arquivo

        Returns:
            Lote encontrado ou None
        """
        pass

    @abstractmethod
    def find_by_status(self, status: ImportStatus) -> list[ImportBatch]:
        """
        Busca lotes por status.

        Args:
            status: Status do lote (PENDING, COMPLETED, etc)

        Returns:
            Lista de lotes (pode estar vazia)
        """
        pass

    @abstractmethod
    def list_all(
        self,
        order_by: str = "created_at",
        descending: bool = True,
        limit: Optional[int] = None,
    ) -> list[ImportBatch]:
        """
        Lista todos os lotes.

        Args:
            order_by: Campo para ordenar ("created_at", "started_at")
            descending: Se True, ordena decrescente (mais recente primeiro)
            limit: Limite de resultados (opcional)

        Returns:
            Lista de lotes (pode estar vazia)
        """
        pass

    @abstractmethod
    def update(self, batch: ImportBatch) -> None:
        """
        Atualiza lote existente.

        Args:
            batch: Lote com dados atualizados

        Raises:
            ImportBatchNotFoundError: Se lote não existir
        """
        pass

    @abstractmethod
    def delete(self, batch_id: UUID) -> None:
        """
        Remove lote do repositório.

        Args:
            batch_id: UUID do lote a remover

        Raises:
            ImportBatchNotFoundError: Se lote não existir

        Note:
            Considere usar batch.mark_reversed() ao invés de deletar.
        """
        pass

    @abstractmethod
    def exists_by_filename(self, filename: str) -> bool:
        """
        Verifica se lote com determinado filename existe.

        Args:
            filename: Nome do arquivo

        Returns:
            True se lote existe
        """
        pass

    @abstractmethod
    def count(
        self,
        source: Optional[ImportSource] = None,
        status: Optional[ImportStatus] = None,
    ) -> int:
        """
        Conta lotes com filtros opcionais.

        Args:
            source: Filtrar por fonte (opcional)
            status: Filtrar por status (opcional)

        Returns:
            Número de lotes
        """
        pass
