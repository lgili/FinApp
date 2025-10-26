"""
SQLAlchemy ORM Models - Infrastructure Layer.

Estes models representam a estrutura do banco de dados.
São separados das entities do domínio e conectados via mappers.

Diferenças vs Legacy:
- UUIDs ao invés de Integer IDs
- Nomes de colunas alinhados com domain entities
- Relacionamentos simplificados
"""

from __future__ import annotations

import enum
from datetime import date, datetime
from decimal import Decimal
from typing import Any, ClassVar
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class para todos os ORM models."""

    type_annotation_map: ClassVar[dict[type, Any]] = {
        Decimal: Numeric(18, 4),
        UUID: PG_UUID(as_uuid=True),
    }


class AccountTypeEnum(str, enum.Enum):
    """Enum de tipos de conta (ORM)."""

    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    EQUITY = "EQUITY"
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


class AccountModel(Base):
    """
    ORM Model para Account.

    Representa contas contábeis no banco de dados.
    Mapeado para domain.entities.Account via AccountMapper.
    
    Note: Using Integer ID to match legacy database schema.
    """

    __tablename__ = "accounts"

    # Primary Key (Integer for backwards compatibility)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Attributes
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    code: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    card_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Hierarchy
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Lifecycle
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    parent: Mapped[AccountModel | None] = relationship(
        "AccountModel",
        remote_side="AccountModel.id",
        back_populates="children",
        foreign_keys=[parent_id],
    )
    children: Mapped[list[AccountModel]] = relationship(
        "AccountModel", back_populates="parent", foreign_keys=[parent_id]
    )

    def __repr__(self) -> str:
        """Debug representation."""
        return f"<AccountModel(id={self.id}, name='{self.name}', type={self.type})>"


class TransactionModel(Base):
    """
    ORM Model para Transaction.

    Representa transações contábeis no banco de dados.
    Mapeado para domain.entities.Transaction via TransactionMapper.
    
    Note: Using Integer ID to match legacy database schema.
    Column names match DB: occurred_at (not date), reference, metadata.
    """

    __tablename__ = "transactions"

    # Primary Key (Integer for backwards compatibility)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Attributes - using DB column names
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    
    # Metadata JSON - SQLAlchemy reserves 'metadata' name, so we use 'extra_data' in Python
    # and map it to 'metadata' column in the database
    extra_data: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, default=dict, nullable=False
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    postings: Mapped[list[PostingModel]] = relationship(
        "PostingModel",
        back_populates="transaction",
        cascade="all, delete-orphan",
        order_by="PostingModel.id",
    )

    def __repr__(self) -> str:
        """Debug representation."""
        return (
            f"<TransactionModel(id={self.id}, "
            f"occurred_at={self.occurred_at}, "
            f"description='{self.description[:30]}...')>"
        )


class PostingModel(Base):
    """
    ORM Model para Posting.

    Representa lançamentos contábeis individuais.
    Parte do aggregate Transaction.
    
    Note: Using Integer IDs to match legacy database schema.
    Column names match DB: memo (not notes).
    """

    __tablename__ = "postings"

    # Primary Key (Integer auto-increment)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign Keys (Integer to match legacy schema)
    transaction_id: Mapped[int] = mapped_column(
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Amount
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)

    # Optional memo (using DB column name)
    memo: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    transaction: Mapped[TransactionModel] = relationship(
        "TransactionModel", back_populates="postings"
    )
    account: Mapped[AccountModel] = relationship("AccountModel")

    # Constraints
    __table_args__ = (
        CheckConstraint("amount != 0", name="ck_posting_non_zero"),
    )

    def __repr__(self) -> str:
        """Debug representation."""
        return (
            f"<PostingModel(id={self.id}, "
            f"account_id={self.account_id}, "
            f"amount={self.amount} {self.currency})>"
        )

    def __repr__(self) -> str:
        """Debug representation."""
        return (
            f"<PostingModel(id={self.id}, "
            f"account_id={self.account_id}, "
            f"amount={self.amount} {self.currency})>"
        )


class ImportBatchModel(Base):
    """
    ORM Model para ImportBatch.

    Rastreia lotes de importação de statements.
    
    Note: Column names match database schema (imported_at, metadata).
    Properties are mapped in Python code.
    """

    __tablename__ = "import_batches"

    # Primary Key (Integer for backwards compatibility with legacy schema)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Attributes
    source: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    transaction_count: Mapped[int] = mapped_column(default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Note: 'external_id' column exists in DB but not in our enhanced model
    # It's kept for backwards compatibility but will be nullable in new imports
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)

    # Metadata JSON - using 'extra_data' in Python and mapping to 'metadata' column
    extra_data: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, default=dict, nullable=False
    )

    # Timestamps - using 'imported_at' to match DB schema
    imported_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    entries: Mapped[list[StatementEntryModel]] = relationship(
        "StatementEntryModel",
        back_populates="batch",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """Debug representation."""
        return f"<ImportBatchModel(id={self.id}, source='{self.source}', status='{self.status}')>"


class StatementEntryModel(Base):
    """
    ORM Model para StatementEntry.

    Representa lançamentos de extrato bancário importados.
    Mapeado para domain.entities.StatementEntry via StatementEntryMapper.
    
    Note: Column names match database schema (Integer IDs, metadata instead of extra_metadata).
    """

    __tablename__ = "statement_entries"

    # Primary Key (Integer for backwards compatibility with legacy schema)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign Keys (Integer to match legacy schema)
    batch_id: Mapped[int] = mapped_column(
        ForeignKey("import_batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Attributes
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)
    payee: Mapped[str | None] = mapped_column(String(255), nullable=True)
    memo: Mapped[str | None] = mapped_column(Text, nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="imported", index=True
    )

    # Optional fields (Integer IDs to match legacy schema)
    suggested_account_id: Mapped[int | None] = mapped_column(
        ForeignKey("accounts.id", ondelete="SET NULL"),
        nullable=True,
    )
    transaction_id: Mapped[int | None] = mapped_column(
        ForeignKey("transactions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Metadata JSON - using 'extra_data' in Python and mapping to 'metadata' column
    extra_data: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, default=dict, nullable=False
    )

    # Timestamps (com defaults do Python)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    batch: Mapped[ImportBatchModel] = relationship(
        "ImportBatchModel", back_populates="entries"
    )
    suggested_account: Mapped[AccountModel | None] = relationship(
        "AccountModel", foreign_keys=[suggested_account_id]
    )
    transaction: Mapped[TransactionModel | None] = relationship(
        "TransactionModel", foreign_keys=[transaction_id]
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("batch_id", "external_id", name="uq_statement_entry_unique"),
    )

    def __repr__(self) -> str:
        """Debug representation."""
        return (
            f"<StatementEntryModel(id={self.id}, "
            f"external_id='{self.external_id}', "
            f"status='{self.status}', "
            f"amount={self.amount} {self.currency})>"
        )


class CardStatementModel(Base):
    """ORM model for persisted credit card statements."""

    __tablename__ = "card_statements"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    card_account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    period_end: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    closing_day: Mapped[int] = mapped_column(nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    items: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    account: Mapped[AccountModel] = relationship("AccountModel")

    __table_args__ = (
        UniqueConstraint(
            "card_account_id",
            "period_start",
            "period_end",
            name="uq_card_statement_period",
        ),
    )


# Future models (não implementados ainda):
# - RuleModel (para fase de rules engine)
