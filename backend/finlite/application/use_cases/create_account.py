"""Create Account Use Case."""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from finlite.application.dtos import AccountDTO, CreateAccountDTO
from finlite.domain.entities import Account
from finlite.domain.exceptions import AccountAlreadyExistsError
from finlite.domain.repositories import IUnitOfWork
from finlite.domain.value_objects import AccountType


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
    4. Returns the created account DTO
    """

    def __init__(self, uow: IUnitOfWork) -> None:
        """Initialize use case with unit of work.

        Args:
            uow: Unit of work for transaction management
        """
        self._uow = uow

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
                raise AccountAlreadyExistsError(
                    f"Account with code '{dto.code}' already exists"
                )

            # Create domain entity
            account = Account.create(
                name=dto.code,  # Using code as name for now
                account_type=AccountType[dto.type],
                currency=dto.currency,
                parent_id=None,  # Will be resolved later
            )

            # Persist
            self._uow.accounts.add(account)
            self._uow.commit()

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
            code=account.name,  # Using name as code for now
            name=account.name,
            type=account.account_type.name,
            currency=account.currency,
            balance=Decimal("0"),  # TODO: Calculate balance from transactions
            parent_code=None,  # TODO: Resolve from parent_id
            is_placeholder=False,  # TODO: Add to Account entity
            tags=(),  # TODO: Add to Account entity
        )
