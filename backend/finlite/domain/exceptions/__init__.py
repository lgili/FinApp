"""Domain exceptions."""

from finlite.domain.exceptions._exceptions import (
    DomainException,
    AccountException,
    DuplicateAccountError,
    InvalidAccountTypeError,
    AccountNotFoundError,
    TransactionException,
    UnbalancedTransactionError,
    InvalidPostingError,
    TransactionNotFoundError,
    ImportException,
    DuplicateImportError,
    ImportBatchNotFoundError,
    ValidationError,
)

# Alias for consistency with use case naming
AccountAlreadyExistsError = DuplicateAccountError

__all__ = [
    "DomainException",
    "AccountException",
    "DuplicateAccountError",
    "AccountAlreadyExistsError",  # Alias
    "InvalidAccountTypeError",
    "AccountNotFoundError",
    "TransactionException",
    "UnbalancedTransactionError",
    "InvalidPostingError",
    "TransactionNotFoundError",
    "ImportException",
    "DuplicateImportError",
    "ImportBatchNotFoundError",
    "ValidationError",
]
