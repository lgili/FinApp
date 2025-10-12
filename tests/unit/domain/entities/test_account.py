"""
Testes unitários para Account entity.

Testa criação, validações, hierarquia e ciclo de vida.
"""

from datetime import datetime
from uuid import UUID, uuid4

import pytest

from finlite.domain.entities.account import Account
from finlite.domain.value_objects.account_type import AccountType


class TestAccountCreation:
    """Testes de criação de Account."""

    def test_create_account(self):
        """Deve criar conta com factory method."""
        account = Account.create(
            name="Assets:Checking",
            account_type=AccountType.ASSET,
            currency="BRL"
        )

        assert isinstance(account.id, UUID)
        assert account.name == "Assets:Checking"
        assert account.account_type == AccountType.ASSET
        assert account.currency == "BRL"
        assert account.parent_id is None
        assert account.is_active is True
        assert isinstance(account.created_at, datetime)
        assert isinstance(account.updated_at, datetime)

    def test_create_with_parent(self):
        """Deve criar conta com parent_id."""
        parent_id = uuid4()
        account = Account.create(
            name="Assets:Checking",
            account_type=AccountType.ASSET,
            currency="BRL",
            parent_id=parent_id
        )

        assert account.parent_id == parent_id

    def test_name_validation_empty(self):
        """Deve rejeitar nome vazio."""
        with pytest.raises(ValueError, match="cannot be empty"):
            Account.create("", AccountType.ASSET, "BRL")

        with pytest.raises(ValueError, match="cannot be empty"):
            Account.create("   ", AccountType.ASSET, "BRL")

    def test_name_validation_empty_component(self):
        """Deve rejeitar componente vazio no nome."""
        with pytest.raises(ValueError, match="empty component"):
            Account.create("Assets:", AccountType.ASSET, "BRL")

        with pytest.raises(ValueError, match="empty component"):
            Account.create("Assets::Checking", AccountType.ASSET, "BRL")

    def test_currency_validation(self):
        """Deve validar formato ISO 4217 da moeda."""
        # Válido
        Account.create("Assets:Checking", AccountType.ASSET, "BRL")
        Account.create("Assets:Checking", AccountType.ASSET, "USD")
        Account.create("Assets:Checking", AccountType.ASSET, "EUR")

        # Inválido
        with pytest.raises(ValueError, match="3 uppercase letters"):
            Account.create("Assets:Checking", AccountType.ASSET, "BR")

        with pytest.raises(ValueError, match="3 uppercase letters"):
            Account.create("Assets:Checking", AccountType.ASSET, "brl")


class TestAccountHierarchy:
    """Testes de hierarquia de contas."""

    def test_is_root(self):
        """Deve identificar conta raiz."""
        root = Account.create("Assets", AccountType.ASSET, "BRL")
        assert root.is_root()

        child = Account.create(
            "Assets:Checking",
            AccountType.ASSET,
            "BRL",
            parent_id=root.id
        )
        assert not child.is_root()

    def test_is_child_of(self):
        """Deve verificar relacionamento pai-filho."""
        parent = Account.create("Expenses", AccountType.EXPENSE, "BRL")
        child = Account.create(
            "Expenses:Food",
            AccountType.EXPENSE,
            "BRL",
            parent_id=parent.id
        )

        assert child.is_child_of(parent.id)
        assert not child.is_child_of(uuid4())

    def test_get_full_name_parts(self):
        """Deve dividir nome em partes."""
        account = Account.create(
            "Expenses:Food:Restaurant",
            AccountType.EXPENSE,
            "BRL"
        )

        parts = account.get_full_name_parts()
        assert parts == ["Expenses", "Food", "Restaurant"]

    def test_get_depth(self):
        """Deve calcular profundidade na hierarquia."""
        root = Account.create("Assets", AccountType.ASSET, "BRL")
        assert root.get_depth() == 1

        level2 = Account.create("Assets:Investments", AccountType.ASSET, "BRL")
        assert level2.get_depth() == 2

        level3 = Account.create("Assets:Investments:Stocks", AccountType.ASSET, "BRL")
        assert level3.get_depth() == 3

    def test_change_parent(self):
        """Deve permitir alterar conta pai."""
        account = Account.create("Expenses:Food", AccountType.EXPENSE, "BRL")
        assert account.parent_id is None

        new_parent_id = uuid4()
        account.change_parent(new_parent_id)

        assert account.parent_id == new_parent_id

    def test_change_parent_to_self_raises(self):
        """Deve impedir conta ser seu próprio pai."""
        account = Account.create("Assets", AccountType.ASSET, "BRL")

        with pytest.raises(ValueError, match="cannot be its own parent"):
            account.change_parent(account.id)


class TestAccountLifecycle:
    """Testes de ciclo de vida (ativar/desativar)."""

    def test_deactivate(self):
        """Deve desativar conta."""
        account = Account.create("Assets:Old", AccountType.ASSET, "BRL")
        assert account.is_active

        account.deactivate()

        assert not account.is_active

    def test_reactivate(self):
        """Deve reativar conta desativada."""
        account = Account.create("Assets:Temp", AccountType.ASSET, "BRL")
        account.deactivate()
        assert not account.is_active

        account.reactivate()

        assert account.is_active

    def test_rename(self):
        """Deve permitir renomear conta."""
        account = Account.create("Assets:Bank", AccountType.ASSET, "BRL")
        old_updated_at = account.updated_at

        account.rename("Assets:Checking")

        assert account.name == "Assets:Checking"
        assert account.updated_at > old_updated_at

    def test_rename_with_invalid_name_rollback(self):
        """Deve fazer rollback se novo nome for inválido."""
        account = Account.create("Assets:Bank", AccountType.ASSET, "BRL")
        original_name = account.name

        with pytest.raises(ValueError):
            account.rename("")  # Nome inválido

        # Nome deve permanecer o original
        assert account.name == original_name


class TestAccountEquality:
    """Testes de igualdade (entity identity)."""

    def test_equality_by_id(self):
        """Deve comparar por ID (entity identity)."""
        account1 = Account.create("Assets:A", AccountType.ASSET, "BRL")
        account2 = Account.create("Assets:B", AccountType.ASSET, "BRL")

        # IDs diferentes = não são iguais
        assert account1 != account2

        # Mesma instância = igual
        same = account1
        assert same == account1

    def test_equality_with_different_type(self):
        """Deve retornar False ao comparar com não-Account."""
        account = Account.create("Assets:A", AccountType.ASSET, "BRL")

        assert account != "not an account"
        assert account != 123
        assert account != None

    def test_hash_by_id(self):
        """Deve gerar hash baseado em ID."""
        account = Account.create("Assets:A", AccountType.ASSET, "BRL")

        # Deve ser hashable (pode usar em set/dict)
        accounts_set = {account}
        assert account in accounts_set

        # Hash deve ser consistente
        assert hash(account) == hash(account)


class TestAccountStringRepresentation:
    """Testes de representação string."""

    def test_str_representation(self):
        """Deve formatar string legível."""
        account = Account.create(
            "Assets:Checking",
            AccountType.ASSET,
            "BRL"
        )

        result = str(account)

        assert "Assets:Checking" in result
        assert "ASSET" in result
        assert "BRL" in result

    def test_str_representation_inactive(self):
        """Deve indicar conta inativa."""
        account = Account.create("Assets:Old", AccountType.ASSET, "BRL")
        account.deactivate()

        result = str(account)

        assert "INACTIVE" in result

    def test_repr_representation(self):
        """Deve formatar string técnica."""
        account = Account.create(
            "Assets:Checking",
            AccountType.ASSET,
            "BRL"
        )

        result = repr(account)

        assert "Account(" in result
        assert "id=" in result
        assert "name='Assets:Checking'" in result
        assert "account_type=" in result
        assert "currency='BRL'" in result


class TestAccountTypeIntegration:
    """Testes de integração com AccountType."""

    def test_all_account_types(self):
        """Deve criar conta com todos os tipos."""
        types = [
            AccountType.ASSET,
            AccountType.LIABILITY,
            AccountType.EQUITY,
            AccountType.INCOME,
            AccountType.EXPENSE
        ]

        for account_type in types:
            account = Account.create(
                f"Test:{account_type.value}",
                account_type,
                "BRL"
            )
            assert account.account_type == account_type
