"""
TransactionMapper - Converte entre Domain Transaction e ORM TransactionModel.

O mapper é responsável por traduzir entre:
- Domain Entity (Transaction + Postings) ←→ ORM Models (TransactionModel + PostingModels)

Este é um mapper mais complexo pois precisa lidar com o aggregate root.

Note: Handles UUID (domain) ↔ Integer (database) conversion.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from finlite.domain.entities.transaction import Transaction
from finlite.domain.value_objects.money import Money
from finlite.domain.value_objects.posting import Posting
from finlite.infrastructure.persistence.sqlalchemy.models import (
    PostingModel,
    TransactionModel,
)
from finlite.infrastructure.persistence.sqlalchemy.mappers._uuid_helpers import (
    uuid_to_int,
    int_to_uuid,
)


class TransactionMapper:
    """
    Mapper bidirectional para Transaction ←→ TransactionModel.

    Também mapeia Postings (value objects) ←→ PostingModels.

    Examples:
        >>> # Domain → ORM
        >>> transaction = Transaction.create(...)
        >>> model = TransactionMapper.to_model(transaction)
        >>>
        >>> # ORM → Domain
        >>> transaction = TransactionMapper.to_entity(model)
    """

    @staticmethod
    def to_model(transaction: Transaction) -> TransactionModel:
        """
        Converte Domain Transaction para ORM TransactionModel.

        Args:
            transaction: Entity do domínio

        Returns:
            ORM model pronto para persistir (com postings)

        Examples:
            >>> transaction = Transaction.create(
            ...     date=date(2025, 10, 1),
            ...     description="Test",
            ...     postings=[...]
            ... )
            >>> model = TransactionMapper.to_model(transaction)
            >>> len(model.postings)
            2
        """
        # Cria transaction model
        model = TransactionModel(
            reference=str(transaction.id),  # Store UUID in reference column
            occurred_at=transaction.date,  # date → datetime (stored as occurred_at in DB)
            description=transaction.description,
            extra_data={
                "tags": list(transaction.tags),
                "notes": transaction.notes,
                "import_batch_id": str(transaction.import_batch_id) if transaction.import_batch_id else None,
            },
            created_at=transaction.created_at,
        )

        # Cria posting models  
        model.postings = [
            TransactionMapper._posting_to_model(posting, None)  # transaction_id will be set by relationship
            for posting in transaction.postings
        ]

        return model

    @staticmethod
    def to_entity(model: TransactionModel) -> Transaction:
        """
        Converte ORM TransactionModel para Domain Transaction.

        Args:
            model: ORM model do banco (com postings carregados)

        Returns:
            Entity do domínio

        Examples:
            >>> model = session.get(TransactionModel, tx_id)
            >>> transaction = TransactionMapper.to_entity(model)
            >>> transaction.is_balanced()
            True
        """
        # Converte postings
        postings = [
            TransactionMapper._model_to_posting(posting_model)
            for posting_model in model.postings
        ]

        # Extract UUID from reference or generate from integer ID
        if model.reference:
            try:
                transaction_id = UUID(model.reference)
            except (ValueError, TypeError):
                transaction_id = int_to_uuid(model.id)
        else:
            transaction_id = int_to_uuid(model.id)

        # Extract data from extra_data JSON
        extra = model.extra_data or {}
        tags = tuple(extra.get("tags", []))
        notes = extra.get("notes")
        import_batch_id_str = extra.get("import_batch_id")
        import_batch_id = UUID(import_batch_id_str) if import_batch_id_str else None

        # Cria transaction entity
        return Transaction(
            id=transaction_id,
            date=model.occurred_at.date() if isinstance(model.occurred_at, datetime) else model.occurred_at,
            description=model.description,
            postings=tuple(postings),  # list → tuple (imutável)
            tags=tags,
            notes=notes,
            import_batch_id=import_batch_id,
            created_at=model.created_at,
            updated_at=model.created_at,  # No updated_at in model
        )

    @staticmethod
    def update_model_from_entity(
        model: TransactionModel, transaction: Transaction
    ) -> None:
        """
        Atualiza ORM model existente com dados da entity.

        IMPORTANTE: Este método NÃO atualiza postings (que são imutáveis).
        Para alterar postings, delete e recrie a transação.

        Args:
            model: ORM model existente (será modificado)
            transaction: Entity com dados atualizados

        Examples:
            >>> model = session.get(TransactionModel, tx_id)
            >>> # Modificar apenas campos não-core
            >>> transaction.notes = "Updated notes"
            >>> TransactionMapper.update_model_from_entity(model, transaction)
        """
        model.reference = str(transaction.id)
        model.occurred_at = transaction.date
        model.description = transaction.description
        model.extra_data = {
            "tags": list(transaction.tags),
            "notes": transaction.notes,
            "import_batch_id": str(transaction.import_batch_id) if transaction.import_batch_id else None,
        }
        # NOTE: postings NÃO são atualizados (imutáveis)

    @staticmethod
    def _posting_to_model(posting: Posting, transaction_id) -> PostingModel:
        """
        Converte Posting (value object) para PostingModel (ORM).

        Args:
            posting: Value object do domínio
            transaction_id: ID da transação pai (can be None, will be set by relationship)

        Returns:
            ORM model do posting
        """
        # Convert account UUID to Integer ID by looking up via code
        # Note: This will be handled by the repository when saving
        return PostingModel(
            transaction_id=transaction_id,
            account_id=uuid_to_int(posting.account_id),  # Convert UUID to Int
            amount=posting.amount.amount,  # Money → Decimal
            currency=posting.amount.currency,
            memo=posting.notes,  # notes → memo (DB column name)
        )

    @staticmethod
    def _model_to_posting(model: PostingModel) -> Posting:
        """
        Converte PostingModel (ORM) para Posting (value object).

        Args:
            model: ORM model do banco

        Returns:
            Value object do domínio
        """
        # Convert Integer account_id back to UUID
        account_id = int_to_uuid(model.account_id)
        
        return Posting(
            account_id=account_id,
            amount=Money(
                amount=Decimal(str(model.amount)),  # Garantir Decimal
                currency=model.currency,
            ),
            notes=model.memo,  # memo → notes (domain attribute)
        )
