"""
IAccountRepository - Interface para repositório de contas.

Define contrato para persistência de Account entities.
Implementações concretas (SQLAlchemy, JSON, etc) devem seguir esta interface.

Padrão: Repository Pattern (Domain-Driven Design)
Referência: https://martinfowler.com/eaaCatalog/repository.html
"""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from finlite.domain.entities.account import Account
from finlite.domain.value_objects.account_type import AccountType


class IAccountRepository(ABC):
    """
    Interface abstrata para repositório de contas.

    Repositório esconde detalhes de persistência do domínio.
    Permite trocar implementação (DB, JSON, mock) sem mudar domínio.

    Examples:
        >>> # Implementação concreta
        >>> class SQLAccountRepository(IAccountRepository):
        ...     def add(self, account: Account) -> None:
        ...         # Salva no PostgreSQL
        ...         pass
        ...
        >>> # Implementação mock para testes
        >>> class InMemoryAccountRepository(IAccountRepository):
        ...     def __init__(self):
        ...         self.accounts = {}
        ...     
        ...     def add(self, account: Account) -> None:
        ...         self.accounts[account.id] = account
    """

    @abstractmethod
    def add(self, account: Account) -> None:
        """
        Adiciona nova conta ao repositório.

        Args:
            account: Conta a ser adicionada

        Raises:
            DuplicateAccountError: Se conta com mesmo nome já existe
        """
        pass

    @abstractmethod
    def get(self, account_id: UUID) -> Account:
        """
        Busca conta por ID.

        Args:
            account_id: UUID da conta

        Returns:
            Conta encontrada

        Raises:
            AccountNotFoundError: Se conta não existir
        """
        pass

    @abstractmethod
    def find_by_name(self, name: str) -> Optional[Account]:
        """
        Busca conta por nome exato.

        Args:
            name: Nome completo da conta (ex: "Assets:Checking")

        Returns:
            Conta encontrada ou None
        """
        pass

    @abstractmethod
    def find_by_code(self, code: str) -> Optional[Account]:
        """
        Busca conta por código único.

        Args:
            code: Código único da conta (ex: "ASSET001" ou "Assets:Checking")

        Returns:
            Conta encontrada ou None

        Examples:
            >>> account = repo.find_by_code("ASSET001")
            >>> if account:
            ...     print(account.name)
        """
        pass

    @abstractmethod
    def find_by_type(self, account_type: AccountType) -> list[Account]:
        """
        Busca todas as contas de determinado tipo.

        Args:
            account_type: Tipo de conta (ASSET, LIABILITY, etc)

        Returns:
            Lista de contas (pode estar vazia)
        """
        pass

    @abstractmethod
    def find_children(self, parent_id: UUID) -> list[Account]:
        """
        Busca contas filhas diretas de uma conta.

        Args:
            parent_id: UUID da conta pai

        Returns:
            Lista de contas filhas (pode estar vazia)
        """
        pass

    @abstractmethod
    def find_root_accounts(self) -> list[Account]:
        """
        Busca contas raiz (sem pai).

        Returns:
            Lista de contas raiz (pode estar vazia)
        """
        pass

    @abstractmethod
    def list_all(self, include_inactive: bool = False) -> list[Account]:
        """
        Lista todas as contas.

        Args:
            include_inactive: Se True, inclui contas desativadas

        Returns:
            Lista de contas (pode estar vazia)
        """
        pass

    @abstractmethod
    def update(self, account: Account) -> None:
        """
        Atualiza conta existente.

        Args:
            account: Conta com dados atualizados

        Raises:
            AccountNotFoundError: Se conta não existir
        """
        pass

    @abstractmethod
    def delete(self, account_id: UUID) -> None:
        """
        Remove conta do repositório.

        Args:
            account_id: UUID da conta a remover

        Raises:
            AccountNotFoundError: Se conta não existir

        Note:
            Considere usar Account.deactivate() ao invés de deletar
            para manter histórico.
        """
        pass

    @abstractmethod
    def exists_by_name(self, name: str) -> bool:
        """
        Verifica se conta com determinado nome existe.

        Args:
            name: Nome completo da conta

        Returns:
            True se conta existe
        """
        pass

    @abstractmethod
    def count(self, include_inactive: bool = False) -> int:
        """
        Conta número total de contas.

        Args:
            include_inactive: Se True, inclui contas desativadas

        Returns:
            Número de contas
        """
        pass
