"""
Transaction Entity - Representa uma transação contábil.

Em contabilidade de partida dobrada, uma transação é um conjunto
de lançamentos (postings) que devem balancear (soma zero).

Exemplo:
    Transação: "Receber salário R$ 5000"
    Data: 2025-10-01
    Postings:
        1. Assets:Checking    +5000 BRL  (débito)
        2. Income:Salary      -5000 BRL  (crédito)
    Soma: 0 ✓ (balanceado)

Referências:
- Double-Entry Bookkeeping: https://en.wikipedia.org/wiki/Double-entry_bookkeeping
- Domain-Driven Design: Aggregate Root
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional
from uuid import UUID, uuid4

from finlite.domain.value_objects.money import Money
from finlite.domain.value_objects.posting import Posting, validate_postings_balance


@dataclass
class Transaction:
    """
    Entity representando uma transação contábil (Aggregate Root).

    Uma transação é o aggregate root que contém postings.
    Postings não existem fora de uma transação.

    Invariantes:
    - Postings devem balancear (soma = 0)
    - Deve ter pelo menos 2 postings
    - Todos os postings devem ter a mesma moeda
    - Postings são imutáveis após criação da transação

    Attributes:
        id: Identificador único (UUID)
        date: Data da transação
        description: Descrição legível (ex: "Receber salário")
        postings: Lista de lançamentos contábeis (imutável)
        tags: Tags opcionais para categorização (ex: ["fixo", "mensal"])
        notes: Notas adicionais (memo)
        import_batch_id: UUID do lote de importação (se aplicável)
        created_at: Data de criação do registro
        updated_at: Data de última atualização

    Examples:
        >>> from uuid import uuid4
        >>> from datetime import date
        >>> 
        >>> checking_id = uuid4()
        >>> salary_id = uuid4()
        >>> 
        >>> # Criar transação de salário
        >>> transaction = Transaction.create(
        ...     date=date(2025, 10, 1),
        ...     description="Receber salário",
        ...     postings=[
        ...         Posting(checking_id, Money.from_float(5000.0, "BRL")),
        ...         Posting(salary_id, Money.from_float(-5000.0, "BRL"))
        ...     ]
        ... )
        >>> 
        >>> transaction.is_balanced()
        True
        >>> transaction.get_total_debits()
        Money(amount=Decimal('5000.0'), currency='BRL')
    """

    id: UUID
    date: date
    description: str
    postings: tuple[Posting, ...]  # Imutável (tuple, não list)
    tags: tuple[str, ...] = field(default_factory=tuple)
    notes: Optional[str] = None
    import_batch_id: Optional[UUID] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validações após inicialização."""
        self._validate_description()
        self._validate_postings()
        self._validate_tags()

        # Garante que postings é tuple (imutável)
        if not isinstance(self.postings, tuple):
            object.__setattr__(self, "postings", tuple(self.postings))

        # Garante que tags é tuple
        if not isinstance(self.tags, tuple):
            object.__setattr__(self, "tags", tuple(self.tags))

    @classmethod
    def create(
        cls,
        date: date,
        description: str,
        postings: list[Posting],
        tags: Optional[list[str]] = None,
        notes: Optional[str] = None,
        import_batch_id: Optional[UUID] = None,
    ) -> Transaction:
        """
        Factory method para criar nova transação.

        Args:
            date: Data da transação
            description: Descrição legível
            postings: Lista de lançamentos (deve balancear)
            tags: Tags opcionais para categorização
            notes: Notas adicionais
            import_batch_id: UUID do lote de importação (opcional)

        Returns:
            Nova instância de Transaction

        Raises:
            ValueError: Se postings não balancearem
            ValueError: Se tiver menos de 2 postings
            ValueError: Se postings tiverem moedas diferentes

        Examples:
            >>> from uuid import uuid4
            >>> from datetime import date
            >>> 
            >>> acc1, acc2 = uuid4(), uuid4()
            >>> transaction = Transaction.create(
            ...     date=date(2025, 10, 1),
            ...     description="Compra no mercado",
            ...     postings=[
            ...         Posting(acc1, Money.from_float(-100.0, "BRL")),
            ...         Posting(acc2, Money.from_float(100.0, "BRL"))
            ...     ],
            ...     tags=["food", "essential"]
            ... )
        """
        return cls(
            id=uuid4(),
            date=date,
            description=description,
            postings=tuple(postings),
            tags=tuple(tags or []),
            notes=notes,
            import_batch_id=import_batch_id,
        )

    def is_balanced(self) -> bool:
        """
        Verifica se transação está balanceada (postings somam zero).

        Returns:
            True se soma dos postings é zero

        Examples:
            >>> transaction = Transaction.create(
            ...     date=date.today(),
            ...     description="Test",
            ...     postings=[
            ...         Posting(uuid4(), Money.from_float(100.0, "BRL")),
            ...         Posting(uuid4(), Money.from_float(-100.0, "BRL"))
            ...     ]
            ... )
            >>> transaction.is_balanced()
            True
        """
        try:
            validate_postings_balance(list(self.postings))
            return True
        except ValueError:
            return False

    def get_currency(self) -> str:
        """
        Retorna moeda da transação.

        Todas as postings devem ter a mesma moeda.

        Returns:
            Código ISO 4217 da moeda

        Examples:
            >>> transaction = Transaction.create(
            ...     date=date.today(),
            ...     description="Test",
            ...     postings=[
            ...         Posting(uuid4(), Money.from_float(100.0, "BRL")),
            ...         Posting(uuid4(), Money.from_float(-100.0, "BRL"))
            ...     ]
            ... )
            >>> transaction.get_currency()
            'BRL'
        """
        return self.postings[0].amount.currency

    def get_total_debits(self) -> Money:
        """
        Calcula total de débitos (lançamentos positivos).

        Returns:
            Soma de todos os débitos

        Examples:
            >>> transaction = Transaction.create(
            ...     date=date.today(),
            ...     description="Test",
            ...     postings=[
            ...         Posting(uuid4(), Money.from_float(100.0, "BRL")),
            ...         Posting(uuid4(), Money.from_float(50.0, "BRL")),
            ...         Posting(uuid4(), Money.from_float(-150.0, "BRL"))
            ...     ]
            ... )
            >>> transaction.get_total_debits()
            Money(amount=Decimal('150.0'), currency='BRL')
        """
        currency = self.get_currency()
        total = Money.zero(currency)

        for posting in self.postings:
            if posting.is_debit():
                total = total + posting.amount

        return total

    def get_total_credits(self) -> Money:
        """
        Calcula total de créditos (lançamentos negativos, em valor absoluto).

        Returns:
            Soma absoluta de todos os créditos

        Examples:
            >>> transaction = Transaction.create(
            ...     date=date.today(),
            ...     description="Test",
            ...     postings=[
            ...         Posting(uuid4(), Money.from_float(150.0, "BRL")),
            ...         Posting(uuid4(), Money.from_float(-100.0, "BRL")),
            ...         Posting(uuid4(), Money.from_float(-50.0, "BRL"))
            ...     ]
            ... )
            >>> transaction.get_total_credits()
            Money(amount=Decimal('150.0'), currency='BRL')
        """
        currency = self.get_currency()
        total = Money.zero(currency)

        for posting in self.postings:
            if posting.is_credit():
                total = total + abs(posting.amount)

        return total

    def get_postings_for_account(self, account_id: UUID) -> list[Posting]:
        """
        Retorna postings de uma conta específica.

        Args:
            account_id: UUID da conta

        Returns:
            Lista de postings da conta (pode estar vazia)

        Examples:
            >>> account_id = uuid4()
            >>> transaction = Transaction.create(
            ...     date=date.today(),
            ...     description="Test",
            ...     postings=[
            ...         Posting(account_id, Money.from_float(100.0, "BRL")),
            ...         Posting(uuid4(), Money.from_float(-100.0, "BRL"))
            ...     ]
            ... )
            >>> postings = transaction.get_postings_for_account(account_id)
            >>> len(postings)
            1
        """
        return [p for p in self.postings if p.account_id == account_id]

    def has_account(self, account_id: UUID) -> bool:
        """
        Verifica se transação envolve determinada conta.

        Args:
            account_id: UUID da conta

        Returns:
            True se algum posting pertence à conta

        Examples:
            >>> account_id = uuid4()
            >>> transaction = Transaction.create(
            ...     date=date.today(),
            ...     description="Test",
            ...     postings=[
            ...         Posting(account_id, Money.from_float(100.0, "BRL")),
            ...         Posting(uuid4(), Money.from_float(-100.0, "BRL"))
            ...     ]
            ... )
            >>> transaction.has_account(account_id)
            True
        """
        return any(p.account_id == account_id for p in self.postings)

    def has_tag(self, tag: str) -> bool:
        """
        Verifica se transação tem determinada tag.

        Args:
            tag: Tag para procurar (case-insensitive)

        Returns:
            True se tag existe

        Examples:
            >>> transaction = Transaction.create(
            ...     date=date.today(),
            ...     description="Test",
            ...     postings=[
            ...         Posting(uuid4(), Money.from_float(100.0, "BRL")),
            ...         Posting(uuid4(), Money.from_float(-100.0, "BRL"))
            ...     ],
            ...     tags=["food", "Essential"]
            ... )
            >>> transaction.has_tag("food")
            True
            >>> transaction.has_tag("ESSENTIAL")
            True
        """
        return tag.lower() in [t.lower() for t in self.tags]

    def add_tag(self, tag: str) -> Transaction:
        """
        Cria nova transação com tag adicional.

        Transaction é imutável, então retorna nova instância.

        Args:
            tag: Tag para adicionar

        Returns:
            Nova Transaction com tag adicionada

        Examples:
            >>> transaction = Transaction.create(
            ...     date=date.today(),
            ...     description="Test",
            ...     postings=[
            ...         Posting(uuid4(), Money.from_float(100.0, "BRL")),
            ...         Posting(uuid4(), Money.from_float(-100.0, "BRL"))
            ...     ],
            ...     tags=["food"]
            ... )
            >>> new_tx = transaction.add_tag("essential")
            >>> new_tx.has_tag("essential")
            True
            >>> transaction.has_tag("essential")
            False  # Original não mudou
        """
        if self.has_tag(tag):
            return self  # Já tem, retorna mesma instância

        new_tags = list(self.tags) + [tag.strip()]
        return Transaction(
            id=self.id,
            date=self.date,
            description=self.description,
            postings=self.postings,
            tags=tuple(new_tags),
            notes=self.notes,
            import_batch_id=self.import_batch_id,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )

    def remove_tag(self, tag: str) -> Transaction:
        """
        Cria nova transação sem determinada tag.

        Args:
            tag: Tag para remover

        Returns:
            Nova Transaction sem a tag

        Examples:
            >>> transaction = Transaction.create(
            ...     date=date.today(),
            ...     description="Test",
            ...     postings=[
            ...         Posting(uuid4(), Money.from_float(100.0, "BRL")),
            ...         Posting(uuid4(), Money.from_float(-100.0, "BRL"))
            ...     ],
            ...     tags=["food", "essential"]
            ... )
            >>> new_tx = transaction.remove_tag("essential")
            >>> new_tx.has_tag("essential")
            False
        """
        if not self.has_tag(tag):
            return self  # Não tem, retorna mesma instância

        new_tags = [t for t in self.tags if t.lower() != tag.lower()]
        return Transaction(
            id=self.id,
            date=self.date,
            description=self.description,
            postings=self.postings,
            tags=tuple(new_tags),
            notes=self.notes,
            import_batch_id=self.import_batch_id,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )

    def is_from_import(self) -> bool:
        """
        Verifica se transação veio de importação.

        Returns:
            True se import_batch_id não é None

        Examples:
            >>> manual = Transaction.create(
            ...     date=date.today(),
            ...     description="Manual",
            ...     postings=[
            ...         Posting(uuid4(), Money.from_float(100.0, "BRL")),
            ...         Posting(uuid4(), Money.from_float(-100.0, "BRL"))
            ...     ]
            ... )
            >>> manual.is_from_import()
            False
            >>> 
            >>> imported = Transaction.create(
            ...     date=date.today(),
            ...     description="Imported",
            ...     postings=[
            ...         Posting(uuid4(), Money.from_float(100.0, "BRL")),
            ...         Posting(uuid4(), Money.from_float(-100.0, "BRL"))
            ...     ],
            ...     import_batch_id=uuid4()
            ... )
            >>> imported.is_from_import()
            True
        """
        return self.import_batch_id is not None

    def _validate_description(self) -> None:
        """
        Valida descrição da transação.

        Raises:
            ValueError: Se descrição for inválida
        """
        if not isinstance(self.description, str):
            raise TypeError(
                f"Transaction description must be str, got {type(self.description)}"
            )

        if not self.description.strip():
            raise ValueError("Transaction description cannot be empty")

    def _validate_postings(self) -> None:
        """
        Valida postings (balanceamento, quantidade, moedas).

        Raises:
            ValueError: Se postings forem inválidos
        """
        if not self.postings:
            raise ValueError("Transaction must have at least one posting")

        # Valida balanceamento (delega para função do Posting)
        validate_postings_balance(list(self.postings))

    def _validate_tags(self) -> None:
        """
        Valida tags.

        Raises:
            ValueError: Se tags forem inválidas
        """
        if not all(isinstance(t, str) and t.strip() for t in self.tags):
            raise ValueError("All tags must be non-empty strings")

    def __eq__(self, other: object) -> bool:
        """
        Igualdade baseada em ID (entity identity).

        Examples:
            >>> tx1 = Transaction.create(
            ...     date=date.today(),
            ...     description="Test",
            ...     postings=[
            ...         Posting(uuid4(), Money.from_float(100.0, "BRL")),
            ...         Posting(uuid4(), Money.from_float(-100.0, "BRL"))
            ...     ]
            ... )
            >>> tx2 = Transaction.create(
            ...     date=date.today(),
            ...     description="Test",
            ...     postings=[
            ...         Posting(uuid4(), Money.from_float(100.0, "BRL")),
            ...         Posting(uuid4(), Money.from_float(-100.0, "BRL"))
            ...     ]
            ... )
            >>> tx1 == tx2
            False  # IDs diferentes
        """
        if not isinstance(other, Transaction):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash baseado em ID (para usar em sets/dicts)."""
        return hash(self.id)

    def __str__(self) -> str:
        """
        Representação string legível.

        Returns:
            Formato: "YYYY-MM-DD: description (N postings)"

        Examples:
            >>> transaction = Transaction.create(
            ...     date=date(2025, 10, 1),
            ...     description="Receber salário",
            ...     postings=[
            ...         Posting(uuid4(), Money.from_float(5000.0, "BRL")),
            ...         Posting(uuid4(), Money.from_float(-5000.0, "BRL"))
            ...     ]
            ... )
            >>> str(transaction)
            '2025-10-01: Receber salário (2 postings)'
        """
        return f"{self.date}: {self.description} ({len(self.postings)} postings)"

    def __repr__(self) -> str:
        """Representação técnica para debug."""
        return (
            f"Transaction(id={self.id!r}, date={self.date!r}, "
            f"description={self.description!r}, postings={len(self.postings)} postings)"
        )
