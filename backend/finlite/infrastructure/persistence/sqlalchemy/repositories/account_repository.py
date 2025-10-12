"""
SqlAlchemyAccountRepository - Implementação concreta do IAccountRepository.

Usa SQLAlchemy para persistir/recuperar Accounts do banco de dados.
Converte entre Domain (Account) e ORM (AccountModel) via AccountMapper.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from finlite.domain.entities.account import Account
from finlite.domain.repositories.account_repository import IAccountRepository
from finlite.domain.value_objects.account_type import AccountType
from finlite.infrastructure.persistence.sqlalchemy.mappers.account_mapper import (
    AccountMapper,
)
from finlite.infrastructure.persistence.sqlalchemy.models import AccountModel


class SqlAlchemyAccountRepository(IAccountRepository):
    """
    Repository concreto para Account usando SQLAlchemy.

    Implementa IAccountRepository usando SQLAlchemy + AccountMapper.

    Examples:
        >>> session = Session(engine)
        >>> repo = SqlAlchemyAccountRepository(session)
        >>>
        >>> # Criar e salvar
        >>> account = Account.create("Assets:Checking", AccountType.ASSET, "BRL")
        >>> repo.add(account)
        >>> session.commit()
        >>>
        >>> # Buscar
        >>> found = repo.get(account.id)
    """

    def __init__(self, session: Session) -> None:
        """
        Inicializa repository com sessão SQLAlchemy.

        Args:
            session: SQLAlchemy session (gerenciada por UnitOfWork)
        """
        self._session = session

    def add(self, account: Account) -> None:
        """
        Adiciona nova conta ao repositório.

        Args:
            account: Entity do domínio para persistir

        Examples:
            >>> account = Account.create("Assets:Checking", AccountType.ASSET, "BRL")
            >>> repo.add(account)
            >>> session.commit()
        """
        model = AccountMapper.to_model(account)
        self._session.add(model)

    def get(self, account_id: UUID) -> Account:
        """
        Busca conta por ID.

        Args:
            account_id: UUID da conta

        Returns:
            Account entity

        Raises:
            AccountNotFoundError: Se conta não existir

        Examples:
            >>> account = repo.get(account_id)
            >>> print(account.name)
        """
        from finlite.domain.exceptions import AccountNotFoundError

        model = self._session.get(AccountModel, account_id)
        if model is None:
            raise AccountNotFoundError(account_id)
        return AccountMapper.to_entity(model)

    def find_by_name(self, name: str) -> Optional[Account]:
        """
        Busca conta por nome exato.

        Args:
            name: Nome completo da conta (ex: "Assets:Checking")

        Returns:
            Account entity ou None se não encontrado

        Examples:
            >>> account = repo.find_by_name("Assets:Checking")
        """
        stmt = select(AccountModel).where(AccountModel.name == name)
        model = self._session.scalar(stmt)

        if model is None:
            return None
        return AccountMapper.to_entity(model)

    def find_by_code(self, code: str) -> Optional[Account]:
        """
        Busca conta por código único.

        Args:
            code: Código único da conta (ex: "ASSET001" ou "Assets:Checking")

        Returns:
            Account entity ou None se não encontrado

        Note:
            No modelo ORM, o 'code' do domínio é mapeado para 'name' no banco.
            Este método usa 'name' internamente.

        Examples:
            >>> account = repo.find_by_code("ASSET001")
            >>> if account:
            ...     print(account.name)
        """
        # No ORM, o 'code' do domínio é armazenado como 'name'
        stmt = select(AccountModel).where(AccountModel.name == code)
        model = self._session.scalar(stmt)

        if model is None:
            return None
        return AccountMapper.to_entity(model)

    def find_by_type(self, account_type: AccountType) -> list[Account]:
        """
        Busca todas as contas de um tipo.

        Args:
            account_type: Tipo de conta (ASSET, LIABILITY, etc)

        Returns:
            Lista de Account entities

        Examples:
            >>> assets = repo.find_by_type(AccountType.ASSET)
            >>> for account in assets:
            ...     print(account.name)
        """
        # Converte domain type para ORM enum
        orm_type = AccountMapper._domain_type_to_orm(account_type)

        stmt = select(AccountModel).where(AccountModel.account_type == orm_type)
        models = self._session.scalars(stmt).all()

        return [AccountMapper.to_entity(model) for model in models]

    def find_children(self, parent_id: UUID) -> list[Account]:
        """
        Busca contas filhas diretas de uma conta.

        Args:
            parent_id: UUID da conta pai

        Returns:
            Lista de Account entities filhas

        Examples:
            >>> children = repo.find_children(parent_account_id)
        """
        stmt = select(AccountModel).where(AccountModel.parent_id == parent_id)
        models = self._session.scalars(stmt).all()

        return [AccountMapper.to_entity(model) for model in models]

    def find_root_accounts(self) -> list[Account]:
        """
        Busca contas raiz (sem pai).

        Returns:
            Lista de Account entities raiz

        Examples:
            >>> roots = repo.find_root_accounts()
        """
        stmt = select(AccountModel).where(AccountModel.parent_id.is_(None))
        models = self._session.scalars(stmt).all()

        return [AccountMapper.to_entity(model) for model in models]

    def list_all(self, include_inactive: bool = False) -> list[Account]:
        """
        Lista todas as contas.

        Args:
            include_inactive: Se True, inclui contas desativadas

        Returns:
            Lista de Account entities

        Examples:
            >>> all_accounts = repo.list_all(include_inactive=True)
            >>> active_accounts = repo.list_all(include_inactive=False)
        """
        stmt = select(AccountModel)

        if not include_inactive:
            stmt = stmt.where(AccountModel.is_active == True)  # noqa: E712

        stmt = stmt.order_by(AccountModel.name)
        models = self._session.scalars(stmt).all()

        return [AccountMapper.to_entity(model) for model in models]

    def exists(self, account_id: UUID) -> bool:
        """
        Verifica se conta existe por ID.

        Args:
            account_id: UUID da conta

        Returns:
            True se existe

        Examples:
            >>> if repo.exists(account_id):
            ...     print("Conta existe")
        """
        stmt = select(AccountModel.id).where(AccountModel.id == account_id)
        result = self._session.scalar(stmt)
        return result is not None

    def exists_by_name(self, name: str) -> bool:
        """
        Verifica se conta com determinado nome existe.

        Args:
            name: Nome completo da conta

        Returns:
            True se conta com esse nome existe

        Examples:
            >>> if repo.exists_by_name("Assets:Checking"):
            ...     print("Conta já existe")
        """
        stmt = select(AccountModel.id).where(AccountModel.name == name)
        result = self._session.scalar(stmt)
        return result is not None

    def count(self, include_inactive: bool = False) -> int:
        """
        Conta número total de contas.

        Args:
            include_inactive: Se True, inclui contas desativadas

        Returns:
            Número de contas

        Examples:
            >>> total = repo.count()
            >>> active_only = repo.count(include_inactive=False)
        """
        from sqlalchemy import func

        stmt = select(func.count(AccountModel.id))

        if not include_inactive:
            stmt = stmt.where(AccountModel.is_active == True)  # noqa: E712

        return self._session.scalar(stmt) or 0

    def update(self, account: Account) -> None:
        """
        Atualiza conta existente.

        Args:
            account: Entity com dados atualizados

        Raises:
            AccountNotFoundError: Se conta não existe

        Examples:
            >>> account = repo.get(account_id)
            >>> account.rename("Assets:NewName")
            >>> repo.update(account)
            >>> session.commit()
        """
        from finlite.domain.exceptions import AccountNotFoundError

        model = self._session.get(AccountModel, account.id)

        if model is None:
            raise AccountNotFoundError(account.id)

        AccountMapper.update_model_from_entity(model, account)

    def delete(self, account_id: UUID) -> None:
        """
        Remove conta do repositório.

        ATENÇÃO: Apenas para testes. Em produção, use account.deactivate().

        Args:
            account_id: UUID da conta

        Raises:
            AccountNotFoundError: Se conta não existe

        Examples:
            >>> repo.delete(account_id)  # Apenas em testes!
        """
        from finlite.domain.exceptions import AccountNotFoundError

        model = self._session.get(AccountModel, account_id)

        if model is None:
            raise AccountNotFoundError(account_id)

        self._session.delete(model)
