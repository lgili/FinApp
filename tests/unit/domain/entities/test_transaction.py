"""
Testes unitários para Transaction entity.

Testa criação, validação de balanceamento, postings e operações.
"""

from datetime import date
from uuid import uuid4

import pytest

from finlite.domain.entities.transaction import Transaction
from finlite.domain.value_objects.money import Money
from finlite.domain.value_objects.posting import Posting


class TestTransactionCreation:
    """Testes de criação de Transaction."""

    def test_create_simple_transaction(self):
        """Deve criar transação simples balanceada."""
        acc1 = uuid4()
        acc2 = uuid4()

        transaction = Transaction.create(
            date=date(2025, 10, 1),
            description="Test transaction",
            postings=[
                Posting(acc1, Money.from_float(100.0, "BRL")),
                Posting(acc2, Money.from_float(-100.0, "BRL"))
            ]
        )

        assert transaction.date == date(2025, 10, 1)
        assert transaction.description == "Test transaction"
        assert len(transaction.postings) == 2
        assert transaction.is_balanced()

    def test_create_with_multiple_postings(self):
        """Deve criar transação com múltiplos postings."""
        acc1 = uuid4()
        acc2 = uuid4()
        acc3 = uuid4()

        transaction = Transaction.create(
            date=date(2025, 10, 1),
            description="Split transaction",
            postings=[
                Posting(acc1, Money.from_float(-100.0, "BRL")),
                Posting(acc2, Money.from_float(60.0, "BRL")),
                Posting(acc3, Money.from_float(40.0, "BRL"))
            ]
        )

        assert len(transaction.postings) == 3
        assert transaction.is_balanced()

    def test_create_with_tags(self):
        """Deve criar transação com tags."""
        acc1 = uuid4()
        acc2 = uuid4()

        transaction = Transaction.create(
            date=date(2025, 10, 1),
            description="Monthly rent",
            postings=[
                Posting(acc1, Money.from_float(1000.0, "BRL")),
                Posting(acc2, Money.from_float(-1000.0, "BRL"))
            ],
            tags=["rent", "fixed", "monthly"]
        )

        assert len(transaction.tags) == 3
        assert "rent" in transaction.tags

    def test_create_with_notes(self):
        """Deve criar transação com notas."""
        acc1 = uuid4()
        acc2 = uuid4()

        transaction = Transaction.create(
            date=date(2025, 10, 1),
            description="Payment",
            postings=[
                Posting(acc1, Money.from_float(100.0, "BRL")),
                Posting(acc2, Money.from_float(-100.0, "BRL"))
            ],
            notes="Additional details here"
        )

        assert transaction.notes == "Additional details here"

    def test_postings_are_immutable(self):
        """Deve garantir que postings sejam imutáveis (tuple)."""
        acc1 = uuid4()
        acc2 = uuid4()

        transaction = Transaction.create(
            date=date(2025, 10, 1),
            description="Test",
            postings=[
                Posting(acc1, Money.from_float(100.0, "BRL")),
                Posting(acc2, Money.from_float(-100.0, "BRL"))
            ]
        )

        assert isinstance(transaction.postings, tuple)

        # Não pode modificar
        with pytest.raises((AttributeError, TypeError)):
            transaction.postings[0] = Posting(uuid4(), Money.from_float(50.0, "BRL"))  # type: ignore

    def test_tags_are_immutable(self):
        """Deve garantir que tags sejam imutáveis (tuple)."""
        acc1 = uuid4()
        acc2 = uuid4()

        transaction = Transaction.create(
            date=date(2025, 10, 1),
            description="Test",
            postings=[
                Posting(acc1, Money.from_float(100.0, "BRL")),
                Posting(acc2, Money.from_float(-100.0, "BRL"))
            ],
            tags=["tag1", "tag2"]
        )

        assert isinstance(transaction.tags, tuple)


class TestTransactionValidation:
    """Testes de validação."""

    def test_description_cannot_be_empty(self):
        """Deve rejeitar descrição vazia."""
        acc1 = uuid4()
        acc2 = uuid4()

        with pytest.raises(ValueError, match="cannot be empty"):
            Transaction.create(
                date=date(2025, 10, 1),
                description="",
                postings=[
                    Posting(acc1, Money.from_float(100.0, "BRL")),
                    Posting(acc2, Money.from_float(-100.0, "BRL"))
                ]
            )

    def test_must_have_at_least_two_postings(self):
        """Deve rejeitar transação com menos de 2 postings."""
        acc1 = uuid4()

        with pytest.raises(ValueError, match="at least 2 postings"):
            Transaction.create(
                date=date(2025, 10, 1),
                description="Invalid",
                postings=[
                    Posting(acc1, Money.from_float(100.0, "BRL"))
                ]
            )

    def test_postings_must_balance(self):
        """Deve rejeitar postings desbalanceados."""
        acc1 = uuid4()
        acc2 = uuid4()

        with pytest.raises(ValueError, match="do not balance"):
            Transaction.create(
                date=date(2025, 10, 1),
                description="Unbalanced",
                postings=[
                    Posting(acc1, Money.from_float(100.0, "BRL")),
                    Posting(acc2, Money.from_float(-50.0, "BRL"))  # Não balanceia!
                ]
            )

    def test_all_postings_must_have_same_currency(self):
        """Deve rejeitar postings com moedas diferentes."""
        acc1 = uuid4()
        acc2 = uuid4()

        with pytest.raises(ValueError, match="same currency"):
            Transaction.create(
                date=date(2025, 10, 1),
                description="Mixed currencies",
                postings=[
                    Posting(acc1, Money.from_float(100.0, "BRL")),
                    Posting(acc2, Money.from_float(-100.0, "USD"))  # Moeda diferente!
                ]
            )


class TestTransactionBalanceChecks:
    """Testes de verificação de balanceamento."""

    def test_is_balanced_true(self):
        """Deve identificar transação balanceada."""
        acc1 = uuid4()
        acc2 = uuid4()

        transaction = Transaction.create(
            date=date(2025, 10, 1),
            description="Balanced",
            postings=[
                Posting(acc1, Money.from_float(100.0, "BRL")),
                Posting(acc2, Money.from_float(-100.0, "BRL"))
            ]
        )

        assert transaction.is_balanced() is True

    def test_get_total_debits(self):
        """Deve calcular total de débitos."""
        acc1 = uuid4()
        acc2 = uuid4()
        acc3 = uuid4()

        transaction = Transaction.create(
            date=date(2025, 10, 1),
            description="Multiple debits",
            postings=[
                Posting(acc1, Money.from_float(100.0, "BRL")),   # débito
                Posting(acc2, Money.from_float(50.0, "BRL")),    # débito
                Posting(acc3, Money.from_float(-150.0, "BRL"))   # crédito
            ]
        )

        total = transaction.get_total_debits()

        assert total == Money.from_float(150.0, "BRL")

    def test_get_total_credits(self):
        """Deve calcular total de créditos."""
        acc1 = uuid4()
        acc2 = uuid4()
        acc3 = uuid4()

        transaction = Transaction.create(
            date=date(2025, 10, 1),
            description="Multiple credits",
            postings=[
                Posting(acc1, Money.from_float(150.0, "BRL")),   # débito
                Posting(acc2, Money.from_float(-100.0, "BRL")),  # crédito
                Posting(acc3, Money.from_float(-50.0, "BRL"))    # crédito
            ]
        )

        total = transaction.get_total_credits()

        assert total == Money.from_float(150.0, "BRL")  # Valor absoluto

    def test_get_currency(self):
        """Deve retornar moeda dos postings."""
        acc1 = uuid4()
        acc2 = uuid4()

        transaction = Transaction.create(
            date=date(2025, 10, 1),
            description="Test",
            postings=[
                Posting(acc1, Money.from_float(100.0, "USD")),
                Posting(acc2, Money.from_float(-100.0, "USD"))
            ]
        )

        assert transaction.get_currency() == "USD"


class TestTransactionPostingQueries:
    """Testes de consulta de postings."""

    def test_get_postings_for_account(self):
        """Deve buscar postings por conta."""
        acc1 = uuid4()
        acc2 = uuid4()

        transaction = Transaction.create(
            date=date(2025, 10, 1),
            description="Test",
            postings=[
                Posting(acc1, Money.from_float(100.0, "BRL")),
                Posting(acc2, Money.from_float(-100.0, "BRL"))
            ]
        )

        postings = transaction.get_postings_for_account(acc1)

        assert len(postings) == 1
        assert postings[0].account_id == acc1
        assert postings[0].amount == Money.from_float(100.0, "BRL")

    def test_get_postings_for_account_not_found(self):
        """Deve retornar lista vazia se conta não existe."""
        acc1 = uuid4()
        acc2 = uuid4()
        acc3 = uuid4()

        transaction = Transaction.create(
            date=date(2025, 10, 1),
            description="Test",
            postings=[
                Posting(acc1, Money.from_float(100.0, "BRL")),
                Posting(acc2, Money.from_float(-100.0, "BRL"))
            ]
        )

        postings = transaction.get_postings_for_account(acc3)

        assert len(postings) == 0

    def test_has_account(self):
        """Deve verificar se transação afeta conta."""
        acc1 = uuid4()
        acc2 = uuid4()
        acc3 = uuid4()

        transaction = Transaction.create(
            date=date(2025, 10, 1),
            description="Test",
            postings=[
                Posting(acc1, Money.from_float(100.0, "BRL")),
                Posting(acc2, Money.from_float(-100.0, "BRL"))
            ]
        )

        assert transaction.has_account(acc1) is True
        assert transaction.has_account(acc2) is True
        assert transaction.has_account(acc3) is False


class TestTransactionTags:
    """Testes de manipulação de tags."""

    def test_has_tag(self):
        """Deve verificar se tem tag."""
        acc1 = uuid4()
        acc2 = uuid4()

        transaction = Transaction.create(
            date=date(2025, 10, 1),
            description="Test",
            postings=[
                Posting(acc1, Money.from_float(100.0, "BRL")),
                Posting(acc2, Money.from_float(-100.0, "BRL"))
            ],
            tags=["food", "restaurant"]
        )

        assert transaction.has_tag("food") is True
        assert transaction.has_tag("transport") is False


class TestTransactionEquality:
    """Testes de igualdade (entity identity)."""

    def test_same_id_equals(self):
        """Deve considerar iguais se mesmo ID."""
        acc1 = uuid4()
        acc2 = uuid4()

        transaction = Transaction.create(
            date=date(2025, 10, 1),
            description="Test",
            postings=[
                Posting(acc1, Money.from_float(100.0, "BRL")),
                Posting(acc2, Money.from_float(-100.0, "BRL"))
            ]
        )

        assert transaction == transaction

    def test_different_id_not_equals(self):
        """Deve considerar diferentes se IDs diferentes."""
        acc1 = uuid4()
        acc2 = uuid4()

        tx1 = Transaction.create(
            date=date(2025, 10, 1),
            description="Test",
            postings=[
                Posting(acc1, Money.from_float(100.0, "BRL")),
                Posting(acc2, Money.from_float(-100.0, "BRL"))
            ]
        )

        tx2 = Transaction.create(
            date=date(2025, 10, 1),
            description="Test",
            postings=[
                Posting(acc1, Money.from_float(100.0, "BRL")),
                Posting(acc2, Money.from_float(-100.0, "BRL"))
            ]
        )

        assert tx1 != tx2  # IDs diferentes


class TestTransactionStringRepresentation:
    """Testes de representação string."""

    def test_str_representation(self):
        """Deve formatar string legível."""
        acc1 = uuid4()
        acc2 = uuid4()

        transaction = Transaction.create(
            date=date(2025, 10, 1),
            description="Grocery shopping",
            postings=[
                Posting(acc1, Money.from_float(100.0, "BRL")),
                Posting(acc2, Money.from_float(-100.0, "BRL"))
            ]
        )

        result = str(transaction)

        assert "2025-10-01" in result
        assert "Grocery shopping" in result
        assert "2 postings" in result

    def test_repr_contains_key_info(self):
        """Deve incluir informações-chave no repr."""
        acc1 = uuid4()
        acc2 = uuid4()

        transaction = Transaction.create(
            date=date(2025, 10, 1),
            description="Test",
            postings=[
                Posting(acc1, Money.from_float(100.0, "BRL")),
                Posting(acc2, Money.from_float(-100.0, "BRL"))
            ]
        )

        result = repr(transaction)

        assert "Transaction(" in result
        assert "Test" in result
