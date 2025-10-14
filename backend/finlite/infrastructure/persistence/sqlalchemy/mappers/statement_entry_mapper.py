"""
StatementEntryMapper - Converte entre Domain StatementEntry e ORM StatementEntryModel.

O mapper é responsável por traduzir entre:
- Domain Entity (StatementEntry) ←→ ORM Model (StatementEntryModel)

Garante que o domain permanece puro (sem dependências de SQLAlchemy).

Note: Uses Integer ID (database) and converts UUIDs for batch_id, suggested_account_id, transaction_id.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from finlite.domain.entities.statement_entry import StatementEntry, StatementStatus
from finlite.infrastructure.persistence.sqlalchemy.models import StatementEntryModel
from finlite.infrastructure.persistence.sqlalchemy.mappers._uuid_helpers import (
    uuid_to_int,
    int_to_uuid,
)


class StatementEntryMapper:
    """
    Mapper bidirectional para StatementEntry ←→ StatementEntryModel.

    Converts between UUID (domain) and Integer (database) IDs.

    Examples:
        >>> # Domain → ORM
        >>> entry = StatementEntry.create(...)
        >>> model = StatementEntryMapper.to_model(entry)
        >>>
        >>> # ORM → Domain
        >>> entry = StatementEntryMapper.to_entity(model)
    """

    @staticmethod
    def to_model(entry: StatementEntry, batch_int_id: int | None = None, for_update: bool = False) -> StatementEntryModel:
        """
        Converte Domain StatementEntry para ORM StatementEntryModel.

        Args:
            entry: Entity do domínio
            batch_int_id: Integer ID do batch (required for inserts)
            for_update: Se True, inclui o ID (para updates). Se False, omite o ID (para inserts).

        Returns:
            ORM model pronto para persistir

        Examples:
            >>> entry = StatementEntry.create(
            ...     batch_id=uuid4(),
            ...     external_id="001",
            ...     memo="Test",
            ...     amount=Decimal("100.00"),
            ...     currency="BRL",
            ...     occurred_at=datetime.now(),
            ... )
            >>> model = StatementEntryMapper.to_model(entry, batch_int_id=123)
            >>> model.external_id
            '001'
        """
        model_data = {
            "batch_id": batch_int_id if batch_int_id is not None else uuid_to_int(entry.batch_id),
            "external_id": entry.external_id,
            "payee": entry.payee,
            "memo": entry.memo,
            "amount": entry.amount,
            "currency": entry.currency,
            "occurred_at": entry.occurred_at,
            "status": entry.status.value,  # Enum to string
            "suggested_account_id": uuid_to_int(entry.suggested_account_id) if entry.suggested_account_id else None,
            "transaction_id": uuid_to_int(entry.transaction_id) if entry.transaction_id else None,
            "extra_data": entry.metadata,  # JSON field (mapped to 'metadata' column)
            "created_at": entry.created_at,
            "updated_at": entry.updated_at,
        }
        
        # Para updates, incluir o ID convertido de UUID
        if for_update and entry.id:
            model_data["id"] = uuid_to_int(entry.id)
        
        return StatementEntryModel(**model_data)

    @staticmethod
    def to_entity(model: StatementEntryModel, batch_uuid: UUID | None = None) -> StatementEntry:
        """
        Converte ORM StatementEntryModel para Domain StatementEntry.

        Args:
            model: ORM model do banco
            batch_uuid: UUID do batch (optional, to preserve correct UUID)

        Returns:
            Entity do domínio

        Examples:
            >>> model = StatementEntryModel(...)
            >>> entry = StatementEntryMapper.to_entity(model)
            >>> entry.external_id
            '001'
        """
        return StatementEntry(
            id=int_to_uuid(model.id),
            batch_id=batch_uuid if batch_uuid else int_to_uuid(model.batch_id),
            external_id=model.external_id,
            payee=model.payee,
            memo=model.memo,
            amount=Decimal(str(model.amount)),  # Ensure Decimal
            currency=model.currency,
            occurred_at=model.occurred_at,
            status=StatementStatus(model.status),  # String to enum
            suggested_account_id=int_to_uuid(model.suggested_account_id) if model.suggested_account_id else None,
            transaction_id=int_to_uuid(model.transaction_id) if model.transaction_id else None,
            metadata=model.extra_data or {},  # mapped from 'metadata' column
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def update_model(model: StatementEntryModel, entry: StatementEntry) -> None:
        """
        Atualiza campos do ORM model a partir do domain entity.

        Útil para update sem recriar o model inteiro.

        Args:
            model: ORM model existente
            entry: Domain entity com dados atualizados

        Examples:
            >>> entry = repo.get(entry_id)
            >>> entry.mark_posted(txn_id)
            >>> model = session.get(StatementEntryModel, entry.id)
            >>> StatementEntryMapper.update_model(model, entry)
        """
        model.batch_id = entry.batch_id
        model.external_id = entry.external_id
        model.payee = entry.payee
        model.memo = entry.memo
        model.amount = entry.amount
        model.currency = entry.currency
        model.occurred_at = entry.occurred_at
        model.status = entry.status.value
        model.suggested_account_id = entry.suggested_account_id
        model.transaction_id = entry.transaction_id
        model.extra_data = entry.metadata  # mapped to 'metadata' column
        model.updated_at = entry.updated_at
