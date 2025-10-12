"""
Posting Value Object - Representa um lançamento contábil individual.

Um posting é uma das "pernas" de uma transação de partida dobrada.
Cada transação tem 2+ postings que devem balancear (soma zero).

Exemplo:
    Transação: "Receber salário R$ 5000"
    Postings:
        1. Assets:Checking    +5000 BRL  (débito em ativo)
        2. Income:Salary      -5000 BRL  (crédito em receita)
    Soma: +5000 - 5000 = 0 ✓ (balanceado)

Referência: Double-Entry Bookkeeping
    https://en.wikipedia.org/wiki/Double-entry_bookkeeping
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from finlite.domain.value_objects.money import Money


@dataclass(frozen=True)
class Posting:
    """
    Value Object imutável para um lançamento contábil.

    Representa uma única "perna" de uma transação. Em contabilidade
    de partida dobrada, toda transação tem pelo menos 2 postings
    (débito e crédito) que devem balancear.

    Attributes:
        account_id: UUID da conta afetada
        amount: Valor monetário (positivo = débito, negativo = crédito)
        notes: Notas adicionais opcionais (ex: memo, categoria)

    Examples:
        >>> from uuid import uuid4
        >>> checking_id = uuid4()
        >>> salary_id = uuid4()

        >>> # Posting de débito (+5000 na conta corrente)
        >>> debit = Posting(
        ...     account_id=checking_id,
        ...     amount=Money.from_float(5000.0, "BRL"),
        ...     notes="Salário de outubro"
        ... )

        >>> # Posting de crédito (-5000 na receita)
        >>> credit = Posting(
        ...     account_id=salary_id,
        ...     amount=Money.from_float(-5000.0, "BRL"),
        ...     notes="Salário de outubro"
        ... )

        >>> debit.is_debit()
        True
        >>> credit.is_credit()
        True
    """

    account_id: UUID
    amount: Money
    notes: Optional[str] = None

    def __post_init__(self) -> None:
        """Validações após inicialização."""
        if not isinstance(self.account_id, UUID):
            raise TypeError(f"account_id must be UUID, got {type(self.account_id)}")

        if not isinstance(self.amount, Money):
            raise TypeError(f"amount must be Money, got {type(self.amount)}")

        if self.amount.is_zero():
            raise ValueError("Posting amount cannot be zero")

        if self.notes is not None:
            if not isinstance(self.notes, str):
                raise TypeError(f"notes must be str or None, got {type(self.notes)}")

            # Remove espaços em branco extras
            object.__setattr__(self, "notes", self.notes.strip() or None)

    def is_debit(self) -> bool:
        """
        Verifica se é um lançamento de débito (valor positivo).

        Returns:
            True se amount > 0

        Examples:
            >>> posting = Posting(
            ...     account_id=uuid4(),
            ...     amount=Money.from_float(100.0, "BRL")
            ... )
            >>> posting.is_debit()
            True
        """
        return self.amount.is_positive()

    def is_credit(self) -> bool:
        """
        Verifica se é um lançamento de crédito (valor negativo).

        Returns:
            True se amount < 0

        Examples:
            >>> posting = Posting(
            ...     account_id=uuid4(),
            ...     amount=Money.from_float(-100.0, "BRL")
            ... )
            >>> posting.is_credit()
            True
        """
        return self.amount.is_negative()

    def invert(self) -> Posting:
        """
        Cria posting invertido (débito vira crédito e vice-versa).

        Útil para estornos/reversões de transações.

        Returns:
            Novo Posting com amount negado

        Examples:
            >>> original = Posting(
            ...     account_id=uuid4(),
            ...     amount=Money.from_float(100.0, "BRL"),
            ...     notes="Compra"
            ... )
            >>> reversed_posting = original.invert()
            >>> reversed_posting.amount
            Money(amount=Decimal('-100.0'), currency='BRL')
        """
        return Posting(
            account_id=self.account_id,
            amount=-self.amount,
            notes=f"[REVERSED] {self.notes}" if self.notes else None,
        )

    def with_notes(self, notes: Optional[str]) -> Posting:
        """
        Cria novo Posting com notes diferentes.

        Args:
            notes: Novas notas (ou None para remover)

        Returns:
            Novo Posting com notes atualizadas

        Examples:
            >>> posting = Posting(
            ...     account_id=uuid4(),
            ...     amount=Money.from_float(100.0, "BRL")
            ... )
            >>> with_notes = posting.with_notes("Compra no mercado")
            >>> with_notes.notes
            'Compra no mercado'
        """
        return Posting(
            account_id=self.account_id, amount=self.amount, notes=notes
        )

    def __str__(self) -> str:
        """
        Representação string legível.

        Returns:
            Formato: "account_id: +BRL 100.00 [notes]"

        Examples:
            >>> posting = Posting(
            ...     account_id=UUID("12345678-1234-5678-1234-567812345678"),
            ...     amount=Money.from_float(100.0, "BRL"),
            ...     notes="Test"
            ... )
            >>> str(posting)
            '12345678-1234-5678-1234-567812345678: BRL 100.00 [Test]'
        """
        base = f"{self.account_id}: {self.amount}"
        if self.notes:
            return f"{base} [{self.notes}]"
        return base

    def __repr__(self) -> str:
        """Representação técnica para debug."""
        return (
            f"Posting(account_id={self.account_id!r}, "
            f"amount={self.amount!r}, notes={self.notes!r})"
        )


def validate_postings_balance(postings: list[Posting]) -> None:
    """
    Valida que conjunto de postings está balanceado (soma zero).

    Em contabilidade de partida dobrada, toda transação deve ter
    postings que somem zero (débitos = créditos).

    Args:
        postings: Lista de postings para validar

    Raises:
        ValueError: Se postings não balancearem
        ValueError: Se postings tiverem moedas diferentes
        ValueError: Se houver menos de 2 postings

    Examples:
        >>> from uuid import uuid4
        >>> acc1, acc2 = uuid4(), uuid4()

        >>> # Balanceado ✓
        >>> postings = [
        ...     Posting(acc1, Money.from_float(100.0, "BRL")),
        ...     Posting(acc2, Money.from_float(-100.0, "BRL"))
        ... ]
        >>> validate_postings_balance(postings)  # OK

        >>> # Desbalanceado ✗
        >>> bad_postings = [
        ...     Posting(acc1, Money.from_float(100.0, "BRL")),
        ...     Posting(acc2, Money.from_float(-50.0, "BRL"))
        ... ]
        >>> validate_postings_balance(bad_postings)
        ValueError: Postings do not balance: total is BRL 50.00 (expected 0)
    """
    if len(postings) < 2:
        raise ValueError(
            f"Transaction must have at least 2 postings, got {len(postings)}"
        )

    # Verifica que todas as moedas são iguais
    currencies = {p.amount.currency for p in postings}
    if len(currencies) > 1:
        raise ValueError(
            f"All postings must have the same currency, got: {currencies}"
        )

    # Calcula soma total
    currency = postings[0].amount.currency
    total = Money.zero(currency)

    for posting in postings:
        total = total + posting.amount

    # Valida balanceamento (deve ser zero)
    if not total.is_zero():
        raise ValueError(
            f"Postings do not balance: total is {total} (expected 0)"
        )
