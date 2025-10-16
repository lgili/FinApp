from finlite.domain.value_objects.money import Money
from finlite.domain.value_objects.posting import Posting
from finlite.domain.entities.import_batch import ImportBatch, ImportSource
from finlite.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork


def test_statement_entry_find_by_sha256_creates_and_finds():
    uow = SqlAlchemyUnitOfWork.create_for_testing()

    from finlite.infrastructure.persistence.sqlalchemy.repositories.import_batch_repository import (
        SqlAlchemyImportBatchRepository,
    )
    from finlite.infrastructure.persistence.sqlalchemy.repositories.statement_entry_repository import (
        SqlAlchemyStatementEntryRepository,
    )

    # Persist batch first
    with uow:
        batch_repo = SqlAlchemyImportBatchRepository(uow.session)
        batch = ImportBatch.create(source=ImportSource.NUBANK_CSV, filename="tst", file_sha256="abc123")
        batch_repo.add(batch)
        uow.commit()

    # Create entry in a fresh transaction so the batch model exists
    with uow:
        entry_repo = SqlAlchemyStatementEntryRepository(uow.session)
        from decimal import Decimal
        from datetime import datetime
        from finlite.domain.entities.statement_entry import StatementEntry

        entry = StatementEntry.create(
            batch_id=batch.id,
            external_id="row_1",
            memo="desc",
            amount=Decimal("10.00"),
            currency="BRL",
            occurred_at=datetime.utcnow(),
        )

        entry_repo.add(entry)
        uow.commit()
        ext_id = entry.external_id

    # outside uow, ensure we can find it by external id
    with uow:
        entry_repo = SqlAlchemyStatementEntryRepository(uow.session)
        found = entry_repo.find_by_external_id(batch.id, ext_id)
        assert found is not None
        assert found.external_id == ext_id
