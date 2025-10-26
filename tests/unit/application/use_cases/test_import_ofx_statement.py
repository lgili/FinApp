"""Tests for ImportOFXStatement use case."""

from datetime import datetime, UTC
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock
import pytest

from finlite.application.use_cases.import_ofx_statement import (
    ImportOFXStatement,
    ImportOFXStatementCommand,
    ImportOFXStatementResult,
)
from finlite.domain.entities.import_batch import ImportBatch, ImportSource, ImportStatus
from finlite.domain.exceptions import DuplicateImportError


class TestImportOFXStatement:
    """Unit tests for OFX import use case."""

    @pytest.fixture
    def mock_batch_repo(self) -> Mock:
        """Provide a mock import batch repository."""
        return Mock()

    @pytest.fixture
    def mock_entry_repo(self) -> Mock:
        """Provide a mock statement entry repository."""
        return Mock()

    @pytest.fixture
    def mock_event_bus(self) -> Mock:
        """Provide a mock event bus."""
        return Mock()

    @pytest.fixture
    def use_case(
        self,
        mock_batch_repo: Mock,
        mock_entry_repo: Mock,
        mock_event_bus: Mock,
    ) -> ImportOFXStatement:
        """Construct the use case with mocked dependencies."""
        return ImportOFXStatement(
            import_batch_repository=mock_batch_repo,
            statement_entry_repository=mock_entry_repo,
            event_bus=mock_event_bus,
        )

    @pytest.fixture
    def sample_ofx_file(self, tmp_path: Path) -> Path:
        """Create a temporary OFX file for testing."""
        ofx_content = """OFXHEADER:100
DATA:OFXSGML
VERSION:102
SECURITY:NONE
ENCODING:USASCII
CHARSET:1252
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE

<OFX>
<BANKMSGSRSV1>
<STMTTRNRS>
<STMTRS>
<CURDEF>USD
<BANKTRANLIST>
<STMTTRN>
<DTPOSTED>20251015120000
<TRNAMT>-100.50
<FITID>TXN001
<NAME>Test Store
<MEMO>Test purchase
</STMTTRN>
<STMTTRN>
<DTPOSTED>20251020120000
<TRNAMT>1000.00
<FITID>TXN002
<NAME>Employer
<MEMO>Salary
</STMTTRN>
</BANKTRANLIST>
</STMTRS>
</STMTTRNRS>
</BANKMSGSRSV1>
</OFX>
"""
        file_path = tmp_path / "test_statement.ofx"
        file_path.write_text(ofx_content)
        return file_path

    def test_import_ofx_success(
        self,
        use_case: ImportOFXStatement,
        sample_ofx_file: Path,
        mock_batch_repo: Mock,
        mock_entry_repo: Mock,
        mock_event_bus: Mock,
    ) -> None:
        """Successfully import OFX file creates batch and entries."""
        # Setup: No duplicate exists
        mock_batch_repo.find_by_sha256.return_value = None

        # Execute
        command = ImportOFXStatementCommand(
            file_path=sample_ofx_file,
            default_currency="USD",
            account_hint="Assets:Bank",
        )
        result = use_case.execute(command)

        # Verify result
        assert isinstance(result, ImportOFXStatementResult)
        assert result.entries_count == 2
        assert len(result.file_sha256) == 64  # SHA256 hash length

        # Verify repository calls
        assert mock_batch_repo.add.call_count == 1
        assert mock_batch_repo.update.call_count == 1
        assert mock_entry_repo.add.call_count == 2

        # Verify batch creation
        created_batch = mock_batch_repo.add.call_args[0][0]
        assert isinstance(created_batch, ImportBatch)
        assert created_batch.source == ImportSource.OFX
        assert created_batch.filename == sample_ofx_file.name

        # Verify event published
        assert mock_event_bus.publish.call_count == 1

    def test_import_duplicate_file_rejected(
        self,
        use_case: ImportOFXStatement,
        sample_ofx_file: Path,
        mock_batch_repo: Mock,
        mock_entry_repo: Mock,
        mock_event_bus: Mock,
    ) -> None:
        """Importing the same file twice raises DuplicateImportError."""
        # Setup: File already imported
        existing_batch = ImportBatch.create(
            source=ImportSource.OFX,
            filename=sample_ofx_file.name,
            file_sha256="existing_hash",
        )
        mock_batch_repo.find_by_sha256.return_value = existing_batch

        # Execute & Assert
        command = ImportOFXStatementCommand(file_path=sample_ofx_file)
        with pytest.raises(DuplicateImportError):
            use_case.execute(command)

        # Verify no entries were created
        assert mock_entry_repo.add.call_count == 0

        # Verify failure event was published
        assert mock_event_bus.publish.call_count == 1

    def test_import_nonexistent_file_raises_error(
        self,
        use_case: ImportOFXStatement,
    ) -> None:
        """Importing a non-existent file raises FileNotFoundError."""
        command = ImportOFXStatementCommand(
            file_path=Path("/nonexistent/file.ofx")
        )

        with pytest.raises(FileNotFoundError):
            use_case.execute(command)

    def test_parse_ofx_datetime(
        self,
        use_case: ImportOFXStatement,
    ) -> None:
        """OFX datetime strings are correctly parsed."""
        # Standard format: YYYYMMDDHHMMSS
        dt = use_case._parse_ofx_datetime("20251015143000")
        assert dt.year == 2025
        assert dt.month == 10
        assert dt.day == 15
        assert dt.hour == 14
        assert dt.minute == 30
        assert dt.second == 0
        assert dt.tzinfo == UTC

        # With timezone (should be ignored)
        dt = use_case._parse_ofx_datetime("20251015143000[+5:EST]")
        assert dt.year == 2025
        assert dt.tzinfo == UTC

    def test_parse_ofx_datetime_invalid_fallback(
        self,
        use_case: ImportOFXStatement,
    ) -> None:
        """Invalid datetime falls back to current time."""
        dt = use_case._parse_ofx_datetime("invalid")
        assert isinstance(dt, datetime)
        assert dt.tzinfo == UTC

    def test_extract_transactions_with_header_currency(
        self,
        use_case: ImportOFXStatement,
    ) -> None:
        """Transactions inherit currency from header CURDEF."""
        ofx_text = """
<OFX>
<CURDEF>BRL
<STMTTRN>
<DTPOSTED>20251015120000
<TRNAMT>100.00
<FITID>TXN001
<NAME>Test
</STMTTRN>
</OFX>
"""
        transactions = use_case._extract_transactions(ofx_text, "USD")

        assert len(transactions) == 1
        assert transactions[0]["CURRENCY"] == "BRL"

    def test_extract_transactions_with_transaction_currency(
        self,
        use_case: ImportOFXStatement,
    ) -> None:
        """Transaction-level currency overrides header currency."""
        ofx_text = """
<OFX>
<CURDEF>BRL
<STMTTRN>
<DTPOSTED>20251015120000
<TRNAMT>100.00
<FITID>TXN001
<NAME>Test
<CURRENCY>EUR
</STMTTRN>
</OFX>
"""
        transactions = use_case._extract_transactions(ofx_text, "USD")

        assert len(transactions) == 1
        assert transactions[0]["CURRENCY"] == "EUR"

    def test_extract_transactions_uses_default_currency(
        self,
        use_case: ImportOFXStatement,
    ) -> None:
        """Transactions use default currency when no CURDEF or CURRENCY."""
        ofx_text = """
<OFX>
<STMTTRN>
<DTPOSTED>20251015120000
<TRNAMT>100.00
<FITID>TXN001
<NAME>Test
</STMTTRN>
</OFX>
"""
        transactions = use_case._extract_transactions(ofx_text, "JPY")

        assert len(transactions) == 1
        assert transactions[0]["CURRENCY"] == "JPY"

    def test_create_entry_with_fitid(
        self,
        use_case: ImportOFXStatement,
    ) -> None:
        """Entry uses FITID as external_id when available."""
        from uuid import uuid4

        transaction = {
            "DTPOSTED": "20251015120000",
            "TRNAMT": "-50.25",
            "FITID": "BANK-TXN-12345",
            "NAME": "Store",
            "MEMO": "Purchase",
            "CURRENCY": "USD",
        }

        entry = use_case._create_entry(
            transaction=transaction,
            batch_id=uuid4(),
            file_name="statement.ofx",
            row_index=1,
            default_currency="USD",
            account_hint=None,
        )

        assert entry.external_id == "BANK-TXN-12345"
        assert entry.amount == Decimal("-50.25")
        assert entry.payee == "Store"
        assert entry.memo == "Store - Purchase"

    def test_create_entry_without_fitid_uses_fallback(
        self,
        use_case: ImportOFXStatement,
    ) -> None:
        """Entry uses filename:row:index when FITID not available."""
        from uuid import uuid4

        transaction = {
            "DTPOSTED": "20251015120000",
            "TRNAMT": "100.00",
            "NAME": "Employer",
            "MEMO": "Salary",
            "CURRENCY": "USD",
        }

        entry = use_case._create_entry(
            transaction=transaction,
            batch_id=uuid4(),
            file_name="statement.ofx",
            row_index=5,
            default_currency="USD",
            account_hint=None,
        )

        assert entry.external_id == "statement.ofx:row:5"

    def test_create_entry_combines_name_and_memo(
        self,
        use_case: ImportOFXStatement,
    ) -> None:
        """Entry memo combines NAME and MEMO fields."""
        from uuid import uuid4

        # Both NAME and MEMO
        transaction1 = {
            "DTPOSTED": "20251015120000",
            "TRNAMT": "100.00",
            "FITID": "TXN1",
            "NAME": "Store",
            "MEMO": "Purchase",
            "CURRENCY": "USD",
        }
        entry1 = use_case._create_entry(
            transaction=transaction1,
            batch_id=uuid4(),
            file_name="test.ofx",
            row_index=1,
            default_currency="USD",
            account_hint=None,
        )
        assert entry1.memo == "Store - Purchase"
        assert entry1.payee == "Store"

        # Only NAME
        transaction2 = {
            "DTPOSTED": "20251015120000",
            "TRNAMT": "100.00",
            "FITID": "TXN2",
            "NAME": "Store",
            "CURRENCY": "USD",
        }
        entry2 = use_case._create_entry(
            transaction=transaction2,
            batch_id=uuid4(),
            file_name="test.ofx",
            row_index=2,
            default_currency="USD",
            account_hint=None,
        )
        assert entry2.memo == "Store"
        assert entry2.payee == "Store"

        # Only MEMO
        transaction3 = {
            "DTPOSTED": "20251015120000",
            "TRNAMT": "100.00",
            "FITID": "TXN3",
            "MEMO": "Purchase",
            "CURRENCY": "USD",
        }
        entry3 = use_case._create_entry(
            transaction=transaction3,
            batch_id=uuid4(),
            file_name="test.ofx",
            row_index=3,
            default_currency="USD",
            account_hint=None,
        )
        assert entry3.memo == "Purchase"
        assert entry3.payee is None

    def test_read_ofx_file_handles_encoding(
        self,
        use_case: ImportOFXStatement,
        tmp_path: Path,
    ) -> None:
        """OFX files are read with UTF-8, fallback to Latin-1."""
        # UTF-8 file
        utf8_file = tmp_path / "utf8.ofx"
        utf8_file.write_text("Test UTF-8 content", encoding="utf-8")
        content = use_case._read_ofx_file(utf8_file)
        assert content == "Test UTF-8 content"

        # Latin-1 file
        latin1_file = tmp_path / "latin1.ofx"
        latin1_file.write_bytes(b"Test \xe9 content")  # é in Latin-1
        content = use_case._read_ofx_file(latin1_file)
        assert "Test" in content
