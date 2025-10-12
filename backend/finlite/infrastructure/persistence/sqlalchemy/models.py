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
from uuid import UUID

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
    """

    __tablename__ = "accounts"

    # Primary Key (UUID)
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, nullable=False
    )

    # Attributes
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    account_type: Mapped[AccountTypeEnum] = mapped_column(
        Enum(AccountTypeEnum), nullable=False, index=True
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False)

    # Hierarchy
    parent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Lifecycle
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Timestamps (com defaults do Python)
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
        return f"<AccountModel(id={self.id}, name='{self.name}', type={self.account_type})>"


class TransactionModel(Base):
    """
    ORM Model para Transaction.

    Representa transações contábeis no banco de dados.
    Mapeado para domain.entities.Transaction via TransactionMapper.
    """

    __tablename__ = "transactions"

    # Primary Key (UUID)
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, nullable=False
    )

    # Attributes
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)

    # Optional fields
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Import tracking
    import_batch_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("import_batches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Timestamps (com defaults do Python)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    postings: Mapped[list[PostingModel]] = relationship(
        "PostingModel",
        back_populates="transaction",
        cascade="all, delete-orphan",
        order_by="PostingModel.id",
    )

    import_batch: Mapped[ImportBatchModel | None] = relationship("ImportBatchModel")

    def __repr__(self) -> str:
        """Debug representation."""
        return (
            f"<TransactionModel(id={self.id}, "
            f"date={self.date.date()}, "
            f"description='{self.description[:30]}...')>"
        )


class PostingModel(Base):
    """
    ORM Model para Posting.

    Representa lançamentos contábeis individuais.
    Parte do aggregate Transaction.
    """

    __tablename__ = "postings"

    # Primary Key (auto-increment)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign Keys
    transaction_id: Mapped[UUID] = mapped_column(
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("accounts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Amount
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)

    # Optional notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    transaction: Mapped[TransactionModel] = relationship(
        "TransactionModel", back_populates="postings"
    )
    account: Mapped[AccountModel] = relationship("AccountModel")

    # Constraints
    __table_args__ = (
        CheckConstraint("amount != 0", name="ck_posting_amount_non_zero"),
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
    """

    __tablename__ = "import_batches"

    # Primary Key (UUID)
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, nullable=False
    )

    # Attributes
    source: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")

    # Metadata JSON (renamed to avoid SQLAlchemy reserved word 'metadata')
    extra_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Timestamps (com defaults do Python)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        """Debug representation."""
        return f"<ImportBatchModel(id={self.id}, source='{self.source}', status='{self.status}')>"


# Future models (não implementados ainda na Fase 2):
# - StatementEntryModel (para fase de ingestion)
# - RuleModel (para fase de rules engine)
