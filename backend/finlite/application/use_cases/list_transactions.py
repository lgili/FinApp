"""List Transactions Use Case."""

from datetime import date
from uuid import UUID

from finlite.application.dtos import TransactionDTO, TransactionFilterDTO, PostingDTO
from finlite.domain.entities import Transaction
from finlite.domain.repositories import IUnitOfWork


class ListTransactionsUseCase:
    """Use case for listing transactions.

    This use case:
    1. Retrieves transactions based on filters
    2. Returns transaction DTOs
    """

    def __init__(self, uow: IUnitOfWork) -> None:
        """Initialize use case with unit of work.

        Args:
            uow: Unit of work for transaction management
        """
        self._uow = uow

    def execute(
        self, filter_dto: TransactionFilterDTO | None = None
    ) -> list[TransactionDTO]:
        """Execute the use case.

        Args:
            filter_dto: Optional filters for transactions

        Returns:
            List of transaction DTOs
        """
        with self._uow:
            if not filter_dto:
                # No filters - get all transactions
                transactions = self._uow.transactions.list_all(limit=100)
            else:
                transactions = self._apply_filters(filter_dto)

            # Convert to DTOs
            return [self._to_dto(txn) for txn in transactions]

    def _apply_filters(self, filter_dto: TransactionFilterDTO) -> list[Transaction]:
        """Apply filters to retrieve transactions.

        Args:
            filter_dto: Filter criteria

        Returns:
            List of filtered transactions
        """
        # Apply date range filter
        if filter_dto.start_date or filter_dto.end_date:
            # Get account_id if account_code provided
            account_id = None
            if filter_dto.account_code:
                account = self._uow.accounts.find_by_code(filter_dto.account_code)
                if account:
                    account_id = account.id

            return self._uow.transactions.find_by_date_range(
                start_date=filter_dto.start_date or date.min,
                end_date=filter_dto.end_date or date.max,
                account_id=account_id,
            )

        # Apply account filter
        if filter_dto.account_code:
            account = self._uow.accounts.find_by_code(filter_dto.account_code)
            if account:
                return self._uow.transactions.find_by_account(
                    account_id=account.id,
                    limit=filter_dto.limit,
                )
            return []

        # Apply description search
        if filter_dto.description:
            return self._uow.transactions.search_description(
                pattern=filter_dto.description,
                limit=filter_dto.limit,
            )

        # Apply tags filter
        if filter_dto.tags:
            return self._uow.transactions.find_by_tags(
                tags=list(filter_dto.tags),
                match_all=True,
            )

        # Default - list all with limit
        return self._uow.transactions.list_all(
            limit=filter_dto.limit,
            order_by="date",
        )

    def _to_dto(self, transaction: Transaction) -> TransactionDTO:
        """Convert domain entity to DTO.

        Args:
            transaction: Domain transaction entity

        Returns:
            Transaction DTO
        """
        # Get account codes for postings
        account_codes = {}  # account_id -> code
        for posting in transaction.postings:
            if posting.account_id not in account_codes:
                try:
                    account = self._uow.accounts.get(posting.account_id)
                    account_codes[posting.account_id] = account.code
                except Exception:
                    account_codes[posting.account_id] = f"UNKNOWN-{posting.account_id}"

        posting_dtos = tuple(
            PostingDTO(
                account_code=account_codes.get(p.account_id, "UNKNOWN"),
                amount=p.amount.amount,
                currency=p.amount.currency,
            )
            for p in transaction.postings
        )

        return TransactionDTO(
            id=transaction.id,
            date=transaction.date,
            description=transaction.description,
            postings=posting_dtos,
            tags=transaction.tags,
            payee=None,  # TODO: Add payee to Transaction entity
            note=transaction.notes,
            import_batch_id=transaction.import_batch_id,
        )
