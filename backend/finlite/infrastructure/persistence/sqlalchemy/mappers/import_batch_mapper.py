"""
ImportBatchMapper - Converte entre Domain ImportBatch e ORM ImportBatchModel.

O mapper é responsável por traduzir entre:
- Domain Entity (ImportBatch com UUID) ←→ ORM Model (ImportBatchModel com Integer ID)

Garante que o domain permanece puro (sem dependências de SQLAlchemy).

Note: Uses Integer ID (database) and stores UUID in external_id column.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from finlite.domain.entities.import_batch import ImportBatch, ImportSource, ImportStatus
from finlite.infrastructure.persistence.sqlalchemy.models import ImportBatchModel
from finlite.infrastructure.persistence.sqlalchemy.mappers._uuid_helpers import (
    uuid_to_int,
    int_to_uuid,
)


class ImportBatchMapper:
    """
    Mapper bidirectional para ImportBatch ←→ ImportBatchModel.

    Converts between UUID (domain) and Integer (database) IDs.
    Stores UUID in 'external_id' column for full recovery.

    Examples:
        >>> # Domain → ORM
        >>> batch = ImportBatch.create(...)
        >>> model = ImportBatchMapper.to_model(batch)
        >>>
        >>> # ORM → Domain
        >>> batch = ImportBatchMapper.to_entity(model)
    """

    @staticmethod
    def to_model(batch: ImportBatch, for_update: bool = False) -> ImportBatchModel:
        """
        Converte Domain ImportBatch para ORM ImportBatchModel.

        Args:
            batch: Entity do domínio
            for_update: Se True, inclui o ID (para updates). Se False, omite o ID (para inserts).

        Returns:
            ORM model pronto para persistir

        Examples:
            >>> batch = ImportBatch.create(
            ...     source=ImportSource.NUBANK_CSV,
            ...     filename="extrato.csv",
            ... )
            >>> model = ImportBatchMapper.to_model(batch)
            >>> model.source
            'NUBANK_CSV'
        """
        model_data = {
            "source": batch.source.value,  # Enum to string
            "external_id": str(batch.id),  # Store UUID here
            "status": batch.status.value,  # Enum to string
            "filename": batch.filename,
            "file_sha256": batch.file_sha256,
            "transaction_count": batch.transaction_count,
            "error_message": batch.error_message,
            "extra_data": batch.metadata,  # mapped to 'metadata' column
            "imported_at": batch.started_at,
            "completed_at": batch.completed_at,
            "created_at": batch.created_at,
            "updated_at": batch.updated_at,
        }
        
        # Para updates, incluir o ID convertido de UUID
        if for_update and batch.id:
            model_data["id"] = uuid_to_int(batch.id)
        
        return ImportBatchModel(**model_data)

    @staticmethod
    def to_entity(model: ImportBatchModel) -> ImportBatch:
        """
        Converte ORM ImportBatchModel para Domain ImportBatch.

        Args:
            model: ORM model do banco

        Returns:
            Entity do domínio

        Examples:
            >>> model = session.get(ImportBatchModel, 123)
            >>> batch = ImportBatchMapper.to_entity(model)
            >>> batch.source
            <ImportSource.NUBANK_CSV: 'NUBANK_CSV'>
        """
        # Use external_id as UUID if available, otherwise generate from Integer ID
        if model.external_id:
            try:
                batch_id = UUID(model.external_id)
            except (ValueError, AttributeError):
                batch_id = int_to_uuid(model.id)
        else:
            batch_id = int_to_uuid(model.id)

        return ImportBatch(
            id=batch_id,
            source=ImportSource(model.source),  # String to enum
            status=ImportStatus(model.status),  # String to enum
            filename=model.filename,
            file_sha256=model.file_sha256,
            transaction_count=model.transaction_count,
            metadata=model.extra_data or {},  # mapped from 'metadata' column
            error_message=model.error_message,
            started_at=model.imported_at,
            completed_at=model.completed_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def update_model(model: ImportBatchModel, batch: ImportBatch) -> None:
        """
        Atualiza campos do ORM model a partir do domain entity.

        Útil para update sem recriar o model inteiro.

        Args:
            model: ORM model existente
            batch: Domain entity com dados atualizados

        Examples:
            >>> batch = repo.get(batch_id)
            >>> batch.mark_completed(transaction_count=42)
            >>> model = session.get(ImportBatchModel, model_id)
            >>> ImportBatchMapper.update_model(model, batch)
        """
        model.source = batch.source.value
        model.external_id = str(batch.id)
        model.status = batch.status.value
        model.filename = batch.filename
        model.file_sha256 = batch.file_sha256
        model.transaction_count = batch.transaction_count
        model.error_message = batch.error_message
        model.extra_data = batch.metadata
        model.imported_at = batch.started_at
        model.completed_at = batch.completed_at
        model.updated_at = batch.updated_at
