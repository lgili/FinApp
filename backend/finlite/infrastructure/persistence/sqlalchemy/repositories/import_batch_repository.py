"""
SqlAlchemyImportBatchRepository - Implementação SQLAlchemy do repository de ImportBatch.

Implementa IImportBatchRepository usando SQLAlchemy como ORM.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from finlite.domain.entities.import_batch import ImportBatch, ImportSource, ImportStatus
from finlite.domain.repositories.import_batch_repository import IImportBatchRepository
from finlite.infrastructure.persistence.sqlalchemy.mappers.import_batch_mapper import (
    ImportBatchMapper,
)
from finlite.infrastructure.persistence.sqlalchemy.models import ImportBatchModel


class ImportBatchNotFoundError(Exception):
    """Exception lançada quando batch não é encontrado."""

    pass


class SqlAlchemyImportBatchRepository(IImportBatchRepository):
    """
    Implementação SQLAlchemy de IImportBatchRepository.

    Examples:
        >>> session = get_session()
        >>> repo = SqlAlchemyImportBatchRepository(session)
        >>> batch = repo.get(batch_id)
    """

    def __init__(self, session: Session) -> None:
        """
        Inicializa repository com session do SQLAlchemy.

        Args:
            session: SQLAlchemy session ativa
        """
        self._session = session

    def add(self, batch: ImportBatch) -> None:
        """
        Adiciona novo batch ao banco.

        Args:
            batch: ImportBatch entity

        Examples:
            >>> batch = ImportBatch.create(...)
            >>> repo.add(batch)
        """
        from finlite.infrastructure.persistence.sqlalchemy.mappers._uuid_helpers import int_to_uuid
        
        model = ImportBatchMapper.to_model(batch, for_update=False)
        self._session.add(model)
        self._session.flush()  # Get generated ID
        # Note: Don't overwrite batch._id since it already has a valid UUID
        # The UUID is preserved in external_id column

    def get(self, batch_id: UUID) -> ImportBatch:
        """
        Busca batch por ID.

        Args:
            batch_id: UUID do batch

        Returns:
            ImportBatch entity

        Raises:
            ImportBatchNotFoundError: Se batch não existir

        Examples:
            >>> batch = repo.get(batch_id)
        """
        # Query by external_id (UUID stored as string)
        stmt = select(ImportBatchModel).where(
            ImportBatchModel.external_id == str(batch_id)
        )
        model = self._session.execute(stmt).scalar_one_or_none()

        if model is None:
            raise ImportBatchNotFoundError(f"ImportBatch not found: {batch_id}")

        return ImportBatchMapper.to_entity(model)

    def find_by_sha256(self, file_sha256: str) -> Optional[ImportBatch]:
        """
        Busca batch por hash SHA256 do arquivo.

        Usado para deduplicação - evitar importar o mesmo arquivo duas vezes.

        Args:
            file_sha256: Hash SHA256 do arquivo (64 caracteres hex)

        Returns:
            ImportBatch se encontrado, None caso contrário

        Examples:
            >>> existing = repo.find_by_sha256("abc123...")
            >>> if existing:
            ...     print(f"File already imported as batch {existing.id}")
        """
        stmt = select(ImportBatchModel).where(
            ImportBatchModel.file_sha256 == file_sha256
        )
        model = self._session.execute(stmt).scalar_one_or_none()

        if model is None:
            return None

        return ImportBatchMapper.to_entity(model)

    def find_by_source(
        self,
        source: ImportSource,
        status: Optional[ImportStatus] = None,
    ) -> list[ImportBatch]:
        """
        Busca batches por fonte de importação.

        Args:
            source: ImportSource enum
            status: Filtro opcional por status

        Returns:
            Lista de batches (pode ser vazia)

        Examples:
            >>> nubank_batches = repo.find_by_source(ImportSource.NUBANK_CSV)
        """
        stmt = select(ImportBatchModel).where(
            ImportBatchModel.source == source.value
        )
        
        if status is not None:
            stmt = stmt.where(ImportBatchModel.status == status.value)
        
        stmt = stmt.order_by(ImportBatchModel.created_at.desc())
        models = self._session.execute(stmt).scalars().all()

        return [ImportBatchMapper.to_entity(model) for model in models]

    def find_by_filename(self, filename: str) -> Optional[ImportBatch]:
        """
        Busca batch por nome de arquivo.

        Args:
            filename: Nome do arquivo

        Returns:
            ImportBatch se encontrado, None caso contrário

        Examples:
            >>> existing = repo.find_by_filename("extrato-2025-10.csv")
        """
        stmt = select(ImportBatchModel).where(
            ImportBatchModel.filename == filename
        )
        model = self._session.execute(stmt).scalar_one_or_none()

        if model is None:
            return None

        return ImportBatchMapper.to_entity(model)

    def find_by_status(self, status: ImportStatus) -> list[ImportBatch]:
        """
        Busca batches por status.

        Args:
            status: ImportStatus enum

        Returns:
            Lista de batches (pode ser vazia)

        Examples:
            >>> pending_batches = repo.find_by_status(ImportStatus.PENDING)
        """
        stmt = (
            select(ImportBatchModel)
            .where(ImportBatchModel.status == status.value)
            .order_by(ImportBatchModel.created_at.desc())
        )
        models = self._session.execute(stmt).scalars().all()

        return [ImportBatchMapper.to_entity(model) for model in models]

    def list_all(self, limit: int = 100, offset: int = 0) -> list[ImportBatch]:
        """
        Lista todos os batches com paginação.

        Args:
            limit: Número máximo de resultados (default: 100)
            offset: Offset para paginação (default: 0)

        Returns:
            Lista de batches ordenados por data de criação (mais recente primeiro)

        Examples:
            >>> batches = repo.list_all(limit=50)
            >>> for batch in batches:
            ...     print(f"{batch.id}: {batch.source} - {batch.status}")
        """
        stmt = (
            select(ImportBatchModel)
            .order_by(ImportBatchModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        models = self._session.execute(stmt).scalars().all()

        return [ImportBatchMapper.to_entity(model) for model in models]

    def exists_by_filename(self, filename: str) -> bool:
        """
        Verifica se batch com determinado filename existe.

        Args:
            filename: Nome do arquivo

        Returns:
            True se batch existe, False caso contrário

        Examples:
            >>> if repo.exists_by_filename("extrato.csv"):
            ...     print("File already imported")
        """
        from sqlalchemy import func

        stmt = select(func.count(ImportBatchModel.id)).where(
            ImportBatchModel.filename == filename
        )
        count = self._session.execute(stmt).scalar_one()
        return count > 0

    def count(
        self,
        source: Optional[ImportSource] = None,
        status: Optional[ImportStatus] = None,
    ) -> int:
        """
        Conta batches com filtros opcionais.

        Args:
            source: Filtrar por fonte (opcional)
            status: Filtrar por status (opcional)

        Returns:
            Número de batches

        Examples:
            >>> total = repo.count()
            >>> pending_nubank = repo.count(
            ...     source=ImportSource.NUBANK_CSV,
            ...     status=ImportStatus.PENDING
            ... )
        """
        from sqlalchemy import func

        stmt = select(func.count(ImportBatchModel.id))
        
        if source is not None:
            stmt = stmt.where(ImportBatchModel.source == source.value)
        
        if status is not None:
            stmt = stmt.where(ImportBatchModel.status == status.value)
        
        return self._session.execute(stmt).scalar_one()

    def update(self, batch: ImportBatch) -> None:
        """
        Atualiza batch existente.

        Args:
            batch: ImportBatch entity com dados atualizados

        Raises:
            ImportBatchNotFoundError: Se batch não existir

        Examples:
            >>> batch = repo.get(batch_id)
            >>> batch.mark_completed(transaction_count=42)
            >>> repo.update(batch)
        """
        # Query by external_id (UUID)
        stmt = select(ImportBatchModel).where(
            ImportBatchModel.external_id == str(batch.id)
        )
        model = self._session.execute(stmt).scalar_one_or_none()

        if model is None:
            raise ImportBatchNotFoundError(f"ImportBatch not found: {batch.id}")

        ImportBatchMapper.update_model(model, batch)
        self._session.flush()

    def delete(self, batch_id: UUID) -> None:
        """
        Remove batch do banco.

        Args:
            batch_id: UUID do batch

        Raises:
            ImportBatchNotFoundError: Se batch não existir

        Note:
            Isso removerá todos os StatementEntries relacionados (CASCADE).

        Examples:
            >>> repo.delete(batch_id)
        """
        stmt = select(ImportBatchModel).where(
            ImportBatchModel.external_id == str(batch_id)
        )
        model = self._session.execute(stmt).scalar_one_or_none()

        if model is None:
            raise ImportBatchNotFoundError(f"ImportBatch not found: {batch_id}")

        self._session.delete(model)
        self._session.flush()

    def count_by_status(self, status: ImportStatus) -> int:
        """
        Conta batches por status.

        Args:
            status: ImportStatus enum

        Returns:
            Número de batches com aquele status

        Examples:
            >>> pending_count = repo.count_by_status(ImportStatus.PENDING)
            >>> print(f"{pending_count} pending imports")
        """
        return self.count(status=status)
