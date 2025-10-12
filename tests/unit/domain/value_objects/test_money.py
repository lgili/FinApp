"""
Testes unitários para Money value object.

Testa todas as operações, validações e edge cases do Money.
"""

from decimal import Decimal

import pytest

from finlite.domain.value_objects.money import Money


class TestMoneyCreation:
    """Testes de criação de Money."""

    def test_create_with_decimal(self):
        """Deve criar Money com Decimal."""
        money = Money(amount=Decimal("100.50"), currency="BRL")

        assert money.amount == Decimal("100.50")
        assert money.currency == "BRL"

    def test_create_from_float(self):
        """Deve criar Money a partir de float."""
        money = Money.from_float(100.50, "USD")

        assert money.amount == Decimal("100.50")
        assert money.currency == "USD"

    def test_create_from_int(self):
        """Deve criar Money a partir de centavos."""
        money = Money.from_int(10050, "BRL")  # 10050 centavos = R$ 100.50

        assert money.amount == Decimal("100.50")
        assert money.currency == "BRL"

    def test_create_zero(self):
        """Deve criar Money com valor zero."""
        money = Money.zero("EUR")

        assert money.amount == Decimal("0")
        assert money.currency == "EUR"
        assert money.is_zero()

    def test_currency_must_be_3_uppercase_letters(self):
        """Deve validar formato ISO 4217 da moeda."""
        # Válido
        Money(Decimal("100"), "BRL")
        Money(Decimal("100"), "USD")
        Money(Decimal("100"), "EUR")

        # Inválido - não são 3 letras
        with pytest.raises(ValueError, match="must be 3 uppercase letters"):
            Money(Decimal("100"), "BR")

        with pytest.raises(ValueError, match="must be 3 uppercase letters"):
            Money(Decimal("100"), "BRLL")

        # Inválido - não são maiúsculas
        with pytest.raises(ValueError, match="must be 3 uppercase letters"):
            Money(Decimal("100"), "brl")

        # Inválido - não é string
        with pytest.raises(TypeError, match="Currency must be str"):
            Money(Decimal("100"), 123)  # type: ignore

    def test_amount_converted_to_decimal(self):
        """Deve converter amount para Decimal automaticamente."""
        money = Money(amount=100, currency="BRL")  # type: ignore

        assert isinstance(money.amount, Decimal)
        assert money.amount == Decimal("100")


class TestMoneyArithmetic:
    """Testes de operações aritméticas."""

    def test_addition_same_currency(self):
        """Deve somar Money com mesma moeda."""
        m1 = Money.from_float(100.0, "BRL")
        m2 = Money.from_float(50.0, "BRL")

        result = m1 + m2

        assert result.amount == Decimal("150.0")
        assert result.currency == "BRL"

    def test_addition_different_currencies_raises(self):
        """Deve lançar erro ao somar moedas diferentes."""
        brl = Money.from_float(100.0, "BRL")
        usd = Money.from_float(50.0, "USD")

        with pytest.raises(ValueError, match="Cannot operate on different currencies"):
            brl + usd

    def test_subtraction_same_currency(self):
        """Deve subtrair Money com mesma moeda."""
        m1 = Money.from_float(100.0, "BRL")
        m2 = Money.from_float(30.0, "BRL")

        result = m1 - m2

        assert result.amount == Decimal("70.0")
        assert result.currency == "BRL"

    def test_multiplication_by_int(self):
        """Deve multiplicar Money por int."""
        money = Money.from_float(100.0, "BRL")

        result = money * 3

        assert result.amount == Decimal("300.0")
        assert result.currency == "BRL"

    def test_multiplication_by_float(self):
        """Deve multiplicar Money por float."""
        money = Money.from_float(100.0, "BRL")

        result = money * 1.5

        assert result.amount == Decimal("150.0")
        assert result.currency == "BRL"

    def test_reverse_multiplication(self):
        """Deve permitir multiplicação reversa: 2 * Money."""
        money = Money.from_float(100.0, "BRL")

        result = 2 * money

        assert result.amount == Decimal("200.0")
        assert result.currency == "BRL"

    def test_division_by_int(self):
        """Deve dividir Money por int."""
        money = Money.from_float(100.0, "BRL")

        result = money / 2

        assert result.amount == Decimal("50.0")
        assert result.currency == "BRL"

    def test_division_by_zero_raises(self):
        """Deve lançar erro ao dividir por zero."""
        money = Money.from_float(100.0, "BRL")

        with pytest.raises(ZeroDivisionError):
            money / 0

    def test_negation(self):
        """Deve inverter sinal."""
        money = Money.from_float(100.0, "BRL")

        result = -money

        assert result.amount == Decimal("-100.0")
        assert result.currency == "BRL"

    def test_absolute_value(self):
        """Deve retornar valor absoluto."""
        money = Money.from_float(-100.0, "BRL")

        result = abs(money)

        assert result.amount == Decimal("100.0")
        assert result.currency == "BRL"


class TestMoneyComparison:
    """Testes de comparação."""

    def test_equality(self):
        """Deve comparar Money por igualdade."""
        m1 = Money.from_float(100.0, "BRL")
        m2 = Money.from_float(100.0, "BRL")

        assert m1 == m2

    def test_inequality(self):
        """Deve detectar diferenças."""
        m1 = Money.from_float(100.0, "BRL")
        m2 = Money.from_float(50.0, "BRL")

        assert m1 != m2

    def test_less_than(self):
        """Deve comparar menor que."""
        m1 = Money.from_float(50.0, "BRL")
        m2 = Money.from_float(100.0, "BRL")

        assert m1 < m2
        assert not m2 < m1

    def test_less_than_or_equal(self):
        """Deve comparar menor ou igual."""
        m1 = Money.from_float(50.0, "BRL")
        m2 = Money.from_float(100.0, "BRL")
        m3 = Money.from_float(100.0, "BRL")

        assert m1 <= m2
        assert m2 <= m3

    def test_greater_than(self):
        """Deve comparar maior que."""
        m1 = Money.from_float(100.0, "BRL")
        m2 = Money.from_float(50.0, "BRL")

        assert m1 > m2
        assert not m2 > m1

    def test_greater_than_or_equal(self):
        """Deve comparar maior ou igual."""
        m1 = Money.from_float(100.0, "BRL")
        m2 = Money.from_float(50.0, "BRL")
        m3 = Money.from_float(100.0, "BRL")

        assert m1 >= m2
        assert m1 >= m3

    def test_comparison_different_currencies_raises(self):
        """Deve lançar erro ao comparar moedas diferentes."""
        brl = Money.from_float(100.0, "BRL")
        usd = Money.from_float(100.0, "USD")

        with pytest.raises(ValueError, match="Cannot operate on different currencies"):
            brl < usd


class TestMoneyPredicates:
    """Testes de métodos booleanos."""

    def test_is_positive(self):
        """Deve identificar valores positivos."""
        positive = Money.from_float(100.0, "BRL")
        negative = Money.from_float(-100.0, "BRL")
        zero = Money.zero("BRL")

        assert positive.is_positive()
        assert not negative.is_positive()
        assert not zero.is_positive()

    def test_is_negative(self):
        """Deve identificar valores negativos."""
        positive = Money.from_float(100.0, "BRL")
        negative = Money.from_float(-100.0, "BRL")
        zero = Money.zero("BRL")

        assert negative.is_negative()
        assert not positive.is_negative()
        assert not zero.is_negative()

    def test_is_zero(self):
        """Deve identificar zero."""
        zero = Money.zero("BRL")
        non_zero = Money.from_float(0.01, "BRL")

        assert zero.is_zero()
        assert not non_zero.is_zero()


class TestMoneyFormatting:
    """Testes de conversão e formatação."""

    def test_round(self):
        """Deve arredondar para N casas decimais."""
        money = Money.from_float(100.126, "BRL")

        rounded = money.round(2)

        assert rounded.amount == Decimal("100.13")

    def test_to_float(self):
        """Deve converter para float."""
        money = Money.from_float(100.50, "BRL")

        assert money.to_float() == 100.50

    def test_to_cents(self):
        """Deve converter para centavos."""
        money = Money.from_float(100.50, "BRL")

        assert money.to_cents() == 10050

    def test_str_representation(self):
        """Deve formatar string legível."""
        money = Money.from_float(100.50, "BRL")

        assert str(money) == "BRL 100.50"

    def test_repr_representation(self):
        """Deve formatar string técnica."""
        money = Money.from_float(100.50, "BRL")

        # Decimal normaliza 100.50 para 100.5
        assert repr(money) == "Money(amount=Decimal('100.5'), currency='BRL')"


class TestMoneyImmutability:
    """Testes de imutabilidade."""

    def test_cannot_modify_amount(self):
        """Deve impedir modificação de amount."""
        money = Money.from_float(100.0, "BRL")

        with pytest.raises(AttributeError):
            money.amount = Decimal("200.0")  # type: ignore

    def test_cannot_modify_currency(self):
        """Deve impedir modificação de currency."""
        money = Money.from_float(100.0, "BRL")

        with pytest.raises(AttributeError):
            money.currency = "USD"  # type: ignore

    def test_operations_return_new_instance(self):
        """Deve retornar nova instância em operações."""
        original = Money.from_float(100.0, "BRL")

        result = original + Money.from_float(50.0, "BRL")

        assert original.amount == Decimal("100.0")  # Original não mudou
        assert result.amount == Decimal("150.0")  # Novo objeto


class TestMoneyEdgeCases:
    """Testes de casos extremos."""

    def test_very_large_values(self):
        """Deve lidar com valores muito grandes."""
        large = Money(Decimal("999999999999.99"), "BRL")

        assert large.amount == Decimal("999999999999.99")

    def test_very_small_values(self):
        """Deve lidar com valores muito pequenos."""
        small = Money(Decimal("0.01"), "BRL")

        assert small.amount == Decimal("0.01")

    def test_precision_preserved_in_calculations(self):
        """Deve preservar precisão em cálculos."""
        m1 = Money(Decimal("10.01"), "BRL")
        m2 = Money(Decimal("20.02"), "BRL")

        result = m1 + m2

        assert result.amount == Decimal("30.03")

    def test_negative_zero_normalized(self):
        """Deve normalizar -0 para 0."""
        positive = Money.from_float(100.0, "BRL")
        negative = Money.from_float(-100.0, "BRL")

        result = positive + negative

        assert result.is_zero()
        assert result.amount == Decimal("0")
