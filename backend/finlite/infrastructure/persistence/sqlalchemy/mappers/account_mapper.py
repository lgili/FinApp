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
    Stores account code for full recovery.

    Examples:
        >>> # Domain → ORM
        >>> account = Account.create(code="Assets:Checking", name="Checking", account_type=AccountType.ASSET, currency="BRL")
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
            >>> account = Account.create(code="Assets:Checking", name="Checking", account_type=AccountType.ASSET, currency="BRL")
            >>> model = AccountMapper.to_model(account)
            >>>
            >>> # Update account existente
            >>> model = AccountMapper.to_model(account, for_update=True)
        """
        model_data = {
            "name": account.name,
            "code": account.code,  # Store account code
            "type": account.account_type.value,
            "currency": account.currency,
            "parent_id": account.parent_id,  # Repository handles UUID→Integer conversion
            "is_archived": not account.is_active,
            "created_at": account.created_at,
            "updated_at": account.updated_at,
            "card_metadata": AccountMapper._card_metadata_to_dict(account),
        }

        # Note: ID is handled by repository, not set here
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
            >>> model = AccountModel(id=1, code="Assets:Checking", name="Checking", ...)
            >>> account = AccountMapper.to_entity(model)
            >>> account.code
            'Assets:Checking'
        """
        # Generate UUID from integer ID (consistent conversion)
        account_id = int_to_uuid(model.id)

        # For parent_id: convert from integer if present
        if parent_model:
            parent_id = int_to_uuid(parent_model.id)
        elif model.parent_id:
            parent_id = int_to_uuid(model.parent_id)
        else:
            parent_id = None

        return Account(
            id=account_id,
            code=model.code,  # Pass the code from database
            name=model.name,
            account_type=AccountType(model.type),
            currency=model.currency,
            parent_id=parent_id,
            is_active=not model.is_archived,
            created_at=model.created_at,
            updated_at=model.updated_at,
            **AccountMapper._card_metadata_to_kwargs(model.card_metadata),
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
            >>> account.rename("New Account Name")
            >>> AccountMapper.update_model_from_entity(model, account)
            >>> session.commit()
        """
        model.name = account.name
        model.code = account.code
        model.type = account.account_type.value
        model.currency = account.currency
        model.parent_id = account.parent_id
        model.is_archived = not account.is_active
        model.updated_at = account.updated_at
        model.card_metadata = AccountMapper._card_metadata_to_dict(account)

    @staticmethod
    def _card_metadata_to_dict(account: Account) -> dict[str, str | int]:
        """
        Serialize card metadata to dict for persistence.
        """
        if not account.has_card_metadata():
            return {}
        return {
            "issuer": account.card_issuer,
            "closing_day": account.card_closing_day,
            "due_day": account.card_due_day,
        }

    @staticmethod
    def _card_metadata_to_kwargs(metadata: dict[str, str | int] | None) -> dict[str, int | str | None]:
        """
        Deserialize stored metadata into Account kwargs.
        """
        if not metadata:
            return {
                "card_issuer": None,
                "card_closing_day": None,
                "card_due_day": None,
            }
        return {
            "card_issuer": metadata.get("issuer"),
            "card_closing_day": metadata.get("closing_day"),
            "card_due_day": metadata.get("due_day"),
        }
