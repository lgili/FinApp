"""
Unit tests for ImportNubankStatement Use Case.

Tests:
- Successful import with valid CSV
- Duplicate file detection (via SHA256)
- Invalid CSV format handling
- Event publishing
- File not found error
"""

import pytest
from datetime import datetime, UTC
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from uuid import uuid4

from finlite.application.use_cases.import_nubank_statement import (
    ImportNubankStatement,
    ImportNubankStatementCommand,
    ImportNubankStatementResult,
)
from finlite.domain.entities.import_batch import ImportBatch, ImportSource, ImportStatus
from finlite.domain.entities.statement_entry import StatementEntry, StatementStatus
from finlite.domain.events.statement_events import StatementImported, StatementImportFailed
from finlite.domain.exceptions import DuplicateImportError


class TestImportNubankStatement:
    """Test suite for ImportNubankStatement use case."""

    def setup_method(self):
        """Setup test fixtures before each test."""
        self.batch_repo = Mock()
        self.entry_repo = Mock()
        self.event_bus = Mock()
        
        self.use_case = ImportNubankStatement(
            import_batch_repository=self.batch_repo,
            statement_entry_repository=self.entry_repo,
            event_bus=self.event_bus,
        )
    
    def test_successful_import_creates_batch_and_entries(self, tmp_path):
        """Test successful import creates batch and entries."""
        # Arrange
        csv_file = tmp_path / "nubank.csv"
        csv_file.write_text(
            "date,description,amount\n"
            "2025-10-01,Salary,1000.00\n"
            "2025-10-02,Coffee,-5.50\n"
        )
        
        # Mock: No duplicate exists
        self.batch_repo.find_by_sha256.return_value = None
        
        # Mock: add() and update() do nothing
        self.batch_repo.add.return_value = None
        self.batch_repo.update.return_value = None
        self.entry_repo.add.return_value = None
        
        # Act
        command = ImportNubankStatementCommand(file_path=csv_file)
        result = self.use_case.execute(command)
        
        # Assert: Batch created
        assert self.batch_repo.add.called
        batch_arg = self.batch_repo.add.call_args[0][0]
        assert isinstance(batch_arg, ImportBatch)
        assert batch_arg.source == ImportSource.NUBANK_CSV
        assert batch_arg.filename == "nubank.csv"
        
        # Assert: Entries created
        assert self.entry_repo.add.call_count == 2
        
        # Assert: Batch marked as completed
        assert self.batch_repo.update.called
        
        # Assert: Event published
        assert self.event_bus.publish.call_count == 1
        event = self.event_bus.publish.call_args[0][0]
        assert isinstance(event, StatementImported)
        assert event.entries_count == 2
        
        # Assert: Result
        assert isinstance(result, ImportNubankStatementResult)
        assert result.entries_count == 2
        assert len(result.file_sha256) == 64  # SHA256 is 64 hex chars
    
    def test_duplicate_file_raises_error(self, tmp_path):
        """Test importing same file twice raises DuplicateImportError."""
        # Arrange
        csv_file = tmp_path / "nubank.csv"
        csv_file.write_text("date,description,amount\n2025-10-01,Test,100.00\n")
        
        # Mock: Duplicate exists
        existing_batch = ImportBatch.create(
            source=ImportSource.NUBANK_CSV,
            filename="nubank.csv",
        )
        self.batch_repo.find_by_sha256.return_value = existing_batch
        
        # Act & Assert
        command = ImportNubankStatementCommand(file_path=csv_file)
        
        with pytest.raises(DuplicateImportError) as exc_info:
            self.use_case.execute(command)
        
        assert str(existing_batch.id) in str(exc_info.value)
        
        # Assert: Failure event published
        assert self.event_bus.publish.called
        event = self.event_bus.publish.call_args[0][0]
        assert isinstance(event, StatementImportFailed)
        assert event.error_type == "duplicate"
    
    def test_file_not_found_raises_error(self):
        """Test importing non-existent file raises FileNotFoundError."""
        # Arrange
        nonexistent_file = Path("/tmp/does_not_exist.csv")
        command = ImportNubankStatementCommand(file_path=nonexistent_file)
        
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            self.use_case.execute(command)
    
    def test_invalid_csv_format_raises_error(self, tmp_path):
        """Test invalid CSV format raises ValueError."""
        # Arrange
        csv_file = tmp_path / "invalid.csv"
        csv_file.write_text("date,description,amount\ninvalid_date,Test,not_a_number\n")
        
        # Mock: No duplicate
        self.batch_repo.find_by_sha256.return_value = None
        self.batch_repo.add.return_value = None
        
        # Act & Assert
        command = ImportNubankStatementCommand(file_path=csv_file)
        
        with pytest.raises(ValueError):
            self.use_case.execute(command)
        
        # Assert: Failure event published
        assert self.event_bus.publish.called
        event = self.event_bus.publish.call_args[0][0]
        assert isinstance(event, StatementImportFailed)
    
    def test_empty_csv_creates_batch_with_zero_entries(self, tmp_path):
        """Test empty CSV (only headers) creates batch with 0 entries."""
        # Arrange
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("date,description,amount\n")  # Only headers
        
        # Mock
        self.batch_repo.find_by_sha256.return_value = None
        self.batch_repo.add.return_value = None
        self.batch_repo.update.return_value = None
        
        # Act
        command = ImportNubankStatementCommand(file_path=csv_file)
        result = self.use_case.execute(command)
        
        # Assert
        assert result.entries_count == 0
        assert self.entry_repo.add.call_count == 0
        
        # Batch should still be created and marked complete
        assert self.batch_repo.add.called
        assert self.batch_repo.update.called
    
    def test_custom_currency_is_applied(self, tmp_path):
        """Test custom currency parameter is applied to entries."""
        # Arrange
        csv_file = tmp_path / "usd.csv"
        csv_file.write_text("date,description,amount\n2025-10-01,Test,100.00\n")
        
        # Mock
        self.batch_repo.find_by_sha256.return_value = None
        self.batch_repo.add.return_value = None
        self.batch_repo.update.return_value = None
        self.entry_repo.add.return_value = None
        
        # Act
        command = ImportNubankStatementCommand(
            file_path=csv_file,
            default_currency="USD",
        )
        result = self.use_case.execute(command)
        
        # Assert: Entry has USD currency
        entry_arg = self.entry_repo.add.call_args[0][0]
        assert entry_arg.currency == "USD"
    
    def test_account_hint_is_stored_in_metadata(self, tmp_path):
        """Test account_hint is stored in entry metadata."""
        # Arrange
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("date,description,amount\n2025-10-01,Test,100.00\n")
        
        # Mock
        self.batch_repo.find_by_sha256.return_value = None
        self.batch_repo.add.return_value = None
        self.batch_repo.update.return_value = None
        self.entry_repo.add.return_value = None
        
        # Act
        command = ImportNubankStatementCommand(
            file_path=csv_file,
            account_hint="Assets:Nubank",
        )
        result = self.use_case.execute(command)
        
        # Assert: Entry metadata contains account_hint
        entry_arg = self.entry_repo.add.call_args[0][0]
        assert entry_arg.metadata["account_hint"] == "Assets:Nubank"
    
    @patch("finlite.application.use_cases.import_nubank_statement.sha256_file")
    def test_sha256_is_calculated_correctly(self, mock_sha256, tmp_path):
        """Test SHA256 hash is calculated for the file."""
        # Arrange
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("date,description,amount\n2025-10-01,Test,100.00\n")
        
        mock_sha256.return_value = "abc123def456" * 5  # 64 chars
        
        # Mock
        self.batch_repo.find_by_sha256.return_value = None
        self.batch_repo.add.return_value = None
        self.batch_repo.update.return_value = None
        self.entry_repo.add.return_value = None
        
        # Act
        command = ImportNubankStatementCommand(file_path=csv_file)
        result = self.use_case.execute(command)
        
        # Assert
        mock_sha256.assert_called_once_with(csv_file)
        assert self.batch_repo.find_by_sha256.called
        assert result.file_sha256 == "abc123def456" * 5
    
    def test_batch_status_transitions(self, tmp_path):
        """Test batch status transitions from PENDING to COMPLETED."""
        # Arrange
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("date,description,amount\n2025-10-01,Test,100.00\n")
        
        # Capture batch status at call time
        batch_status_at_add = None
        def capture_add_status(batch):
            nonlocal batch_status_at_add
            batch_status_at_add = batch.status
        
        # Mock
        self.batch_repo.find_by_sha256.return_value = None
        self.batch_repo.add.side_effect = capture_add_status
        self.batch_repo.update.return_value = None
        self.entry_repo.add.return_value = None
        
        # Act
        command = ImportNubankStatementCommand(file_path=csv_file)
        result = self.use_case.execute(command)
        
        # Assert: Batch created with PENDING status
        assert batch_status_at_add == ImportStatus.PENDING
        
        # Assert: Batch updated to COMPLETED
        updated_batch = self.batch_repo.update.call_args[0][0]
        assert updated_batch.status == ImportStatus.COMPLETED
        assert updated_batch.transaction_count == 1
