"""Tests for AccountType value object."""

import pytest

from finlite.domain.value_objects.account_type import AccountType


class TestAccountTypeEnum:
    """Tests for AccountType enum values."""

    def test_all_types_exist(self):
        """All five account types are defined."""
        assert AccountType.ASSET.value == "ASSET"
        assert AccountType.LIABILITY.value == "LIABILITY"
        assert AccountType.EQUITY.value == "EQUITY"
        assert AccountType.INCOME.value == "INCOME"
        assert AccountType.EXPENSE.value == "EXPENSE"

    def test_is_string_enum(self):
        """AccountType inherits from str."""
        assert isinstance(AccountType.ASSET, str)
        assert isinstance(AccountType.INCOME, str)

    def test_enum_equality(self):
        """Enum values are equal to their string values."""
        assert AccountType.ASSET == "ASSET"
        assert AccountType.LIABILITY == "LIABILITY"


class TestIsDebitPositive:
    """Tests for is_debit_positive method."""

    def test_asset_is_debit_positive(self):
        """ASSET accounts have debit positive nature."""
        assert AccountType.ASSET.is_debit_positive() is True

    def test_expense_is_debit_positive(self):
        """EXPENSE accounts have debit positive nature."""
        assert AccountType.EXPENSE.is_debit_positive() is True

    def test_liability_is_not_debit_positive(self):
        """LIABILITY accounts have credit positive nature."""
        assert AccountType.LIABILITY.is_debit_positive() is False

    def test_equity_is_not_debit_positive(self):
        """EQUITY accounts have credit positive nature."""
        assert AccountType.EQUITY.is_debit_positive() is False

    def test_income_is_not_debit_positive(self):
        """INCOME accounts have credit positive nature."""
        assert AccountType.INCOME.is_debit_positive() is False


class TestIsCreditPositive:
    """Tests for is_credit_positive method."""

    def test_liability_is_credit_positive(self):
        """LIABILITY accounts have credit positive nature."""
        assert AccountType.LIABILITY.is_credit_positive() is True

    def test_equity_is_credit_positive(self):
        """EQUITY accounts have credit positive nature."""
        assert AccountType.EQUITY.is_credit_positive() is True

    def test_income_is_credit_positive(self):
        """INCOME accounts have credit positive nature."""
        assert AccountType.INCOME.is_credit_positive() is True

    def test_asset_is_not_credit_positive(self):
        """ASSET accounts have debit positive nature."""
        assert AccountType.ASSET.is_credit_positive() is False

    def test_expense_is_not_credit_positive(self):
        """EXPENSE accounts have debit positive nature."""
        assert AccountType.EXPENSE.is_credit_positive() is False

    def test_inverse_of_debit_positive(self):
        """is_credit_positive is inverse of is_debit_positive."""
        for account_type in AccountType:
            assert account_type.is_credit_positive() == (
                not account_type.is_debit_positive()
            )


class TestIsBalanceSheetAccount:
    """Tests for is_balance_sheet_account method."""

    def test_asset_is_balance_sheet(self):
        """ASSET is a balance sheet account."""
        assert AccountType.ASSET.is_balance_sheet_account() is True

    def test_liability_is_balance_sheet(self):
        """LIABILITY is a balance sheet account."""
        assert AccountType.LIABILITY.is_balance_sheet_account() is True

    def test_equity_is_balance_sheet(self):
        """EQUITY is a balance sheet account."""
        assert AccountType.EQUITY.is_balance_sheet_account() is True

    def test_income_is_not_balance_sheet(self):
        """INCOME is not a balance sheet account."""
        assert AccountType.INCOME.is_balance_sheet_account() is False

    def test_expense_is_not_balance_sheet(self):
        """EXPENSE is not a balance sheet account."""
        assert AccountType.EXPENSE.is_balance_sheet_account() is False


class TestIsIncomeStatementAccount:
    """Tests for is_income_statement_account method."""

    def test_income_is_income_statement(self):
        """INCOME is an income statement account."""
        assert AccountType.INCOME.is_income_statement_account() is True

    def test_expense_is_income_statement(self):
        """EXPENSE is an income statement account."""
        assert AccountType.EXPENSE.is_income_statement_account() is True

    def test_asset_is_not_income_statement(self):
        """ASSET is not an income statement account."""
        assert AccountType.ASSET.is_income_statement_account() is False

    def test_liability_is_not_income_statement(self):
        """LIABILITY is not an income statement account."""
        assert AccountType.LIABILITY.is_income_statement_account() is False

    def test_equity_is_not_income_statement(self):
        """EQUITY is not an income statement account."""
        assert AccountType.EQUITY.is_income_statement_account() is False

    def test_mutually_exclusive_with_balance_sheet(self):
        """Account cannot be both balance sheet and income statement."""
        for account_type in AccountType:
            is_balance = account_type.is_balance_sheet_account()
            is_income = account_type.is_income_statement_account()
            # XOR: exactly one must be true
            assert is_balance != is_income


class TestGetSignMultiplier:
    """Tests for get_sign_multiplier method."""

    def test_asset_multiplier_is_positive(self):
        """ASSET has +1 multiplier."""
        assert AccountType.ASSET.get_sign_multiplier() == 1

    def test_expense_multiplier_is_positive(self):
        """EXPENSE has +1 multiplier."""
        assert AccountType.EXPENSE.get_sign_multiplier() == 1

    def test_liability_multiplier_is_negative(self):
        """LIABILITY has -1 multiplier."""
        assert AccountType.LIABILITY.get_sign_multiplier() == -1

    def test_equity_multiplier_is_negative(self):
        """EQUITY has -1 multiplier."""
        assert AccountType.EQUITY.get_sign_multiplier() == -1

    def test_income_multiplier_is_negative(self):
        """INCOME has -1 multiplier."""
        assert AccountType.INCOME.get_sign_multiplier() == -1

    def test_multiplier_matches_debit_nature(self):
        """Multiplier is +1 for debit positive, -1 for credit positive."""
        for account_type in AccountType:
            expected = 1 if account_type.is_debit_positive() else -1
            assert account_type.get_sign_multiplier() == expected


class TestFromString:
    """Tests for from_string class method."""

    def test_uppercase_string(self):
        """Converts uppercase string to AccountType."""
        assert AccountType.from_string("ASSET") == AccountType.ASSET
        assert AccountType.from_string("LIABILITY") == AccountType.LIABILITY
        assert AccountType.from_string("EQUITY") == AccountType.EQUITY
        assert AccountType.from_string("INCOME") == AccountType.INCOME
        assert AccountType.from_string("EXPENSE") == AccountType.EXPENSE

    def test_lowercase_string(self):
        """Converts lowercase string to AccountType (case insensitive)."""
        assert AccountType.from_string("asset") == AccountType.ASSET
        assert AccountType.from_string("liability") == AccountType.LIABILITY
        assert AccountType.from_string("equity") == AccountType.EQUITY

    def test_mixed_case_string(self):
        """Converts mixed case string to AccountType."""
        assert AccountType.from_string("Asset") == AccountType.ASSET
        assert AccountType.from_string("LiAbIlItY") == AccountType.LIABILITY

    def test_invalid_string_raises_error(self):
        """Raises ValueError for invalid account type."""
        with pytest.raises(ValueError) as exc_info:
            AccountType.from_string("INVALID")

        assert "Invalid account type" in str(exc_info.value)
        assert "INVALID" in str(exc_info.value)

    def test_error_message_shows_valid_types(self):
        """Error message lists all valid account types."""
        with pytest.raises(ValueError) as exc_info:
            AccountType.from_string("DEBIT")

        error_msg = str(exc_info.value)
        assert "ASSET" in error_msg
        assert "LIABILITY" in error_msg
        assert "EQUITY" in error_msg
        assert "INCOME" in error_msg
        assert "EXPENSE" in error_msg

    def test_empty_string_raises_error(self):
        """Raises ValueError for empty string."""
        with pytest.raises(ValueError):
            AccountType.from_string("")

    def test_whitespace_string_raises_error(self):
        """Raises ValueError for whitespace string."""
        with pytest.raises(ValueError):
            AccountType.from_string("   ")


class TestStringRepresentation:
    """Tests for __str__ and __repr__ methods."""

    def test_str_returns_value(self):
        """__str__ returns the enum value."""
        assert str(AccountType.ASSET) == "ASSET"
        assert str(AccountType.LIABILITY) == "LIABILITY"
        assert str(AccountType.INCOME) == "INCOME"

    def test_repr_format(self):
        """__repr__ returns technical representation."""
        assert repr(AccountType.ASSET) == "<AccountType.ASSET: 'ASSET'>"
        assert repr(AccountType.LIABILITY) == "<AccountType.LIABILITY: 'LIABILITY'>"
        assert repr(AccountType.INCOME) == "<AccountType.INCOME: 'INCOME'>"


class TestAccountingRules:
    """Integration tests for double-entry accounting rules."""

    def test_fundamental_equation_accounts(self):
        """ASSET = LIABILITY + EQUITY accounts."""
        # Asset side of equation
        assert AccountType.ASSET.is_debit_positive()

        # Liability and Equity side
        assert AccountType.LIABILITY.is_credit_positive()
        assert AccountType.EQUITY.is_credit_positive()

    def test_profit_equation_accounts(self):
        """PROFIT = INCOME - EXPENSE accounts."""
        # Income increases profit (credit positive)
        assert AccountType.INCOME.is_credit_positive()

        # Expense decreases profit (debit positive)
        assert AccountType.EXPENSE.is_debit_positive()

    def test_balance_sheet_vs_income_statement(self):
        """Accounts are classified into two financial statements."""
        balance_sheet = [
            AccountType.ASSET,
            AccountType.LIABILITY,
            AccountType.EQUITY,
        ]
        income_statement = [AccountType.INCOME, AccountType.EXPENSE]

        for acc_type in balance_sheet:
            assert acc_type.is_balance_sheet_account()
            assert not acc_type.is_income_statement_account()

        for acc_type in income_statement:
            assert acc_type.is_income_statement_account()
            assert not acc_type.is_balance_sheet_account()
