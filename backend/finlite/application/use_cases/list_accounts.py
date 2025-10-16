"""List Accounts Use Case."""

from decimal import Decimal

from finlite.application.dtos import AccountDTO
from finlite.domain.entities import Account
from finlite.domain.repositories import IUnitOfWork
from finlite.domain.value_objects import AccountType


class ListAccountsUseCase:
    """Use case for listing accounts.

    This use case:
    1. Retrieves all accounts from repository
    2. Optionally filters by type
    3. Returns account DTOs
    """

    def __init__(self, uow: IUnitOfWork) -> None:
        """Initialize use case with unit of work.

        Args:
            uow: Unit of work for transaction management
        """
        self._uow = uow

    def execute(
        self,
        account_type: AccountType | None = None,
        include_inactive: bool = False,
    ) -> list[AccountDTO]:
        """Execute the use case.

        Args:
            account_type: Optional filter by account type
            include_inactive: Whether to include inactive accounts

        Returns:
            List of account DTOs
        """
        with self._uow:
            # Get all accounts
            accounts = self._uow.accounts.list_all()

            # Apply filters
            filtered_accounts = accounts
            if account_type is not None:
                filtered_accounts = [
                    acc for acc in filtered_accounts if acc.account_type == account_type
                ]

            if not include_inactive:
                filtered_accounts = [
                    acc for acc in filtered_accounts if acc.is_active
                ]

            # Convert to DTOs
            return [self._to_dto(account) for account in filtered_accounts]

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
        )
