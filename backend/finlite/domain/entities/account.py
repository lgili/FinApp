"""
Account Entity - Representa uma conta contábil.

Em contabilidade de partida dobrada, contas são categorizações
hierárquicas onde transações são registradas.

Exemplos:
    Assets:Checking              (Conta corrente)
    Assets:Investments:Stocks    (Investimentos em ações)
    Liabilities:CreditCard       (Cartão de crédito)
    Income:Salary                (Salário)
    Expenses:Food:Restaurant     (Alimentação em restaurantes)

Referências:
- Chart of Accounts: https://en.wikipedia.org/wiki/Chart_of_accounts
- Domain-Driven Design: Entities têm identidade e ciclo de vida
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from finlite.domain.value_objects.account_type import AccountType


@dataclass
class Account:
    """
    Entity representando uma conta contábil.

    Entities têm identidade própria (UUID) e ciclo de vida.
    São mutáveis (podem ter nome alterado, por exemplo).

    Attributes:
        id: Identificador único (UUID)
        name: Nome da conta (ex: "Assets:Checking", "Expenses:Food")
        account_type: Tipo contábil (ASSET, LIABILITY, etc)
        currency: Moeda padrão da conta (ISO 4217)
        parent_id: UUID da conta pai (hierarquia), None para raiz
        is_active: Se a conta está ativa (pode desativar sem deletar)
        created_at: Data de criação
        updated_at: Data de última atualização

    Examples:
        >>> # Conta de ativo (conta corrente)
        >>> checking = Account.create(
        ...     name="Assets:Checking",
        ...     account_type=AccountType.ASSET,
        ...     currency="BRL"
        ... )

        >>> # Conta de despesa (subconta de Food)
        >>> food_id = uuid4()
        >>> restaurant = Account.create(
        ...     name="Expenses:Food:Restaurant",
        ...     account_type=AccountType.EXPENSE,
        ...     currency="BRL",
        ...     parent_id=food_id
        ... )

        >>> # Desativar conta
        >>> checking.deactivate()
        >>> checking.is_active
        False
    """

    id: UUID
    name: str
    account_type: AccountType
    currency: str
    parent_id: Optional[UUID] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validações após inicialização."""
        self._validate_name()
        self._validate_currency()

    @classmethod
    def create(
        cls,
        name: str,
        account_type: AccountType,
        currency: str,
        parent_id: Optional[UUID] = None,
    ) -> Account:
        """
        Factory method para criar nova conta.

        Args:
            name: Nome da conta (ex: "Assets:Checking")
            account_type: Tipo contábil
            currency: Moeda padrão (ISO 4217)
            parent_id: UUID da conta pai (opcional)

        Returns:
            Nova instância de Account

        Examples:
            >>> account = Account.create(
            ...     name="Assets:Checking",
            ...     account_type=AccountType.ASSET,
            ...     currency="BRL"
            ... )
        """
        return cls(
            id=uuid4(),
            name=name,
            account_type=account_type,
            currency=currency,
            parent_id=parent_id,
        )

    def rename(self, new_name: str) -> None:
        """
        Renomeia a conta.

        Args:
            new_name: Novo nome da conta

        Raises:
            ValueError: Se novo nome for inválido

        Examples:
            >>> account = Account.create("Assets:Bank", AccountType.ASSET, "BRL")
            >>> account.rename("Assets:Checking")
            >>> account.name
            'Assets:Checking'
        """
        old_name = self.name
        self.name = new_name

        try:
            self._validate_name()
        except ValueError:
            self.name = old_name  # Rollback em caso de erro
            raise

        self.updated_at = datetime.utcnow()

    def deactivate(self) -> None:
        """
        Desativa a conta (soft delete).

        Contas desativadas não podem receber novos lançamentos,
        mas mantêm histórico.

        Examples:
            >>> account = Account.create("Assets:Old", AccountType.ASSET, "BRL")
            >>> account.deactivate()
            >>> account.is_active
            False
        """
        self.is_active = False
        self.updated_at = datetime.utcnow()

    def reactivate(self) -> None:
        """
        Reativa conta desativada.

        Examples:
            >>> account = Account.create("Assets:Temp", AccountType.ASSET, "BRL")
            >>> account.deactivate()
            >>> account.reactivate()
            >>> account.is_active
            True
        """
        self.is_active = True
        self.updated_at = datetime.utcnow()

    def change_parent(self, new_parent_id: Optional[UUID]) -> None:
        """
        Altera conta pai (reorganiza hierarquia).

        Args:
            new_parent_id: Novo UUID da conta pai (None = raiz)

        Raises:
            ValueError: Se tentar definir próprio ID como pai

        Examples:
            >>> account = Account.create("Expenses:Food", AccountType.EXPENSE, "BRL")
            >>> expenses_id = uuid4()
            >>> account.change_parent(expenses_id)
            >>> account.parent_id == expenses_id
            True
        """
        if new_parent_id is not None and new_parent_id == self.id:
            raise ValueError("Account cannot be its own parent")

        self.parent_id = new_parent_id
        self.updated_at = datetime.utcnow()

    def is_root(self) -> bool:
        """
        Verifica se é conta raiz (sem pai).

        Returns:
            True se parent_id é None

        Examples:
            >>> root = Account.create("Assets", AccountType.ASSET, "BRL")
            >>> root.is_root()
            True

            >>> child = Account.create(
            ...     "Assets:Checking",
            ...     AccountType.ASSET,
            ...     "BRL",
            ...     parent_id=root.id
            ... )
            >>> child.is_root()
            False
        """
        return self.parent_id is None

    def is_child_of(self, parent_id: UUID) -> bool:
        """
        Verifica se é filho direto de uma conta.

        Args:
            parent_id: UUID da suposta conta pai

        Returns:
            True se parent_id corresponde

        Examples:
            >>> parent = Account.create("Expenses", AccountType.EXPENSE, "BRL")
            >>> child = Account.create(
            ...     "Expenses:Food",
            ...     AccountType.EXPENSE,
            ...     "BRL",
            ...     parent_id=parent.id
            ... )
            >>> child.is_child_of(parent.id)
            True
        """
        return self.parent_id == parent_id

    def get_full_name_parts(self) -> list[str]:
        """
        Divide nome completo em partes hierárquicas.

        Returns:
            Lista de partes do nome

        Examples:
            >>> account = Account.create(
            ...     "Expenses:Food:Restaurant",
            ...     AccountType.EXPENSE,
            ...     "BRL"
            ... )
            >>> account.get_full_name_parts()
            ['Expenses', 'Food', 'Restaurant']
        """
        return self.name.split(":")

    def get_depth(self) -> int:
        """
        Retorna profundidade da conta na hierarquia.

        Returns:
            Número de níveis (1 = raiz, 2 = filho direto, etc)

        Examples:
            >>> root = Account.create("Assets", AccountType.ASSET, "BRL")
            >>> root.get_depth()
            1

            >>> nested = Account.create(
            ...     "Assets:Investments:Stocks",
            ...     AccountType.ASSET,
            ...     "BRL"
            ... )
            >>> nested.get_depth()
            3
        """
        return len(self.get_full_name_parts())

    def _validate_name(self) -> None:
        """
        Valida formato do nome da conta.

        Raises:
            ValueError: Se nome for inválido
        """
        if not isinstance(self.name, str):
            raise TypeError(f"Account name must be str, got {type(self.name)}")

        if not self.name.strip():
            raise ValueError("Account name cannot be empty")

        # Valida formato hierárquico (ex: "Assets:Checking")
        parts = self.name.split(":")
        for part in parts:
            if not part.strip():
                raise ValueError(
                    f"Account name has empty component: '{self.name}'"
                )

            # Valida caracteres (alfanuméricos, espaços, alguns símbolos)
            if not part.replace(" ", "").replace("-", "").replace("_", "").isalnum():
                raise ValueError(
                    f"Account name contains invalid characters: '{part}' in '{self.name}'"
                )

    def _validate_currency(self) -> None:
        """
        Valida formato ISO 4217 da moeda.

        Raises:
            ValueError: Se moeda for inválida
        """
        if not isinstance(self.currency, str):
            raise TypeError(f"Currency must be str, got {type(self.currency)}")

        if len(self.currency) != 3 or not self.currency.isupper():
            raise ValueError(
                f"Currency must be 3 uppercase letters (ISO 4217), got '{self.currency}'"
            )

    def __eq__(self, other: object) -> bool:
        """
        Igualdade baseada em ID (entity identity).

        Entities são comparadas por identidade, não por valor.
        Duas contas são iguais se têm o mesmo UUID.

        Examples:
            >>> account1 = Account.create("Assets:A", AccountType.ASSET, "BRL")
            >>> account2 = Account.create("Assets:B", AccountType.ASSET, "BRL")
            >>> account1 == account2
            False  # IDs diferentes

            >>> same = account1
            >>> same == account1
            True  # Mesmo ID
        """
        if not isinstance(other, Account):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash baseado em ID (para usar em sets/dicts)."""
        return hash(self.id)

    def __str__(self) -> str:
        """
        Representação string legível.

        Returns:
            Formato: "name (type) [currency]"

        Examples:
            >>> account = Account.create(
            ...     "Assets:Checking",
            ...     AccountType.ASSET,
            ...     "BRL"
            ... )
            >>> str(account)
            'Assets:Checking (ASSET) [BRL]'
        """
        status = "" if self.is_active else " [INACTIVE]"
        return f"{self.name} ({self.account_type.value}) [{self.currency}]{status}"

    def __repr__(self) -> str:
        """Representação técnica para debug."""
        return (
            f"Account(id={self.id!r}, name={self.name!r}, "
            f"account_type={self.account_type!r}, currency={self.currency!r})"
        )
