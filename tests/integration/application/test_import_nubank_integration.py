import os
from pathlib import Path

from finlite.application.use_cases.import_nubank_statement import (
    ImportNubankStatement,
    ImportNubankStatementCommand,
)
from finlite.domain.entities.import_batch import ImportBatch
from finlite.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from finlite.infrastructure.persistence.sqlalchemy.repositories.import_batch_repository import (
    SqlAlchemyImportBatchRepository,
)
from finlite.infrastructure.persistence.sqlalchemy.repositories.statement_entry_repository import (
    SqlAlchemyStatementEntryRepository,
)
from finlite.shared.event_bus import InMemoryEventBus


def test_import_nubank_creates_batch_and_detects_duplicate(tmp_path: Path):
    # Arrange: create a small CSV in tmp path
    csv_content = """date,description,amount
2025-01-01,Test deposit,100.00
2025-01-02,Test withdraw,-50.00
"""
    csv_file = tmp_path / "statement.csv"
    csv_file.write_text(csv_content)

    uow = SqlAlchemyUnitOfWork.create_for_testing()

    # Act: first import should succeed and create a batch
    cmd = ImportNubankStatementCommand(file_path=csv_file)
    event_bus = InMemoryEventBus()

    with uow:
        batch_repo = SqlAlchemyImportBatchRepository(uow.session)
        entry_repo = SqlAlchemyStatementEntryRepository(uow.session)

        use_case = ImportNubankStatement(
            import_batch_repository=batch_repo,
            statement_entry_repository=entry_repo,
            event_bus=event_bus,
        )

        result1 = use_case.execute(cmd)
        # Persist changes so subsequent sessions can read the imported batch
        uow.commit()

    # Assert: batch created and entries > 0
    assert result1.batch_id is not None
    with uow:
        repo = SqlAlchemyImportBatchRepository(uow.session)
        batch = repo.find_by_sha256(result1.file_sha256)
        assert isinstance(batch, ImportBatch)

    # Act: importing same file again should raise DuplicateImportError
    with uow:
        batch_repo = SqlAlchemyImportBatchRepository(uow.session)
        entry_repo = SqlAlchemyStatementEntryRepository(uow.session)
        use_case = ImportNubankStatement(
            import_batch_repository=batch_repo,
            statement_entry_repository=entry_repo,
            event_bus=event_bus,
        )

        duplicated = False
        try:
            _ = use_case.execute(cmd)
            uow.commit()
        except Exception:
            duplicated = True

        assert duplicated is True
