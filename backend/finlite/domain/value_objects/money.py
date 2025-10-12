"""
Money Value Object - Representa valores monetários imutáveis.

Este value object implementa o padrão Money Pattern de Martin Fowler,
garantindo que valores monetários sejam sempre tratados com sua moeda
associada, evitando erros de conversão ou soma de moedas diferentes.

Referências:
- https://martinfowler.com/eaaCatalog/money.html
- Domain-Driven Design, Eric Evans
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Union


@dataclass(frozen=True)
class Money:
    """
    Value Object imutável para representar valores monetários.

    Attributes:
        amount: Valor numérico (usa Decimal para precisão)
        currency: Código ISO 4217 da moeda (ex: BRL, USD, EUR)

    Examples:
        >>> Money(Decimal("100.50"), "BRL")
        Money(amount=Decimal('100.50'), currency='BRL')

        >>> brl = Money.from_float(100.50, "BRL")
        >>> usd = Money.from_float(50.0, "USD")
        >>> brl + brl  # OK
        Money(amount=Decimal('201.00'), currency='BRL')
        >>> brl + usd  # Raises ValueError
        ValueError: Cannot operate on different currencies: BRL and USD
    """

    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        """Validações após inicialização."""
        # Garante que amount seja Decimal
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, "amount", Decimal(str(self.amount)))

        # Valida formato de moeda (ISO 4217 - 3 letras maiúsculas)
        if not isinstance(self.currency, str):
            raise TypeError(f"Currency must be str, got {type(self.currency)}")

        if len(self.currency) != 3 or not self.currency.isupper():
            raise ValueError(
                f"Currency must be 3 uppercase letters (ISO 4217), got '{self.currency}'"
            )

    @classmethod
    def from_float(cls, amount: float, currency: str) -> Money:
        """
        Cria Money a partir de float (converte para Decimal).

        Args:
            amount: Valor como float
            currency: Código ISO 4217 da moeda

        Returns:
            Instância de Money

        Examples:
            >>> Money.from_float(100.50, "BRL")
            Money(amount=Decimal('100.50'), currency='BRL')
        """
        return cls(amount=Decimal(str(amount)), currency=currency)

    @classmethod
    def from_int(cls, amount: int, currency: str) -> Money:
        """
        Cria Money a partir de int (útil para centavos).

        Args:
            amount: Valor em centavos (ex: 10050 = R$ 100.50)
            currency: Código ISO 4217 da moeda

        Returns:
            Instância de Money

        Examples:
            >>> Money.from_int(10050, "BRL")  # 10050 centavos = R$ 100.50
            Money(amount=Decimal('100.50'), currency='BRL')
        """
        return cls(amount=Decimal(amount) / 100, currency=currency)

    @classmethod
    def zero(cls, currency: str) -> Money:
        """
        Cria Money com valor zero.

        Args:
            currency: Código ISO 4217 da moeda

        Returns:
            Money com amount=0

        Examples:
            >>> Money.zero("BRL")
            Money(amount=Decimal('0'), currency='BRL')
        """
        return cls(amount=Decimal("0"), currency=currency)

    def __add__(self, other: Money) -> Money:
        """
        Soma dois valores Money (mesma moeda).

        Args:
            other: Outro Money para somar

        Returns:
            Novo Money com soma

        Raises:
            ValueError: Se moedas forem diferentes
            TypeError: Se other não for Money

        Examples:
            >>> Money.from_float(100.0, "BRL") + Money.from_float(50.0, "BRL")
            Money(amount=Decimal('150.0'), currency='BRL')
        """
        if not isinstance(other, Money):
            raise TypeError(f"Cannot add Money with {type(other)}")

        self._check_same_currency(other)
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def __sub__(self, other: Money) -> Money:
        """
        Subtrai dois valores Money (mesma moeda).

        Args:
            other: Outro Money para subtrair

        Returns:
            Novo Money com diferença

        Raises:
            ValueError: Se moedas forem diferentes
            TypeError: Se other não for Money
        """
        if not isinstance(other, Money):
            raise TypeError(f"Cannot subtract Money with {type(other)}")

        self._check_same_currency(other)
        return Money(amount=self.amount - other.amount, currency=self.currency)

    def __mul__(self, multiplier: Union[int, float, Decimal]) -> Money:
        """
        Multiplica Money por escalar.

        Args:
            multiplier: Número para multiplicar

        Returns:
            Novo Money com valor multiplicado

        Examples:
            >>> Money.from_float(100.0, "BRL") * 2
            Money(amount=Decimal('200.0'), currency='BRL')
        """
        if not isinstance(multiplier, (int, float, Decimal)):
            raise TypeError(f"Cannot multiply Money by {type(multiplier)}")

        return Money(
            amount=self.amount * Decimal(str(multiplier)), currency=self.currency
        )

    def __rmul__(self, multiplier: Union[int, float, Decimal]) -> Money:
        """Permite multiplicação reversa: 2 * Money(...)"""
        return self.__mul__(multiplier)

    def __truediv__(self, divisor: Union[int, float, Decimal]) -> Money:
        """
        Divide Money por escalar.

        Args:
            divisor: Número para dividir

        Returns:
            Novo Money com valor dividido

        Raises:
            ZeroDivisionError: Se divisor for zero

        Examples:
            >>> Money.from_float(100.0, "BRL") / 2
            Money(amount=Decimal('50.0'), currency='BRL')
        """
        if not isinstance(divisor, (int, float, Decimal)):
            raise TypeError(f"Cannot divide Money by {type(divisor)}")

        if divisor == 0:
            raise ZeroDivisionError("Cannot divide Money by zero")

        return Money(
            amount=self.amount / Decimal(str(divisor)), currency=self.currency
        )

    def __neg__(self) -> Money:
        """
        Inverte o sinal do valor.

        Returns:
            Novo Money com sinal invertido

        Examples:
            >>> -Money.from_float(100.0, "BRL")
            Money(amount=Decimal('-100.0'), currency='BRL')
        """
        return Money(amount=-self.amount, currency=self.currency)

    def __abs__(self) -> Money:
        """
        Retorna valor absoluto.

        Returns:
            Novo Money com valor absoluto

        Examples:
            >>> abs(Money.from_float(-100.0, "BRL"))
            Money(amount=Decimal('100.0'), currency='BRL')
        """
        return Money(amount=abs(self.amount), currency=self.currency)

    def __lt__(self, other: Money) -> bool:
        """Menor que (<)."""
        self._check_same_currency(other)
        return self.amount < other.amount

    def __le__(self, other: Money) -> bool:
        """Menor ou igual (<=)."""
        self._check_same_currency(other)
        return self.amount <= other.amount

    def __gt__(self, other: Money) -> bool:
        """Maior que (>)."""
        self._check_same_currency(other)
        return self.amount > other.amount

    def __ge__(self, other: Money) -> bool:
        """Maior ou igual (>=)."""
        self._check_same_currency(other)
        return self.amount >= other.amount

    def is_positive(self) -> bool:
        """Verifica se valor é positivo (> 0)."""
        return self.amount > 0

    def is_negative(self) -> bool:
        """Verifica se valor é negativo (< 0)."""
        return self.amount < 0

    def is_zero(self) -> bool:
        """Verifica se valor é zero."""
        return self.amount == 0

    def round(self, decimal_places: int = 2) -> Money:
        """
        Arredonda valor para N casas decimais.

        Args:
            decimal_places: Número de casas decimais (padrão: 2)

        Returns:
            Novo Money arredondado

        Examples:
            >>> Money.from_float(100.126, "BRL").round(2)
            Money(amount=Decimal('100.13'), currency='BRL')
        """
        return Money(
            amount=round(self.amount, decimal_places), currency=self.currency
        )

    def to_float(self) -> float:
        """
        Converte para float (pode perder precisão).

        Returns:
            Valor como float

        Warning:
            Use apenas para display. Para cálculos, use Decimal.
        """
        return float(self.amount)

    def to_cents(self) -> int:
        """
        Converte para centavos (int).

        Returns:
            Valor em centavos

        Examples:
            >>> Money.from_float(100.50, "BRL").to_cents()
            10050
        """
        return int(self.amount * 100)

    def _check_same_currency(self, other: Money) -> None:
        """
        Valida que duas instâncias têm a mesma moeda.

        Args:
            other: Outro Money para comparar

        Raises:
            ValueError: Se moedas forem diferentes
        """
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot operate on different currencies: {self.currency} and {other.currency}"
            )

    def __str__(self) -> str:
        """
        Representação string legível.

        Returns:
            Formato: "BRL 100.50"

        Examples:
            >>> str(Money.from_float(100.50, "BRL"))
            'BRL 100.50'
        """
        return f"{self.currency} {self.amount:.2f}"

    def __repr__(self) -> str:
        """Representação técnica para debug."""
        return f"Money(amount={self.amount!r}, currency={self.currency!r})"
