"""Record Transaction Use Case."""

from dataclasses import dataclass
from uuid import UUID

from finlite.application.dtos import CreateTransactionDTO, TransactionDTO, PostingDTO
from finlite.domain.entities import Transaction
from finlite.domain.exceptions import AccountNotFoundError, UnbalancedTransactionError
from finlite.domain.repositories import IUnitOfWork
from finlite.domain.value_objects import Posting, Money


@dataclass
class RecordTransactionResult:
    """Result of transaction recording."""

    transaction: TransactionDTO
    recorded: bool  # Always True for successful recording


class RecordTransactionUseCase:
    """Use case for recording a new transaction.

    This use case:
    1. Validates all accounts exist
    2. Validates transaction is balanced
    3. Creates transaction entity with postings
    4. Persists transaction
    """

    def __init__(self, uow: IUnitOfWork) -> None:
        """Initialize use case with unit of work.

        Args:
            uow: Unit of work for transaction management
        """
        self._uow = uow

    def execute(self, dto: CreateTransactionDTO) -> RecordTransactionResult:
        """Execute the use case.

        Args:
            dto: Transaction creation data

        Returns:
            RecordTransactionResult with the recorded transaction

        Raises:
            AccountNotFoundError: If any account doesn't exist
            UnbalancedTransactionError: If transaction is not balanced
            ValueError: If transaction data is invalid
        """
        with self._uow:
            # Validate all accounts exist and build account_id map
            account_map = {}  # code -> account
            for posting_dto in dto.postings:
                account = self._uow.accounts.find_by_code(posting_dto.account_code)
                if not account:
                    raise AccountNotFoundError(
                        f"Account '{posting_dto.account_code}' not found"
                    )
                account_map[posting_dto.account_code] = account

            # Create postings with account IDs
            postings = []
            for posting_dto in dto.postings:
                account = account_map[posting_dto.account_code]
                posting = Posting(
                    account_id=account.id,
                    amount=Money(
                        posting_dto.amount,
                        posting_dto.currency,
                    ),
                )
                postings.append(posting)

            # Create transaction entity (validates balance automatically)
            transaction = Transaction.create(
                date=dto.date,
                description=dto.description,
                postings=postings,
                tags=list(dto.tags) if dto.tags else None,
                notes=dto.note,
                import_batch_id=dto.import_batch_id,
            )

            # Persist transaction
            saved_transaction = self._uow.transactions.add(transaction)
            self._uow.commit()

            # Convert to DTO
            transaction_dto = self._to_dto(saved_transaction, account_map)

            return RecordTransactionResult(
                transaction=transaction_dto,
                recorded=True,
            )

    def _to_dto(
        self, transaction: Transaction, account_map: dict[str, any]
    ) -> TransactionDTO:
        """Convert domain entity to DTO.

        Args:
            transaction: Domain transaction entity
            account_map: Map of account codes to accounts

        Returns:
            Transaction DTO
        """
        # Build reverse map: account_id -> account_code
        id_to_code = {acc.id: code for code, acc in account_map.items()}

        posting_dtos = tuple(
            PostingDTO(
                account_code=id_to_code.get(p.account_id, "UNKNOWN"),
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
