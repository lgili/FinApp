"""
AccountMapper - Converte entre Domain Account e ORM AccountModel.

O mapper é responsável por traduzir entre:
- Domain Entity (Account) ←→ ORM Model (AccountModel)

Garante que o domain permanece puro (sem dependências de SQLAlchemy).

Note: Handles UUID (domain) ↔ Integer (database) conversion.
"""

from __future__ import annotations

from uuid import UUID

from finlite.domain.entities.account import Account
from finlite.domain.value_objects.account_type import AccountType
from finlite.infrastructure.persistence.sqlalchemy.models import AccountModel
from finlite.infrastructure.persistence.sqlalchemy.mappers._uuid_helpers import (
    uuid_to_int,
    int_to_uuid,
)


class AccountMapper:
    """
    Mapper bidirectional para Account ←→ AccountModel.
    
    Converts between UUID (domain) and Integer (database) IDs.
    Stores UUID in 'code' column for full recovery.

    Examples:
        >>> # Domain → ORM
        >>> account = Account.create("Assets:Checking", AccountType.ASSET, "BRL")
        >>> model = AccountMapper.to_model(account)
        >>>
        >>> # ORM → Domain
        >>> account = AccountMapper.to_entity(model)
    """

    @staticmethod
    def to_model(account: Account, for_update: bool = False) -> AccountModel:
        """
        Converte Domain Account para ORM AccountModel.

        Args:
            account: Entity do domínio
            for_update: Se True, inclui o ID (para updates). Se False, omite o ID (para inserts).

        Returns:
            ORM model pronto para persistir

        Examples:
            >>> # Novo account (insert) - não passa ID
            >>> account = Account.create("Assets:Checking", AccountType.ASSET, "BRL")
            >>> model = AccountMapper.to_model(account)
            >>> 
            >>> # Update account existente
            >>> model = AccountMapper.to_model(account, for_update=True)
        """
        model_data = {
            "name": account.name,
            "code": str(account.id),  # Store UUID in code column
            "type": account.account_type.value,
            "currency": account.currency,
            "parent_id": account.parent_id,  # Repository handles UUID→Integer conversion
            "is_archived": not account.is_active,
            "created_at": account.created_at,
            "updated_at": account.updated_at,
        }
        
        # Para updates, incluir o ID convertido de UUID
        if for_update and account.id:
            # Extrair integer ID do UUID se possível
            # Assumimos que UUIDs foram gerados a partir de Integer IDs
            model_data["id"] = AccountMapper._uuid_to_int(account.id)
        
        return AccountModel(**model_data)

    @staticmethod
    def to_entity(model: AccountModel, parent_model: AccountModel | None = None) -> Account:
        """
        Converte ORM AccountModel para Domain Account.

        Args:
            model: ORM model do banco
            parent_model: ORM model do parent (opcional, para preservar UUID correto)

        Returns:
            Entity do domínio

        Examples:
            >>> model = AccountModel(id=1, name="Assets:Checking", ...)
            >>> account = AccountMapper.to_entity(model)
            >>> account.name
            'Assets:Checking'
        """
        # If code contains a UUID, use it; otherwise generate from integer ID
        if model.code:
            try:
                account_id = UUID(model.code)
            except (ValueError, AttributeError):
                account_id = int_to_uuid(model.id)
        else:
            account_id = int_to_uuid(model.id)
        
        # For parent_id: if parent_model provided, use its UUID from code
        if parent_model:
            try:
                parent_id = UUID(parent_model.code) if parent_model.code else int_to_uuid(parent_model.id)
            except (ValueError, AttributeError):
                parent_id = int_to_uuid(parent_model.id)
        elif model.parent_id:
            parent_id = int_to_uuid(model.parent_id)
        else:
            parent_id = None
            
        return Account(
            id=account_id,
            name=model.name,
            account_type=AccountType(model.type),
            currency=model.currency,
            parent_id=parent_id,
            is_active=not model.is_archived,
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
        model.code = str(account.id)
        model.type = account.account_type.value
        model.currency = account.currency
        model.parent_id = account.parent_id
        model.is_archived = not account.is_active
        model.updated_at = account.updated_at
