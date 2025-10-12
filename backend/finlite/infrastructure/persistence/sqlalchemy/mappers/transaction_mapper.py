"""
TransactionMapper - Converte entre Domain Transaction e ORM TransactionModel.

O mapper é responsável por traduzir entre:
- Domain Entity (Transaction + Postings) ←→ ORM Models (TransactionModel + PostingModels)

Este é um mapper mais complexo pois precisa lidar com o aggregate root.
"""

from __future__ import annotations

from decimal import Decimal

from finlite.domain.entities.transaction import Transaction
from finlite.domain.value_objects.money import Money
from finlite.domain.value_objects.posting import Posting
from finlite.infrastructure.persistence.sqlalchemy.models import (
    PostingModel,
    TransactionModel,
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
            id=transaction.id,
            date=transaction.date,
            description=transaction.description,
            tags=list(transaction.tags),  # tuple → list para JSON
            notes=transaction.notes,
            import_batch_id=transaction.import_batch_id,
            created_at=transaction.created_at,
            updated_at=transaction.updated_at,
        )

        # Cria posting models
        model.postings = [
            TransactionMapper._posting_to_model(posting, transaction.id)
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

        # Cria transaction entity
        return Transaction(
            id=model.id,
            date=model.date,  # Já é date (não datetime)
            description=model.description,
            postings=tuple(postings),  # list → tuple (imutável)
            tags=tuple(model.tags) if model.tags else (),  # list → tuple
            notes=model.notes,
            import_batch_id=model.import_batch_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
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
        model.description = transaction.description
        model.tags = list(transaction.tags)
        model.notes = transaction.notes
        model.updated_at = transaction.updated_at
        # NOTE: postings NÃO são atualizados (imutáveis)

    @staticmethod
    def _posting_to_model(posting: Posting, transaction_id) -> PostingModel:
        """
        Converte Posting (value object) para PostingModel (ORM).

        Args:
            posting: Value object do domínio
            transaction_id: ID da transação pai

        Returns:
            ORM model do posting
        """
        return PostingModel(
            transaction_id=transaction_id,
            account_id=posting.account_id,
            amount=posting.amount.amount,  # Money → Decimal
            currency=posting.amount.currency,
            notes=posting.notes,
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
        return Posting(
            account_id=model.account_id,
            amount=Money(
                amount=Decimal(str(model.amount)),  # Garantir Decimal
                currency=model.currency,
            ),
            notes=model.notes,
        )
