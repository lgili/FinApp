"""Create Account Use Case."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from uuid import UUID

from finlite.application.dtos import AccountDTO, CreateAccountDTO
from finlite.domain.entities import Account
from finlite.domain.events import AccountCreated
from finlite.domain.exceptions import AccountAlreadyExistsError
from finlite.domain.repositories import IUnitOfWork
from finlite.domain.value_objects import AccountType
from finlite.shared.observability import get_logger


logger = get_logger(__name__)


@dataclass
class CreateAccountResult:
    """Result of account creation."""

    account: AccountDTO
    created: bool  # False if account already existed


class CreateAccountUseCase:
    """Use case for creating a new account.

    This use case:
    1. Validates that account doesn't already exist
    2. Creates the account entity
    3. Persists it using the repository
    4. Publishes AccountCreated event
    5. Returns the created account DTO
    """

    def __init__(self, uow: IUnitOfWork, event_bus=None) -> None:
        """Initialize use case with unit of work and optional event bus.

        Args:
            uow: Unit of work for transaction management
            event_bus: Optional event bus for publishing domain events
        """
        self._uow = uow
        self._event_bus = event_bus

    def execute(self, dto: CreateAccountDTO) -> CreateAccountResult:
        """Execute the use case.

        Args:
            dto: Account creation data

        Returns:
            CreateAccountResult with the created account

        Raises:
            AccountAlreadyExistsError: If account with code already exists
            ValueError: If account data is invalid
        """
        with self._uow:
            # Check if account already exists
            existing = self._uow.accounts.find_by_code(dto.code)
            if existing:
                logger.warning(
                    "account_creation_failed",
                    reason="account_already_exists",
                    account_code=dto.code,
                )
                raise AccountAlreadyExistsError(
                    f"Account with code '{dto.code}' already exists"
                )

            logger.info("creating_account", account_code=dto.code, account_type=dto.type)

            metadata_values = (
                dto.card_issuer,
                dto.card_closing_day,
                dto.card_due_day,
            )
            is_liability = dto.type.upper() == AccountType.LIABILITY.name
            if not is_liability and any(value is not None for value in metadata_values):
                raise ValueError(
                    "Card metadata can only be provided for LIABILITY accounts"
                )
            if is_liability and any(value is not None for value in metadata_values):
                if dto.card_issuer is None or dto.card_closing_day is None or dto.card_due_day is None:
                    raise ValueError(
                        "card_issuer, card_closing_day, and card_due_day must all be provided for credit card accounts"
                    )

            # Create domain entity
            account = Account.create(
                code=dto.code,
                name=dto.name,
                account_type=AccountType[dto.type],
            currency=dto.currency,
            parent_id=None,  # Will be resolved later
            card_issuer=dto.card_issuer,
            card_closing_day=dto.card_closing_day,
            card_due_day=dto.card_due_day,
        )

            # Persist
            self._uow.accounts.add(account)
            self._uow.commit()

            logger.info(
                "account_created",
                account_id=str(account.id),
                account_code=account.code,
                account_type=account.account_type.name,
                currency=account.currency,
            )

            # Publish domain event
            if self._event_bus:
                event = AccountCreated(
                    account_id=account.id,
                    account_code=account.code,
                    account_type=account.account_type.name,
                    currency=account.currency,
                )
                self._event_bus.publish(event)

            # Convert to DTO
            account_dto = self._to_dto(account)

            return CreateAccountResult(account=account_dto, created=True)

    def _to_dto(self, account: Account) -> AccountDTO:
        """Convert domain entity to DTO.

        Args:
            account: Domain account entity

        Returns:
            Account DTO
        """
        return AccountDTO(
            id=account.id,
            code=account.code,
            name=account.name,
            type=account.account_type.name,
            currency=account.currency,
            balance=Decimal("0"),  # TODO: Calculate balance from transactions
            parent_code=None,  # TODO: Resolve from parent_id
            is_placeholder=False,  # TODO: Add to Account entity
            tags=(),  # TODO: Add to Account entity
            card_issuer=account.card_issuer,
            card_closing_day=account.card_closing_day,
            card_due_day=account.card_due_day,
        )
