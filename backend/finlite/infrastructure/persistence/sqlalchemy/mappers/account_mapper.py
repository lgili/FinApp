"""
AccountMapper - Converte entre Domain Account e ORM AccountModel.

O mapper é responsável por traduzir entre:
- Domain Entity (Account) ←→ ORM Model (AccountModel)

Garante que o domain permanece puro (sem dependências de SQLAlchemy).
"""

from __future__ import annotations

from finlite.domain.entities.account import Account
from finlite.domain.value_objects.account_type import AccountType
from finlite.infrastructure.persistence.sqlalchemy.models import (
    AccountModel,
    AccountTypeEnum,
)


class AccountMapper:
    """
    Mapper bidirectional para Account ←→ AccountModel.

    Examples:
        >>> # Domain → ORM
        >>> account = Account.create("Assets:Checking", AccountType.ASSET, "BRL")
        >>> model = AccountMapper.to_model(account)
        >>>
        >>> # ORM → Domain
        >>> account = AccountMapper.to_entity(model)
    """

    @staticmethod
    def to_model(account: Account) -> AccountModel:
        """
        Converte Domain Account para ORM AccountModel.

        Args:
            account: Entity do domínio

        Returns:
            ORM model pronto para persistir

        Examples:
            >>> account = Account.create(
            ...     name="Assets:Checking",
            ...     account_type=AccountType.ASSET,
            ...     currency="BRL"
            ... )
            >>> model = AccountMapper.to_model(account)
            >>> model.name
            'Assets:Checking'
        """
        return AccountModel(
            id=account.id,
            name=account.name,
            account_type=AccountMapper._domain_type_to_orm(account.account_type),
            currency=account.currency,
            parent_id=account.parent_id,
            is_active=account.is_active,
            created_at=account.created_at,
            updated_at=account.updated_at,
        )

    @staticmethod
    def to_entity(model: AccountModel) -> Account:
        """
        Converte ORM AccountModel para Domain Account.

        Args:
            model: ORM model do banco

        Returns:
            Entity do domínio

        Examples:
            >>> model = AccountModel(
            ...     id=uuid4(),
            ...     name="Assets:Checking",
            ...     account_type=AccountTypeEnum.ASSET,
            ...     currency="BRL",
            ...     created_at=datetime.utcnow(),
            ...     updated_at=datetime.utcnow()
            ... )
            >>> account = AccountMapper.to_entity(model)
            >>> account.name
            'Assets:Checking'
        """
        return Account(
            id=model.id,
            name=model.name,
            account_type=AccountMapper._orm_type_to_domain(model.account_type),
            currency=model.currency,
            parent_id=model.parent_id,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def update_model_from_entity(model: AccountModel, account: Account) -> None:
        """
        Atualiza ORM model existente com dados da entity.

        Útil para updates sem recriar o model.

        Args:
            model: ORM model existente (será modificado)
            account: Entity com dados atualizados

        Examples:
            >>> model = session.get(AccountModel, account_id)
            >>> account.rename("Assets:NewName")
            >>> AccountMapper.update_model_from_entity(model, account)
            >>> session.commit()
        """
        model.name = account.name
        model.account_type = AccountMapper._domain_type_to_orm(account.account_type)
        model.currency = account.currency
        model.parent_id = account.parent_id
        model.is_active = account.is_active
        model.updated_at = account.updated_at

    @staticmethod
    def _domain_type_to_orm(domain_type: AccountType) -> AccountTypeEnum:
        """Converte AccountType (domain) para AccountTypeEnum (ORM)."""
        mapping = {
            AccountType.ASSET: AccountTypeEnum.ASSET,
            AccountType.LIABILITY: AccountTypeEnum.LIABILITY,
            AccountType.EQUITY: AccountTypeEnum.EQUITY,
            AccountType.INCOME: AccountTypeEnum.INCOME,
            AccountType.EXPENSE: AccountTypeEnum.EXPENSE,
        }
        return mapping[domain_type]

    @staticmethod
    def _orm_type_to_domain(orm_type: AccountTypeEnum) -> AccountType:
        """Converte AccountTypeEnum (ORM) para AccountType (domain)."""
        mapping = {
            AccountTypeEnum.ASSET: AccountType.ASSET,
            AccountTypeEnum.LIABILITY: AccountType.LIABILITY,
            AccountTypeEnum.EQUITY: AccountType.EQUITY,
            AccountTypeEnum.INCOME: AccountType.INCOME,
            AccountTypeEnum.EXPENSE: AccountType.EXPENSE,
        }
        return mapping[orm_type]
