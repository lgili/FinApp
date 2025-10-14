"""
ImportBatch Entity - Representa um lote de importação.

Um lote agrupa transações importadas de uma fonte externa
(ex: CSV do Nubank, OFX do banco).

Permite rastrear:
- Quais transações vieram de onde
- Quando foram importadas
- Evitar duplicatas
- Reverter importação se necessário

Referência: Domain-Driven Design - Aggregate Root
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class ImportSource(str, Enum):
    """
    Enum para fontes de importação.

    Attributes:
        NUBANK_CSV: CSV exportado do Nubank
        OFX: Arquivo OFX bancário
        MANUAL: Entrada manual (não é importação de fato)
        API: Importação via API externa
        OTHER: Outra fonte

    Examples:
        >>> ImportSource.NUBANK_CSV
        <ImportSource.NUBANK_CSV: 'NUBANK_CSV'>
    """

    NUBANK_CSV = "NUBANK_CSV"
    OFX = "OFX"
    MANUAL = "MANUAL"
    API = "API"
    OTHER = "OTHER"


class ImportStatus(str, Enum):
    """
    Enum para status de importação.

    Attributes:
        PENDING: Importação iniciada mas não finalizada
        COMPLETED: Importação finalizada com sucesso
        FAILED: Importação falhou
        REVERSED: Importação foi revertida

    Examples:
        >>> ImportStatus.COMPLETED
        <ImportStatus.COMPLETED: 'COMPLETED'>
    """

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REVERSED = "REVERSED"


@dataclass
class ImportBatch:
    """
    Entity representando um lote de importação (Aggregate Root).

    Um lote agrupa transações importadas e mantém metadados
    sobre a importação.

    Attributes:
        id: Identificador único (UUID)
        source: Fonte da importação (NUBANK_CSV, OFX, etc)
        status: Status atual (PENDING, COMPLETED, FAILED, REVERSED)
        filename: Nome do arquivo importado (opcional)
        file_sha256: Hash SHA256 do arquivo (para deduplicação)
        transaction_count: Número de transações importadas
        metadata: Metadados adicionais (JSON-serializável)
        error_message: Mensagem de erro se falhou (opcional)
        started_at: Data/hora de início da importação
        completed_at: Data/hora de conclusão (opcional)
        created_at: Data de criação do registro
        updated_at: Data de última atualização

    Examples:
        >>> # Criar lote de importação do Nubank
        >>> batch = ImportBatch.create(
        ...     source=ImportSource.NUBANK_CSV,
        ...     filename="nubank_2025-10.csv",
        ...     metadata={"account": "Assets:Nubank"}
        ... )
        >>> 
        >>> # Marcar como completo após importar 42 transações
        >>> batch.mark_completed(transaction_count=42)
        >>> batch.status
        <ImportStatus.COMPLETED: 'COMPLETED'>
    """

    id: UUID
    source: ImportSource
    status: ImportStatus
    filename: Optional[str] = None
    file_sha256: Optional[str] = None
    transaction_count: int = 0
    metadata: dict = field(default_factory=dict)
    error_message: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validações após inicialização."""
        self._validate_transaction_count()

    @classmethod
    def create(
        cls,
        source: ImportSource,
        filename: Optional[str] = None,
        file_sha256: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> ImportBatch:
        """
        Factory method para criar novo lote de importação.

        Args:
            source: Fonte da importação
            filename: Nome do arquivo (opcional)
            file_sha256: Hash SHA256 do arquivo (opcional)
            metadata: Metadados adicionais (opcional)

        Returns:
            Nova instância de ImportBatch em status PENDING

        Examples:
            >>> batch = ImportBatch.create(
            ...     source=ImportSource.NUBANK_CSV,
            ...     filename="nubank_2025-10.csv",
            ...     file_sha256="abc123...",
            ...     metadata={"account": "Assets:Nubank", "year": 2025}
            ... )
            >>> batch.status
            <ImportStatus.PENDING: 'PENDING'>
        """
        return cls(
            id=uuid4(),
            source=source,
            status=ImportStatus.PENDING,
            filename=filename,
            file_sha256=file_sha256,
            metadata=metadata or {},
        )

    def mark_completed(self, transaction_count: int) -> None:
        """
        Marca importação como completa.

        Args:
            transaction_count: Número de transações importadas

        Raises:
            ValueError: Se status não for PENDING

        Examples:
            >>> batch = ImportBatch.create(ImportSource.NUBANK_CSV)
            >>> batch.mark_completed(42)
            >>> batch.status
            <ImportStatus.COMPLETED: 'COMPLETED'>
            >>> batch.transaction_count
            42
        """
        if self.status != ImportStatus.PENDING:
            raise ValueError(
                f"Cannot mark batch as completed: current status is {self.status.value}"
            )

        self.status = ImportStatus.COMPLETED
        self.transaction_count = transaction_count
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_failed(self, error_message: str) -> None:
        """
        Marca importação como falha.

        Args:
            error_message: Descrição do erro

        Raises:
            ValueError: Se status não for PENDING

        Examples:
            >>> batch = ImportBatch.create(ImportSource.OFX)
            >>> batch.mark_failed("Invalid OFX format")
            >>> batch.status
            <ImportStatus.FAILED: 'FAILED'>
            >>> batch.error_message
            'Invalid OFX format'
        """
        if self.status != ImportStatus.PENDING:
            raise ValueError(
                f"Cannot mark batch as failed: current status is {self.status.value}"
            )

        self.status = ImportStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_reversed(self) -> None:
        """
        Marca importação como revertida.

        Transações associadas devem ser deletadas/marcadas externamente.

        Raises:
            ValueError: Se status não for COMPLETED

        Examples:
            >>> batch = ImportBatch.create(ImportSource.NUBANK_CSV)
            >>> batch.mark_completed(10)
            >>> batch.mark_reversed()
            >>> batch.status
            <ImportStatus.REVERSED: 'REVERSED'>
        """
        if self.status != ImportStatus.COMPLETED:
            raise ValueError(
                f"Cannot reverse batch: current status is {self.status.value}. "
                "Only COMPLETED batches can be reversed."
            )

        self.status = ImportStatus.REVERSED
        self.updated_at = datetime.utcnow()

    def is_completed(self) -> bool:
        """
        Verifica se importação foi completada.

        Returns:
            True se status é COMPLETED

        Examples:
            >>> batch = ImportBatch.create(ImportSource.NUBANK_CSV)
            >>> batch.is_completed()
            False
            >>> batch.mark_completed(5)
            >>> batch.is_completed()
            True
        """
        return self.status == ImportStatus.COMPLETED

    def is_failed(self) -> bool:
        """
        Verifica se importação falhou.

        Returns:
            True se status é FAILED

        Examples:
            >>> batch = ImportBatch.create(ImportSource.OFX)
            >>> batch.is_failed()
            False
            >>> batch.mark_failed("Parse error")
            >>> batch.is_failed()
            True
        """
        return self.status == ImportStatus.FAILED

    def is_reversed(self) -> bool:
        """
        Verifica se importação foi revertida.

        Returns:
            True se status é REVERSED

        Examples:
            >>> batch = ImportBatch.create(ImportSource.API)
            >>> batch.mark_completed(3)
            >>> batch.mark_reversed()
            >>> batch.is_reversed()
            True
        """
        return self.status == ImportStatus.REVERSED

    def can_be_reversed(self) -> bool:
        """
        Verifica se importação pode ser revertida.

        Returns:
            True se status é COMPLETED

        Examples:
            >>> batch = ImportBatch.create(ImportSource.NUBANK_CSV)
            >>> batch.can_be_reversed()
            False  # PENDING não pode ser revertido
            >>> 
            >>> batch.mark_completed(5)
            >>> batch.can_be_reversed()
            True  # COMPLETED pode ser revertido
        """
        return self.status == ImportStatus.COMPLETED

    def add_metadata(self, key: str, value: any) -> None:
        """
        Adiciona metadado ao lote.

        Args:
            key: Chave do metadado
            value: Valor (deve ser JSON-serializável)

        Examples:
            >>> batch = ImportBatch.create(ImportSource.NUBANK_CSV)
            >>> batch.add_metadata("account_id", "12345")
            >>> batch.metadata["account_id"]
            '12345'
        """
        self.metadata[key] = value
        self.updated_at = datetime.utcnow()

    def get_metadata(self, key: str, default: any = None) -> any:
        """
        Retorna metadado do lote.

        Args:
            key: Chave do metadado
            default: Valor padrão se chave não existir

        Returns:
            Valor do metadado ou default

        Examples:
            >>> batch = ImportBatch.create(ImportSource.OFX)
            >>> batch.add_metadata("bank", "Nubank")
            >>> batch.get_metadata("bank")
            'Nubank'
            >>> batch.get_metadata("nonexistent", "default")
            'default'
        """
        return self.metadata.get(key, default)

    def _validate_transaction_count(self) -> None:
        """
        Valida transaction_count.

        Raises:
            ValueError: Se transaction_count for negativo
        """
        if self.transaction_count < 0:
            raise ValueError(
                f"transaction_count cannot be negative, got {self.transaction_count}"
            )

    def __eq__(self, other: object) -> bool:
        """
        Igualdade baseada em ID (entity identity).

        Examples:
            >>> batch1 = ImportBatch.create(ImportSource.NUBANK_CSV)
            >>> batch2 = ImportBatch.create(ImportSource.NUBANK_CSV)
            >>> batch1 == batch2
            False  # IDs diferentes
        """
        if not isinstance(other, ImportBatch):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash baseado em ID (para usar em sets/dicts)."""
        return hash(self.id)

    def __str__(self) -> str:
        """
        Representação string legível.

        Returns:
            Formato: "source (status): N transactions"

        Examples:
            >>> batch = ImportBatch.create(ImportSource.NUBANK_CSV, "file.csv")
            >>> batch.mark_completed(42)
            >>> str(batch)
            'NUBANK_CSV (COMPLETED): 42 transactions'
        """
        filename_part = f" [{self.filename}]" if self.filename else ""
        return (
            f"{self.source.value} ({self.status.value}): "
            f"{self.transaction_count} transactions{filename_part}"
        )

    def __repr__(self) -> str:
        """Representação técnica para debug."""
        return (
            f"ImportBatch(id={self.id!r}, source={self.source!r}, "
            f"status={self.status!r}, transaction_count={self.transaction_count})"
        )
