"""Tests for application-level exceptions."""

import pytest

from finlite.application.exceptions import (
    AccountAlreadyExistsError,
    AccountNotFoundError,
    ApplicationError,
    InvalidAccountTypeError,
    InvalidTransactionError,
    TransactionNotFoundError,
)


class TestApplicationError:
    """Tests for base ApplicationError."""

    def test_is_exception(self):
        """ApplicationError is an Exception."""
        error = ApplicationError("test error")
        assert isinstance(error, Exception)

    def test_message(self):
        """ApplicationError stores message."""
        error = ApplicationError("test error")
        assert str(error) == "test error"


class TestAccountAlreadyExistsError:
    """Tests for AccountAlreadyExistsError."""

    def test_default_message(self):
        """Uses default message when none provided."""
        error = AccountAlreadyExistsError()
        assert str(error) == "Account already exists"
        assert error.message == "Account already exists"

    def test_custom_message(self):
        """Uses custom message when provided."""
        error = AccountAlreadyExistsError("Account CASH already exists")
        assert str(error) == "Account CASH already exists"
        assert error.message == "Account CASH already exists"

    def test_is_application_error(self):
        """AccountAlreadyExistsError is an ApplicationError."""
        error = AccountAlreadyExistsError()
        assert isinstance(error, ApplicationError)


class TestAccountNotFoundError:
    """Tests for AccountNotFoundError."""

    def test_message_with_code(self):
        """Formats message with account code."""
        error = AccountNotFoundError("CASH")
        assert str(error) == "Account not found: CASH"
        assert error.account_id_or_code == "CASH"

    def test_message_with_id(self):
        """Formats message with account ID."""
        account_id = "123e4567-e89b-12d3-a456-426614174000"
        error = AccountNotFoundError(account_id)
        assert str(error) == f"Account not found: {account_id}"
        assert error.account_id_or_code == account_id

    def test_is_application_error(self):
        """AccountNotFoundError is an ApplicationError."""
        error = AccountNotFoundError("CASH")
        assert isinstance(error, ApplicationError)


class TestTransactionNotFoundError:
    """Tests for TransactionNotFoundError."""

    def test_message_with_id(self):
        """Formats message with transaction ID."""
        transaction_id = "123e4567-e89b-12d3-a456-426614174000"
        error = TransactionNotFoundError(transaction_id)
        assert str(error) == f"Transaction not found: {transaction_id}"
        assert error.transaction_id == transaction_id

    def test_is_application_error(self):
        """TransactionNotFoundError is an ApplicationError."""
        error = TransactionNotFoundError("some-id")
        assert isinstance(error, ApplicationError)


class TestInvalidTransactionError:
    """Tests for InvalidTransactionError."""

    def test_custom_message(self):
        """Stores custom validation message."""
        error = InvalidTransactionError("Transaction doesn't balance")
        assert str(error) == "Transaction doesn't balance"
        assert error.message == "Transaction doesn't balance"

    def test_unbalanced_message(self):
        """Handles unbalanced transaction message."""
        error = InvalidTransactionError("Sum of postings must be zero, got 100.00")
        assert "Sum of postings must be zero" in str(error)
        assert error.message == "Sum of postings must be zero, got 100.00"

    def test_is_application_error(self):
        """InvalidTransactionError is an ApplicationError."""
        error = InvalidTransactionError("Invalid")
        assert isinstance(error, ApplicationError)


class TestInvalidAccountTypeError:
    """Tests for InvalidAccountTypeError."""

    def test_message_with_type(self):
        """Formats message with invalid account type."""
        error = InvalidAccountTypeError("INVALID")
        assert str(error) == "Invalid account type: INVALID"
        assert error.account_type == "INVALID"

    def test_different_types(self):
        """Handles different invalid types."""
        error1 = InvalidAccountTypeError("REVENUE")
        assert error1.account_type == "REVENUE"

        error2 = InvalidAccountTypeError("DEBIT")
        assert error2.account_type == "DEBIT"

    def test_is_application_error(self):
        """InvalidAccountTypeError is an ApplicationError."""
        error = InvalidAccountTypeError("INVALID")
        assert isinstance(error, ApplicationError)


class TestExceptionRaising:
    """Tests for raising and catching exceptions."""

    def test_raise_account_already_exists(self):
        """Can raise and catch AccountAlreadyExistsError."""
        with pytest.raises(AccountAlreadyExistsError) as exc_info:
            raise AccountAlreadyExistsError("Account CASH exists")

        assert "Account CASH exists" in str(exc_info.value)

    def test_raise_account_not_found(self):
        """Can raise and catch AccountNotFoundError."""
        with pytest.raises(AccountNotFoundError) as exc_info:
            raise AccountNotFoundError("CASH")

        assert "CASH" in str(exc_info.value)

    def test_raise_transaction_not_found(self):
        """Can raise and catch TransactionNotFoundError."""
        with pytest.raises(TransactionNotFoundError) as exc_info:
            raise TransactionNotFoundError("123")

        assert "123" in str(exc_info.value)

    def test_raise_invalid_transaction(self):
        """Can raise and catch InvalidTransactionError."""
        with pytest.raises(InvalidTransactionError) as exc_info:
            raise InvalidTransactionError("Doesn't balance")

        assert "Doesn't balance" in str(exc_info.value)

    def test_raise_invalid_account_type(self):
        """Can raise and catch InvalidAccountTypeError."""
        with pytest.raises(InvalidAccountTypeError) as exc_info:
            raise InvalidAccountTypeError("INVALID")

        assert "INVALID" in str(exc_info.value)

    def test_catch_as_application_error(self):
        """Can catch specific exceptions as ApplicationError."""
        with pytest.raises(ApplicationError):
            raise AccountNotFoundError("CASH")

        with pytest.raises(ApplicationError):
            raise InvalidTransactionError("Test")
