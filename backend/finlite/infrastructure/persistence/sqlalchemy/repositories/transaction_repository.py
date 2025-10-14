"""
SqlAlchemyTransactionRepository - Implementação concreta do ITransactionRepository.

Usa SQLAlchemy para persistir/recuperar Transactions do banco de dados.
Converte entre Domain (Transaction) e ORM (TransactionModel) via TransactionMapper.
"""

from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from finlite.domain.entities.transaction import Transaction
from finlite.domain.repositories.transaction_repository import ITransactionRepository
from finlite.infrastructure.persistence.sqlalchemy.mappers.transaction_mapper import (
    TransactionMapper,
)
from finlite.infrastructure.persistence.sqlalchemy.models import TransactionModel, PostingModel


class SqlAlchemyTransactionRepository(ITransactionRepository):
    """
    Repository concreto para Transaction usando SQLAlchemy.

    Implementa ITransactionRepository usando SQLAlchemy + TransactionMapper.

    Examples:
        >>> session = Session(engine)
        >>> repo = SqlAlchemyTransactionRepository(session)
        >>>
        >>> # Criar e salvar
        >>> transaction = Transaction.create(...)
        >>> repo.add(transaction)
        >>> session.commit()
        >>>
        >>> # Buscar
        >>> found = repo.get(transaction.id)
    """

    def __init__(self, session: Session) -> None:
        """
        Inicializa repository com sessão SQLAlchemy.

        Args:
            session: SQLAlchemy session (gerenciada por UnitOfWork)
        """
        self._session = session

    def add(self, transaction: Transaction) -> None:
        """
        Adiciona nova transação ao repositório.

        Args:
            transaction: Entity do domínio para persistir

        Examples:
            >>> transaction = Transaction.create(...)
            >>> repo.add(transaction)
            >>> session.commit()
        """
        from finlite.infrastructure.persistence.sqlalchemy.mappers._uuid_helpers import int_to_uuid
        
        model = TransactionMapper.to_model(transaction)
        self._session.add(model)
        self._session.flush()  # Get the generated ID
        # Update transaction with the generated ID (reconstructed from Integer)
        transaction._id = int_to_uuid(model.id)

    def get(self, transaction_id: UUID) -> Transaction:
        """
        Busca transação por ID.

        IMPORTANTE: Eager load postings para evitar lazy loading.

        Args:
            transaction_id: UUID da transação

        Returns:
            Transaction entity

        Raises:
            TransactionNotFoundError: Se transação não existir

        Examples:
            >>> transaction = repo.get(transaction_id)
            >>> print(transaction.description)
        """
        from finlite.domain.exceptions import TransactionNotFoundError

        # Try to find by reference (UUID stored as string)
        stmt = (
            select(TransactionModel)
            .where(TransactionModel.reference == str(transaction_id))
            .options(joinedload(TransactionModel.postings))
        )
        model = self._session.scalar(stmt)

        if model is None:
            raise TransactionNotFoundError(transaction_id)
        return TransactionMapper.to_entity(model)

    def find_by_account(
        self,
        account_id: UUID,
        limit: Optional[int] = None,
    ) -> list[Transaction]:
        """
        Busca transações que afetam uma conta.

        Args:
            account_id: UUID da conta
            limit: Limite de resultados (opcional)

        Returns:
            Lista de Transaction entities

        Examples:
            >>> # Todas as transações da conta
            >>> txs = repo.find_by_account(account_id)
            >>>
            >>> # Últimas 10 transações da conta
            >>> txs = repo.find_by_account(account_id, limit=10)
        """
        from finlite.infrastructure.persistence.sqlalchemy.mappers._uuid_helpers import uuid_to_int
        
        # Convert UUID to Integer ID
        account_int_id = uuid_to_int(account_id)
        
        # Query base: join com postings
        stmt = (
            select(TransactionModel)
            .join(TransactionModel.postings)
            .where(PostingModel.account_id == account_int_id)
            .options(joinedload(TransactionModel.postings))
            .order_by(TransactionModel.occurred_at.desc())
        )

        # Limite
        if limit is not None:
            stmt = stmt.limit(limit)

        models = self._session.scalars(stmt).unique().all()
        return [TransactionMapper.to_entity(model) for model in models]

    def find_by_date_range(
        self,
        start_date: date,
        end_date: date,
        account_id: Optional[UUID] = None,
    ) -> list[Transaction]:
        """
        Busca transações em um período.

        Args:
            start_date: Data inicial (inclusive)
            end_date: Data final (inclusive)
            account_id: Filtrar por conta específica (opcional)

        Returns:
            Lista de Transaction entities

        Examples:
            >>> # Transações de outubro/2025
            >>> txs = repo.find_by_date_range(
            ...     start_date=date(2025, 10, 1),
            ...     end_date=date(2025, 10, 31)
            ... )
            >>>
            >>> # Transações de uma conta específica em outubro
            >>> txs = repo.find_by_date_range(
            ...     start_date=date(2025, 10, 1),
            ...     end_date=date(2025, 10, 31),
            ...     account_id=account_id
            ... )
        """
        stmt = (
            select(TransactionModel)
            .where(
                TransactionModel.occurred_at >= start_date,
                TransactionModel.occurred_at <= end_date,
            )
            .options(joinedload(TransactionModel.postings))
        )

        # Filtro de conta (se fornecido)
        if account_id:
            stmt = stmt.join(TransactionModel.postings).where(
                TransactionModel.postings.any(account_id=account_id)
            )

        stmt = stmt.order_by(TransactionModel.occurred_at.desc())

        models = self._session.scalars(stmt).unique().all()
        return [TransactionMapper.to_entity(model) for model in models]

    def find_by_import_batch(self, batch_id: UUID) -> list[Transaction]:
        """
        Busca transações de um lote de importação.

        Args:
            batch_id: UUID do lote de importação

        Returns:
            Lista de Transaction entities

        Examples:
            >>> txs = repo.find_by_import_batch(batch_id)
        """
        stmt = (
            select(TransactionModel)
            .where(TransactionModel.import_batch_id == batch_id)
            .options(joinedload(TransactionModel.postings))
            .order_by(TransactionModel.occurred_at)
        )

        models = self._session.scalars(stmt).all()
        return [TransactionMapper.to_entity(model) for model in models]

    def exists(self, transaction_id: UUID) -> bool:
        """
        Verifica se transação existe.

        Args:
            transaction_id: UUID da transação

        Returns:
            True se existe

        Examples:
            >>> if repo.exists(transaction_id):
            ...     print("Transação existe")
        """
        stmt = select(TransactionModel.id).where(TransactionModel.id == transaction_id)
        result = self._session.scalar(stmt)
        return result is not None

    def delete(self, transaction_id: UUID) -> None:
        """
        Remove transação do repositório.

        Cascade delete remove postings automaticamente.

        Args:
            transaction_id: UUID da transação

        Raises:
            TransactionNotFoundError: Se transação não existe

        Examples:
            >>> repo.delete(transaction_id)
            >>> session.commit()
        """
        from finlite.domain.exceptions import TransactionNotFoundError

        # Find by reference (UUID stored as string)
        model = self._session.query(TransactionModel).filter_by(reference=str(transaction_id)).first()

        if model is None:
            raise TransactionNotFoundError(transaction_id)

        self._session.delete(model)

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
            Lista de Transaction entities

        Examples:
            >>> # Transações com tag "food" OU "transport"
            >>> txs = repo.find_by_tags(["food", "transport"])
            >>>
            >>> # Transações com tag "food" E "essential"
            >>> txs = repo.find_by_tags(
            ...     ["food", "essential"],
            ...     match_all=True
            ... )
        """
        from sqlalchemy import and_, or_, func

        stmt = select(TransactionModel).options(joinedload(TransactionModel.postings))

        if match_all:
            # Todas as tags devem estar presentes (AND)
            # Para SQLite/JSON, precisamos verificar se cada tag está no array
            conditions = []
            for tag in tags:
                # Usando JSON extract para SQLite
                conditions.append(
                    func.json_extract(TransactionModel.tags, f"$[*]").like(f"%{tag}%")
                )
            stmt = stmt.where(and_(*conditions))
        else:
            # Pelo menos uma tag deve estar presente (OR)
            conditions = []
            for tag in tags:
                conditions.append(
                    func.json_extract(TransactionModel.tags, f"$[*]").like(f"%{tag}%")
                )
            stmt = stmt.where(or_(*conditions))

        stmt = stmt.order_by(TransactionModel.occurred_at.desc())

        models = self._session.scalars(stmt).unique().all()
        return [TransactionMapper.to_entity(model) for model in models]

    def search_description(self, query: str) -> list[Transaction]:
        """
        Busca transações por texto na descrição.

        Args:
            query: Texto para buscar (case-insensitive)

        Returns:
            Lista de Transaction entities

        Examples:
            >>> txs = repo.search_description("restaurant")
        """
        stmt = (
            select(TransactionModel)
            .where(TransactionModel.description.ilike(f"%{query}%"))
            .options(joinedload(TransactionModel.postings))
            .order_by(TransactionModel.occurred_at.desc())
        )

        models = self._session.scalars(stmt).unique().all()
        return [TransactionMapper.to_entity(model) for model in models]

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
            Lista de Transaction entities

        Examples:
            >>> # Últimas 50 transações
            >>> txs = repo.list_all(limit=50)
            >>>
            >>> # Transações mais antigas primeiro
            >>> txs = repo.list_all(descending=False)
        """
        stmt = select(TransactionModel).options(joinedload(TransactionModel.postings))

        # Ordenação
        if order_by == "date":
            order_field = TransactionModel.occurred_at
        elif order_by == "created_at":
            order_field = TransactionModel.created_at
        else:
            order_field = TransactionModel.occurred_at

        if descending:
            stmt = stmt.order_by(order_field.desc())
        else:
            stmt = stmt.order_by(order_field.asc())

        # Limite
        if limit is not None:
            stmt = stmt.limit(limit)

        models = self._session.scalars(stmt).unique().all()
        return [TransactionMapper.to_entity(model) for model in models]

    def update(self, transaction: Transaction) -> None:
        """
        Atualiza transação existente.

        ATENÇÃO: Implementação complexa devido aos postings.
        Recomenda-se delete + add ao invés de update.

        Args:
            transaction: Entity com dados atualizados

        Raises:
            TransactionNotFoundError: Se transação não existe

        Examples:
            >>> transaction = repo.get(transaction_id)
            >>> # Modificar transaction...
            >>> repo.update(transaction)
            >>> session.commit()
        """
        from finlite.domain.exceptions import TransactionNotFoundError

        model = self._session.get(TransactionModel, transaction.id)

        if model is None:
            raise TransactionNotFoundError(transaction.id)

        # Update básico (sem postings por enquanto - complexo)
        model.date = transaction.date
        model.description = transaction.description
        model.tags = list(transaction.tags) if transaction.tags else []
        model.import_batch_id = transaction.import_batch_id

        # TODO: Update postings requires deleting old ones and creating new ones
        # For now, recommend using delete + add instead of update
        # See: https://docs.sqlalchemy.org/en/20/orm/cascades.html

    def delete_by_import_batch(self, batch_id: UUID) -> int:
        """
        Remove todas as transações de um lote.

        Útil para reverter importações.

        Args:
            batch_id: UUID do lote

        Returns:
            Número de transações deletadas

        Examples:
            >>> deleted_count = repo.delete_by_import_batch(batch_id)
            >>> print(f"Deletadas {deleted_count} transações")
            >>> session.commit()
        """
        from sqlalchemy import delete

        stmt = delete(TransactionModel).where(
            TransactionModel.import_batch_id == batch_id
        )

        result = self._session.execute(stmt)
        return result.rowcount

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

        Examples:
            >>> # Total de transações
            >>> total = repo.count()
            >>>
            >>> # Transações de outubro/2025
            >>> count = repo.count(
            ...     start_date=date(2025, 10, 1),
            ...     end_date=date(2025, 10, 31)
            ... )
            >>>
            >>> # Transações de uma conta
            >>> count = repo.count(account_id=account_id)
        """
        from sqlalchemy import func

        stmt = select(func.count(TransactionModel.id))

        # Filtros de data
        if start_date:
            stmt = stmt.where(TransactionModel.occurred_at >= start_date)
        if end_date:
            stmt = stmt.where(TransactionModel.occurred_at <= end_date)

        # Filtro de conta (join com postings)
        if account_id:
            stmt = stmt.join(TransactionModel.postings).where(
                TransactionModel.postings.any(account_id=account_id)
            )

        return self._session.scalar(stmt) or 0
