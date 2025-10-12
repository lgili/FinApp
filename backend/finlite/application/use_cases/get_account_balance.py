"""Get Account Balance Use Case."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from finlite.application.dtos import AccountDTO
from finlite.domain.entities import Account
from finlite.domain.exceptions import AccountNotFoundError
from finlite.domain.repositories import IUnitOfWork


class GetAccountBalanceUseCase:
    """Use case for getting account balance.

    This use case:
    1. Retrieves account by code or ID
    2. Returns account DTO with current balance
    """

    def __init__(self, uow: IUnitOfWork) -> None:
        """Initialize use case with unit of work.

        Args:
            uow: Unit of work for transaction management
        """
        self._uow = uow

    def execute_by_code(self, code: str) -> AccountDTO:
        """Execute the use case by account code.

        Args:
            code: Account code

        Returns:
            Account DTO with balance

        Raises:
            AccountNotFoundError: If account not found
        """
        with self._uow:
            account = self._uow.accounts.find_by_code(code)
            if not account:
                raise AccountNotFoundError(f"Account with code '{code}' not found")

            return self._to_dto(account)

    def execute_by_id(self, account_id: UUID) -> AccountDTO:
        """Execute the use case by account ID.

        Args:
            account_id: Account UUID

        Returns:
            Account DTO with balance

        Raises:
            AccountNotFoundError: If account not found
        """
        with self._uow:
            account = self._uow.accounts.get(account_id)
            return self._to_dto(account)

    def _to_dto(self, account: Account) -> AccountDTO:
        """Convert domain entity to DTO with calculated balance.

        Args:
            account: Domain account entity

        Returns:
            Account DTO with balance calculated from all transactions
        """
        # Calculate balance by summing all postings for this account
        balance = self._calculate_balance(account.id)
        
        return AccountDTO(
            id=account.id,
            code=account.name,  # Using name as code
            name=account.name,
            type=account.account_type.name,
            currency=account.currency,
            balance=balance,
            parent_code=None,  # TODO: Resolve from parent_id
            is_placeholder=False,  # TODO: Add to Account entity
            tags=(),  # TODO: Add to Account entity
        )

    def _calculate_balance(self, account_id: UUID) -> Decimal:
        """Calculate account balance from all transactions.

        Args:
            account_id: Account UUID

        Returns:
            Current balance (sum of all postings)
        """
        # Get all transactions for this account (no date limit)
        transactions = self._uow.transactions.find_by_date_range(
            start_date=date(1900, 1, 1),  # Far past
            end_date=date(2100, 12, 31),  # Far future
            account_id=account_id,
        )
        
        # Sum all postings for this account
        total = Decimal("0")
        for transaction in transactions:
            for posting in transaction.postings:
                if posting.account_id == account_id:
                    total += posting.amount.amount  # Money.amount is Decimal
        
        return total
