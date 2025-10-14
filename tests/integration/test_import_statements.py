"""
Integration tests for Import Statement functionality.

Tests end-to-end flow:
1. Import Nubank CSV → verify batch and entries in database
2. Reimport same file → verify deduplication works
3. Import different file → verify both batches exist
4. Query entries by batch → verify data integrity
"""

import pytest
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from finlite.application.use_cases.import_nubank_statement import (
    ImportNubankStatement,
    ImportNubankStatementCommand,
)
from finlite.domain.entities.import_batch import ImportSource, ImportStatus
from finlite.domain.entities.statement_entry import StatementStatus
from finlite.domain.exceptions import DuplicateImportError
from finlite.shared.di import create_container, init_database


class TestImportStatementsIntegration:
    """Integration tests for statement import with real database."""

    @pytest.fixture
    def container(self, tmp_path):
        """Create container with in-memory database."""
        db_path = tmp_path / "test.db"
        container = create_container(f"sqlite:///{db_path}", echo=False)
        init_database(container)
        return container
    
    @pytest.fixture
    def nubank_csv(self, tmp_path):
        """Create a sample Nubank CSV file."""
        csv_file = tmp_path / "nubank-2025-10.csv"
        csv_content = """date,description,amount,id
2025-10-01,Salary,5000.00,SAL-001
2025-10-02,Supermarket,-250.50,SUP-001
2025-10-03,Coffee Shop,-12.00,COF-001
2025-10-05,Restaurant,-85.75,RES-001
"""
        csv_file.write_text(csv_content)
        return csv_file
    
    @pytest.fixture
    def another_csv(self, tmp_path):
        """Create a different CSV file."""
        csv_file = tmp_path / "nubank-2025-11.csv"
        csv_content = """date,description,amount,id
2025-11-01,Rent,-2000.00,RENT-001
2025-11-05,Utilities,-300.00,UTIL-001
"""
        csv_file.write_text(csv_content)
        return csv_file
    
    def test_import_creates_batch_and_entries_in_database(self, container, nubank_csv):
        """Test that import creates batch and entries persisted in database."""
        # Arrange
        use_case: ImportNubankStatement = container.import_nubank_statement_use_case()
        batch_repo = container.import_batch_repository()
        entry_repo = container.statement_entry_repository()
        
        # Act
        command = ImportNubankStatementCommand(file_path=nubank_csv)
        result = use_case.execute(command)
        
        # Assert: Batch exists in database
        batch = batch_repo.get(result.batch_id)
        assert batch is not None
        assert batch.source == ImportSource.NUBANK_CSV
        assert batch.status == ImportStatus.COMPLETED
        assert batch.filename == "nubank-2025-10.csv"
        assert batch.transaction_count == 4
        assert batch.file_sha256 is not None
        assert len(batch.file_sha256) == 64
        
        # Assert: Entries exist in database
        entries = entry_repo.find_by_batch(result.batch_id)
        assert len(entries) == 4
        
        # Assert: First entry data
        salary_entry = next(e for e in entries if "Salary" in (e.memo or ""))
        assert salary_entry.external_id == "SAL-001"
        assert salary_entry.amount == Decimal("5000.00")
        assert salary_entry.currency == "BRL"
        assert salary_entry.status == StatementStatus.IMPORTED
        assert salary_entry.occurred_at.year == 2025
        assert salary_entry.occurred_at.month == 10
        assert salary_entry.occurred_at.day == 1
        
        # Assert: Negative amount entry
        coffee_entry = next(e for e in entries if "Coffee" in (e.memo or ""))
        assert coffee_entry.amount == Decimal("-12.00")
    
    def test_reimporting_same_file_raises_duplicate_error(self, container, nubank_csv):
        """Test that reimporting the same file raises DuplicateImportError."""
        # Arrange
        use_case: ImportNubankStatement = container.import_nubank_statement_use_case()
        batch_repo = container.import_batch_repository()
        
        # Act: First import
        command = ImportNubankStatementCommand(file_path=nubank_csv)
        result1 = use_case.execute(command)
        
        # Assert: First import successful
        batch1 = batch_repo.get(result1.batch_id)
        assert batch1.status == ImportStatus.COMPLETED
        
        # Act & Assert: Second import raises error
        with pytest.raises(DuplicateImportError) as exc_info:
            use_case.execute(command)
        
        assert str(result1.batch_id) in str(exc_info.value)
        
        # Assert: Only one batch exists
        all_batches = batch_repo.list_all()
        assert len(all_batches) == 1
    
    def test_importing_different_files_creates_multiple_batches(
        self, container, nubank_csv, another_csv
    ):
        """Test that importing different files creates separate batches."""
        # Arrange
        use_case: ImportNubankStatement = container.import_nubank_statement_use_case()
        batch_repo = container.import_batch_repository()
        entry_repo = container.statement_entry_repository()
        
        # Act: Import first file
        command1 = ImportNubankStatementCommand(file_path=nubank_csv)
        result1 = use_case.execute(command1)
        
        # Act: Import second file
        command2 = ImportNubankStatementCommand(file_path=another_csv)
        result2 = use_case.execute(command2)
        
        # Assert: Two different batches
        assert result1.batch_id != result2.batch_id
        assert result1.file_sha256 != result2.file_sha256
        
        # Assert: First batch
        batch1 = batch_repo.get(result1.batch_id)
        assert batch1.transaction_count == 4
        entries1 = entry_repo.find_by_batch(result1.batch_id)
        assert len(entries1) == 4
        
        # Assert: Second batch
        batch2 = batch_repo.get(result2.batch_id)
        assert batch2.transaction_count == 2
        entries2 = entry_repo.find_by_batch(result2.batch_id)
        assert len(entries2) == 2
        
        # Assert: Total
        all_batches = batch_repo.list_all()
        assert len(all_batches) == 2
    
    def test_find_by_sha256_returns_existing_batch(self, container, nubank_csv):
        """Test that find_by_sha256 correctly identifies duplicate files."""
        # Arrange
        use_case: ImportNubankStatement = container.import_nubank_statement_use_case()
        batch_repo = container.import_batch_repository()
        
        # Act: Import file
        command = ImportNubankStatementCommand(file_path=nubank_csv)
        result = use_case.execute(command)
        
        # Assert: Can find by SHA256
        found_batch = batch_repo.find_by_sha256(result.file_sha256)
        assert found_batch is not None
        assert found_batch.id == result.batch_id
        assert found_batch.filename == "nubank-2025-10.csv"
        
        # Assert: Non-existent SHA256 returns None
        fake_sha256 = "0" * 64
        not_found = batch_repo.find_by_sha256(fake_sha256)
        assert not_found is None
    
    def test_entries_have_correct_status_and_timestamps(self, container, nubank_csv):
        """Test that entries are created with correct status and timestamps."""
        # Arrange
        use_case: ImportNubankStatement = container.import_nubank_statement_use_case()
        entry_repo = container.statement_entry_repository()
        
        # Act
        before_import = datetime.utcnow()
        command = ImportNubankStatementCommand(file_path=nubank_csv)
        result = use_case.execute(command)
        after_import = datetime.utcnow()
        
        # Assert: All entries have IMPORTED status
        entries = entry_repo.find_by_batch(result.batch_id)
        for entry in entries:
            assert entry.status == StatementStatus.IMPORTED
            assert entry.transaction_id is None  # Not yet matched
            assert entry.created_at >= before_import
            assert entry.created_at <= after_import
            assert entry.updated_at >= before_import
            assert entry.updated_at <= after_import
    
    def test_find_pending_entries_returns_imported_entries(self, container, nubank_csv):
        """Test that find_pending returns entries in IMPORTED status."""
        # Arrange
        use_case: ImportNubankStatement = container.import_nubank_statement_use_case()
        entry_repo = container.statement_entry_repository()
        
        # Act
        command = ImportNubankStatementCommand(file_path=nubank_csv)
        result = use_case.execute(command)
        
        # Assert: find_pending returns all entries
        pending = entry_repo.find_pending()
        batch_entries = [e for e in pending if e.batch_id == result.batch_id]
        assert len(batch_entries) == 4
        
        for entry in batch_entries:
            assert entry.status == StatementStatus.IMPORTED
    
    def test_batch_status_filtering(self, container, nubank_csv, another_csv):
        """Test filtering batches by status."""
        # Arrange
        use_case: ImportNubankStatement = container.import_nubank_statement_use_case()
        batch_repo = container.import_batch_repository()
        
        # Act: Import both files
        command1 = ImportNubankStatementCommand(file_path=nubank_csv)
        result1 = use_case.execute(command1)
        
        command2 = ImportNubankStatementCommand(file_path=another_csv)
        result2 = use_case.execute(command2)
        
        # Assert: Both completed
        completed_batches = batch_repo.find_by_status(ImportStatus.COMPLETED)
        assert len(completed_batches) >= 2
        batch_ids = [b.id for b in completed_batches]
        assert result1.batch_id in batch_ids
        assert result2.batch_id in batch_ids
        
        # Assert: No pending batches (all completed successfully)
        pending_batches = batch_repo.find_by_status(ImportStatus.PENDING)
        # Filter only our test batches
        test_pending = [b for b in pending_batches if b.id in [result1.batch_id, result2.batch_id]]
        assert len(test_pending) == 0
    
    def test_custom_currency_persists_to_database(self, container, tmp_path):
        """Test that custom currency is persisted correctly."""
        # Arrange
        csv_file = tmp_path / "usd.csv"
        csv_file.write_text("date,description,amount\n2025-10-01,Test,100.00\n")
        
        use_case: ImportNubankStatement = container.import_nubank_statement_use_case()
        entry_repo = container.statement_entry_repository()
        
        # Act
        command = ImportNubankStatementCommand(
            file_path=csv_file,
            default_currency="USD",
        )
        result = use_case.execute(command)
        
        # Assert
        entries = entry_repo.find_by_batch(result.batch_id)
        assert len(entries) == 1
        assert entries[0].currency == "USD"
    
    def test_account_hint_persists_in_metadata(self, container, tmp_path):
        """Test that account hint is persisted in entry metadata."""
        # Arrange
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("date,description,amount\n2025-10-01,Test,100.00\n")
        
        use_case: ImportNubankStatement = container.import_nubank_statement_use_case()
        entry_repo = container.statement_entry_repository()
        
        # Act
        command = ImportNubankStatementCommand(
            file_path=csv_file,
            account_hint="Assets:Nubank:Checking",
        )
        result = use_case.execute(command)
        
        # Assert
        entries = entry_repo.find_by_batch(result.batch_id)
        assert len(entries) == 1
        assert entries[0].metadata["account_hint"] == "Assets:Nubank:Checking"
    
    def test_batch_count_methods(self, container, nubank_csv):
        """Test repository count methods."""
        # Arrange
        use_case: ImportNubankStatement = container.import_nubank_statement_use_case()
        batch_repo = container.import_batch_repository()
        
        # Get initial counts
        initial_total = batch_repo.count()
        initial_completed = batch_repo.count_by_status(ImportStatus.COMPLETED)
        
        # Act: Import file
        command = ImportNubankStatementCommand(file_path=nubank_csv)
        result = use_case.execute(command)
        
        # Assert: Counts increased
        assert batch_repo.count() == initial_total + 1
        assert batch_repo.count_by_status(ImportStatus.COMPLETED) == initial_completed + 1
        
        # Assert: Count with filters
        nubank_count = batch_repo.count(source=ImportSource.NUBANK_CSV)
        assert nubank_count >= 1
        
        completed_nubank_count = batch_repo.count(
            source=ImportSource.NUBANK_CSV,
            status=ImportStatus.COMPLETED,
        )
        assert completed_nubank_count >= 1
