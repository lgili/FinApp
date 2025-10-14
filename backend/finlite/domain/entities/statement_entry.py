"""
StatementEntry Entity - Representa um lançamento de extrato bancário importado.

Um entry representa uma linha do extrato bancário (CSV, OFX, etc.)
que foi importada mas ainda não necessariamente convertida em transação contábil.

Status Flow:
- IMPORTED: Recém importado, aguardando processamento
- MATCHED: Reconciliado com transação existente (duplicata detectada)
- POSTED: Convertido em transação contábil no ledger

Referência: Domain-Driven Design - Entity
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class StatementStatus(str, Enum):
    """Status de processamento do entry."""

    IMPORTED = "imported"  # Recém importado
    MATCHED = "matched"  # Reconciliado com transação existente
    POSTED = "posted"  # Convertido em transação contábil


@dataclass
class StatementEntry:
    """
    Entity representando um lançamento de extrato bancário.

    Attributes:
        id: Identificador único (UUID)
        batch_id: ID do batch de importação ao qual pertence
        external_id: ID externo (FITID do OFX, row hash do CSV, etc.)
        payee: Beneficiário/comerciante (opcional)
        memo: Descrição/memo da transação
        amount: Valor (positivo = crédito, negativo = débito)
        currency: Moeda (ISO 4217)
        occurred_at: Data/hora da transação original
        status: Status de processamento
        suggested_account_id: ID da conta sugerida por regras (opcional)
        transaction_id: ID da transação contábil criada (se POSTED)
        metadata: Metadados adicionais (JSON-serializável)
        created_at: Data de criação do registro
        updated_at: Data de última atualização

    Examples:
        >>> # Criar entry de importação
        >>> entry = StatementEntry.create(
        ...     batch_id=uuid4(),
        ...     external_id="nubank_2025-10-12_001",
        ...     memo="MERCADO EXTRA",
        ...     amount=Decimal("-150.00"),
        ...     currency="BRL",
        ...     occurred_at=datetime(2025, 10, 12, 10, 30),
        ... )
        >>> entry.status
        <StatementStatus.IMPORTED: 'imported'>
        >>>
        >>> # Marcar como postado
        >>> txn_id = uuid4()
        >>> entry.mark_posted(txn_id)
        >>> entry.status
        <StatementStatus.POSTED: 'posted'>
        >>> entry.transaction_id == txn_id
        True
    """

    id: UUID
    batch_id: UUID
    external_id: str
    memo: str
    amount: Decimal
    currency: str
    occurred_at: datetime
    status: StatementStatus
    payee: Optional[str] = None
    suggested_account_id: Optional[UUID] = None
    transaction_id: Optional[UUID] = None
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validações após inicialização."""
        self._validate_currency()
        self._validate_amount()
        self._validate_external_id()

    @classmethod
    def create(
        cls,
        batch_id: UUID,
        external_id: str,
        memo: str,
        amount: Decimal,
        currency: str,
        occurred_at: datetime,
        payee: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> StatementEntry:
        """
        Factory method para criar novo entry.

        Args:
            batch_id: UUID do batch de importação
            external_id: ID externo (deve ser único dentro do batch)
            memo: Descrição da transação
            amount: Valor (usar Decimal para precisão)
            currency: Código ISO 4217 (ex: BRL, USD)
            occurred_at: Data/hora da transação
            payee: Beneficiário (opcional)
            metadata: Metadados adicionais (opcional)

        Returns:
            Nova instância em status IMPORTED

        Examples:
            >>> entry = StatementEntry.create(
            ...     batch_id=uuid4(),
            ...     external_id="row_001",
            ...     memo="Compra online",
            ...     amount=Decimal("-99.90"),
            ...     currency="BRL",
            ...     occurred_at=datetime(2025, 10, 12),
            ... )
            >>> entry.status
            <StatementStatus.IMPORTED: 'imported'>
        """
        return cls(
            id=uuid4(),
            batch_id=batch_id,
            external_id=external_id,
            memo=memo,
            amount=amount,
            currency=currency.upper(),
            occurred_at=occurred_at,
            status=StatementStatus.IMPORTED,
            payee=payee,
            metadata=metadata or {},
        )

    def mark_matched(self, existing_transaction_id: UUID) -> None:
        """
        Marca entry como reconciliado com transação existente.

        Args:
            existing_transaction_id: UUID da transação com qual foi reconciliado

        Raises:
            ValueError: Se status não for IMPORTED

        Examples:
            >>> entry = StatementEntry.create(...)
            >>> txn_id = uuid4()
            >>> entry.mark_matched(txn_id)
            >>> entry.status
            <StatementStatus.MATCHED: 'matched'>
            >>> entry.transaction_id == txn_id
            True
        """
        if self.status != StatementStatus.IMPORTED:
            raise ValueError(
                f"Cannot mark as matched: current status is {self.status.value}, "
                f"expected {StatementStatus.IMPORTED.value}"
            )

        self.status = StatementStatus.MATCHED
        self.transaction_id = existing_transaction_id
        self.updated_at = datetime.utcnow()

    def mark_posted(self, transaction_id: UUID) -> None:
        """
        Marca entry como postado (convertido em transação contábil).

        Args:
            transaction_id: UUID da transação criada

        Raises:
            ValueError: Se status não for IMPORTED

        Examples:
            >>> entry = StatementEntry.create(...)
            >>> txn_id = uuid4()
            >>> entry.mark_posted(txn_id)
            >>> entry.status
            <StatementStatus.POSTED: 'posted'>
            >>> entry.transaction_id == txn_id
            True
        """
        if self.status != StatementStatus.IMPORTED:
            raise ValueError(
                f"Cannot mark as posted: current status is {self.status.value}, "
                f"expected {StatementStatus.IMPORTED.value}"
            )

        self.status = StatementStatus.POSTED
        self.transaction_id = transaction_id
        self.updated_at = datetime.utcnow()

    def suggest_account(self, account_id: UUID) -> None:
        """
        Define conta sugerida por regras/ML.

        Args:
            account_id: UUID da conta sugerida

        Examples:
            >>> entry = StatementEntry.create(...)
            >>> account = uuid4()
            >>> entry.suggest_account(account)
            >>> entry.suggested_account_id == account
            True
        """
        self.suggested_account_id = account_id
        self.updated_at = datetime.utcnow()

    def is_imported(self) -> bool:
        """
        Verifica se entry ainda está importado (não processado).

        Returns:
            True se status == IMPORTED

        Examples:
            >>> entry = StatementEntry.create(...)
            >>> entry.is_imported()
            True
            >>> entry.mark_posted(uuid4())
            >>> entry.is_imported()
            False
        """
        return self.status == StatementStatus.IMPORTED

    def is_matched(self) -> bool:
        """
        Verifica se entry foi reconciliado com transação existente.

        Returns:
            True se status == MATCHED

        Examples:
            >>> entry = StatementEntry.create(...)
            >>> entry.is_matched()
            False
            >>> entry.mark_matched(uuid4())
            >>> entry.is_matched()
            True
        """
        return self.status == StatementStatus.MATCHED

    def is_posted(self) -> bool:
        """
        Verifica se entry foi convertido em transação contábil.

        Returns:
            True se status == POSTED

        Examples:
            >>> entry = StatementEntry.create(...)
            >>> entry.is_posted()
            False
            >>> entry.mark_posted(uuid4())
            >>> entry.is_posted()
            True
        """
        return self.status == StatementStatus.POSTED

    def is_debit(self) -> bool:
        """
        Verifica se é débito (saída de dinheiro).

        Returns:
            True se amount < 0
        """
        return self.amount < Decimal("0")

    def is_credit(self) -> bool:
        """
        Verifica se é crédito (entrada de dinheiro).

        Returns:
            True se amount > 0
        """
        return self.amount > Decimal("0")

    def add_metadata(self, key: str, value: any) -> None:
        """
        Adiciona metadado ao entry.

        Args:
            key: Chave do metadado
            value: Valor (deve ser JSON-serializável)

        Examples:
            >>> entry = StatementEntry.create(...)
            >>> entry.add_metadata("rule_id", "grocery_rule_001")
            >>> entry.metadata["rule_id"]
            'grocery_rule_001'
        """
        self.metadata[key] = value
        self.updated_at = datetime.utcnow()

    def get_metadata(self, key: str, default: any = None) -> any:
        """
        Retorna metadado do entry.

        Args:
            key: Chave do metadado
            default: Valor padrão se chave não existir

        Returns:
            Valor do metadado ou default

        Examples:
            >>> entry = StatementEntry.create(...)
            >>> entry.add_metadata("source", "mobile_app")
            >>> entry.get_metadata("source")
            'mobile_app'
            >>> entry.get_metadata("nonexistent", "N/A")
            'N/A'
        """
        return self.metadata.get(key, default)

    def _validate_currency(self) -> None:
        """
        Valida código de moeda.

        Raises:
            ValueError: Se currency não for 3 caracteres
        """
        if len(self.currency) != 3:
            raise ValueError(f"Currency must be 3-letter ISO 4217 code, got: {self.currency}")

    def _validate_amount(self) -> None:
        """
        Valida amount.

        Raises:
            ValueError: Se amount for zero
        """
        if self.amount == Decimal("0"):
            raise ValueError("Amount cannot be zero")

    def _validate_external_id(self) -> None:
        """
        Valida external_id.

        Raises:
            ValueError: Se external_id for vazio
        """
        if not self.external_id or not self.external_id.strip():
            raise ValueError("external_id cannot be empty")

    def __eq__(self, other: object) -> bool:
        """Igualdade baseada em ID (entity identity)."""
        if not isinstance(other, StatementEntry):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash baseado em ID (para usar em sets/dicts)."""
        return hash(self.id)

    def __str__(self) -> str:
        """
        Representação string legível.

        Returns:
            Formato: "status: amount currency - memo"

        Examples:
            >>> entry = StatementEntry.create(
            ...     batch_id=uuid4(),
            ...     external_id="001",
            ...     memo="MERCADO",
            ...     amount=Decimal("-100.00"),
            ...     currency="BRL",
            ...     occurred_at=datetime.now(),
            ... )
            >>> str(entry)
            'imported: -100.00 BRL - MERCADO'
        """
        payee_part = f" [{self.payee}]" if self.payee else ""
        return f"{self.status.value}: {self.amount} {self.currency} - {self.memo}{payee_part}"

    def __repr__(self) -> str:
        """Representação técnica para debug."""
        return (
            f"StatementEntry(id={self.id!r}, batch_id={self.batch_id!r}, "
            f"status={self.status!r}, amount={self.amount}, memo={self.memo!r})"
        )
