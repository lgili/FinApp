"""Application-level exceptions.

These are exceptions specific to the application layer (use cases).
They wrap domain exceptions and provide application-specific context.
"""


class ApplicationError(Exception):
    """Base exception for all application-level errors."""
    
    pass


class AccountAlreadyExistsError(ApplicationError):
    """Raised when attempting to create an account that already exists."""
    
    def __init__(self, message: str = "Account already exists"):
        super().__init__(message)
        self.message = message


class AccountNotFoundError(ApplicationError):
    """Raised when an account is not found."""
    
    def __init__(self, account_id_or_code: str):
        super().__init__(f"Account not found: {account_id_or_code}")
        self.account_id_or_code = account_id_or_code


class TransactionNotFoundError(ApplicationError):
    """Raised when a transaction is not found."""
    
    def __init__(self, transaction_id: str):
        super().__init__(f"Transaction not found: {transaction_id}")
        self.transaction_id = transaction_id


class InvalidTransactionError(ApplicationError):
    """Raised when a transaction is invalid (e.g., doesn't balance)."""
    
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class InvalidAccountTypeError(ApplicationError):
    """Raised when an invalid account type is provided."""
    
    def __init__(self, account_type: str):
        super().__init__(f"Invalid account type: {account_type}")
        self.account_type = account_type
