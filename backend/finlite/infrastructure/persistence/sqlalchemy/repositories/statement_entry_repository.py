"""
SqlAlchemyStatementEntryRepository - Implementação concreta do IStatementEntryRepository.

Usa SQLAlchemy para persistir/recuperar StatementEntry do banco de dados.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from finlite.domain.entities.statement_entry import StatementEntry, StatementStatus
from finlite.domain.repositories.statement_entry_repository import IStatementEntryRepository
from finlite.infrastructure.persistence.sqlalchemy.mappers.statement_entry_mapper import (
    StatementEntryMapper,
)
from finlite.infrastructure.persistence.sqlalchemy.models import StatementEntryModel


class StatementEntryNotFoundError(Exception):
    """Exceção quando statement entry não é encontrado."""

    def __init__(self, entry_id: UUID):
        super().__init__(f"Statement entry not found: {entry_id}")
        self.entry_id = entry_id


class DuplicateEntryError(Exception):
    """Exceção quando entry duplicado é detectado."""

    def __init__(self, batch_id: UUID, external_id: str):
        super().__init__(f"Duplicate entry in batch {batch_id}: {external_id}")
        self.batch_id = batch_id
        self.external_id = external_id


class SqlAlchemyStatementEntryRepository(IStatementEntryRepository):
    """
    Repository concreto para StatementEntry usando SQLAlchemy.

    Implementa IStatementEntryRepository usando SQLAlchemy + StatementEntryMapper.

    Examples:
        >>> session = Session(engine)
        >>> repo = SqlAlchemyStatementEntryRepository(session)
        >>>
        >>> # Criar e salvar
        >>> entry = StatementEntry.create(
        ...     batch_id=batch_id,
        ...     external_id="001",
        ...     memo="Test",
        ...     amount=Decimal("100.00"),
        ...     currency="BRL",
        ...     occurred_at=datetime.now(),
        ... )
        >>> repo.add(entry)
        >>> session.commit()
    """

    def __init__(self, session: Session) -> None:
        """
        Inicializa repository com sessão SQLAlchemy.

        Args:
            session: SQLAlchemy session (gerenciada por UnitOfWork)
        """
        self._session = session

    def add(self, entry: StatementEntry) -> None:
        """
        Adiciona novo entry ao repositório.

        Args:
            entry: Entity do domínio para persistir

        Raises:
            DuplicateEntryError: Se entry com mesmo batch_id+external_id já existe

        Examples:
            >>> entry = StatementEntry.create(...)
            >>> repo.add(entry)
            >>> session.commit()
        """
        from finlite.infrastructure.persistence.sqlalchemy.mappers._uuid_helpers import int_to_uuid, uuid_to_int
        from finlite.infrastructure.persistence.sqlalchemy.models import ImportBatchModel
        
        # Check for duplicate
        if self.exists_external_id(entry.batch_id, entry.external_id):
            raise DuplicateEntryError(entry.batch_id, entry.external_id)

        # Find batch's integer ID
        batch_model = self._session.query(ImportBatchModel).filter_by(external_id=str(entry.batch_id)).first()
        batch_int_id = batch_model.id if batch_model else None
        
        model = StatementEntryMapper.to_model(entry, batch_int_id=batch_int_id, for_update=False)
        self._session.add(model)
        self._session.flush()  # Get generated ID
        # Note: Don't overwrite entry._id since it already has a valid UUID

    def get(self, entry_id: UUID) -> StatementEntry:
        """
        Busca entry por ID.

        Args:
            entry_id: UUID do entry

        Returns:
            StatementEntry entity

        Raises:
            StatementEntryNotFoundError: Se entry não existir

        Examples:
            >>> entry = repo.get(entry_id)
            >>> print(entry.memo)
        """
        model = self._session.get(StatementEntryModel, entry_id)
        if model is None:
            raise StatementEntryNotFoundError(entry_id)
        return StatementEntryMapper.to_entity(model)

    def find_by_batch(self, batch_id: UUID) -> list[StatementEntry]:
        """
        Busca todos entries de um batch.

        Args:
            batch_id: UUID do batch

        Returns:
            Lista de entries (pode ser vazia)

        Examples:
            >>> entries = repo.find_by_batch(batch_id)
            >>> for entry in entries:
            ...     print(entry.memo)
        """
        from finlite.infrastructure.persistence.sqlalchemy.models import ImportBatchModel
        
        # Find batch's integer ID
        batch_model = self._session.query(ImportBatchModel).filter_by(external_id=str(batch_id)).first()
        if not batch_model:
            return []
        
        stmt = (
            select(StatementEntryModel)
            .where(StatementEntryModel.batch_id == batch_model.id)
            .order_by(StatementEntryModel.occurred_at)
        )
        models = self._session.scalars(stmt).all()
        return [StatementEntryMapper.to_entity(model, batch_uuid=batch_id) for model in models]

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

        Examples:
            >>> pending = repo.find_by_status(StatementStatus.IMPORTED)
            >>> for entry in pending:
            ...     print(entry.memo)
        """
        stmt = (
            select(StatementEntryModel)
            .where(StatementEntryModel.status == status.value)
            .order_by(StatementEntryModel.occurred_at)
        )

        if batch_id is not None:
            stmt = stmt.where(StatementEntryModel.batch_id == batch_id)

        models = self._session.scalars(stmt).all()
        return [StatementEntryMapper.to_entity(model) for model in models]

    def find_pending(self, limit: Optional[int] = None) -> list[StatementEntry]:
        """
        Busca entries pendentes de processamento (status = IMPORTED).

        Args:
            limit: Limite de resultados (opcional)

        Returns:
            Lista de entries pendentes ordenados por occurred_at

        Examples:
            >>> pending = repo.find_pending(limit=100)
            >>> print(f"Pending: {len(pending)}")
        """
        from sqlalchemy.orm import joinedload
        from finlite.infrastructure.persistence.sqlalchemy.models import ImportBatchModel
        from finlite.infrastructure.persistence.sqlalchemy.mappers._uuid_helpers import int_to_uuid
        
        stmt = (
            select(StatementEntryModel)
            .options(joinedload(StatementEntryModel.batch))
            .where(StatementEntryModel.status == StatementStatus.IMPORTED.value)
            .order_by(StatementEntryModel.occurred_at)
        )

        if limit is not None:
            stmt = stmt.limit(limit)

        models = self._session.scalars(stmt).all()
        
        # Convert to entities, preserving batch UUIDs from external_id
        entries = []
        for model in models:
            batch_uuid = UUID(model.batch.external_id) if model.batch and model.batch.external_id else int_to_uuid(model.batch_id)
            entries.append(StatementEntryMapper.to_entity(model, batch_uuid=batch_uuid))
        
        return entries

    def find_by_external_id(self, batch_id: UUID, external_id: str) -> Optional[StatementEntry]:
        """
        Busca entry por batch_id + external_id.

        Args:
            batch_id: UUID do batch
            external_id: ID externo do entry

        Returns:
            Entry encontrado ou None

        Examples:
            >>> entry = repo.find_by_external_id(batch_id, "row_001")
        """
        stmt = select(StatementEntryModel).where(
            StatementEntryModel.batch_id == batch_id,
            StatementEntryModel.external_id == external_id,
        )
        model = self._session.scalar(stmt)

        if model is None:
            return None
        return StatementEntryMapper.to_entity(model)

    def update(self, entry: StatementEntry) -> None:
        """
        Atualiza entry existente.

        Args:
            entry: Entry a ser atualizado

        Raises:
            StatementEntryNotFoundError: Se entry não existir

        Examples:
            >>> entry = repo.get(entry_id)
            >>> entry.mark_posted(txn_id)
            >>> repo.update(entry)
            >>> session.commit()
        """
        model = self._session.get(StatementEntryModel, entry.id)
        if model is None:
            raise StatementEntryNotFoundError(entry.id)

        # Update fields
        StatementEntryMapper.update_model(model, entry)

    def delete(self, entry_id: UUID) -> None:
        """
        Remove entry do repositório.

        Args:
            entry_id: UUID do entry

        Raises:
            StatementEntryNotFoundError: Se entry não existir

        Examples:
            >>> repo.delete(entry_id)
            >>> session.commit()
        """
        model = self._session.get(StatementEntryModel, entry_id)
        if model is None:
            raise StatementEntryNotFoundError(entry_id)

        self._session.delete(model)

    def count_by_status(self, status: StatementStatus, batch_id: Optional[UUID] = None) -> int:
        """
        Conta entries por status.

        Args:
            status: Status a contar
            batch_id: Filtrar por batch específico (opcional)

        Returns:
            Número de entries

        Examples:
            >>> count = repo.count_by_status(StatementStatus.IMPORTED)
            >>> print(f"Pending: {count}")
        """
        stmt = select(func.count()).select_from(StatementEntryModel).where(
            StatementEntryModel.status == status.value
        )

        if batch_id is not None:
            stmt = stmt.where(StatementEntryModel.batch_id == batch_id)

        return self._session.scalar(stmt) or 0

    def exists_external_id(self, batch_id: UUID, external_id: str) -> bool:
        """
        Verifica se já existe entry com external_id no batch.

        Args:
            batch_id: UUID do batch
            external_id: ID externo

        Returns:
            True se existir

        Examples:
            >>> if not repo.exists_external_id(batch_id, "row_001"):
            ...     repo.add(entry)
        """
        from finlite.infrastructure.persistence.sqlalchemy.models import ImportBatchModel
        
        # Find batch's integer ID
        batch_model = self._session.query(ImportBatchModel).filter_by(external_id=str(batch_id)).first()
        if not batch_model:
            return False
        
        stmt = select(func.count()).select_from(StatementEntryModel).where(
            StatementEntryModel.batch_id == batch_model.id,
            StatementEntryModel.external_id == external_id,
        )
        count = self._session.scalar(stmt) or 0
        return count > 0
