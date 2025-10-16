from finlite.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from finlite.domain.entities.import_batch import ImportBatch, ImportSource


def test_import_batch_find_by_sha256():
    uow = SqlAlchemyUnitOfWork.create_for_testing()

    from finlite.infrastructure.persistence.sqlalchemy.repositories.import_batch_repository import (
        SqlAlchemyImportBatchRepository,
    )

    # create and persist
    with uow:
        batch = ImportBatch.create(source=ImportSource.NUBANK_CSV, filename="t.csv", file_sha256="deadbeef")
        repo = SqlAlchemyImportBatchRepository(uow.session)
        repo.add(batch)
        uow.commit()

    # query
    with uow:
        repo = SqlAlchemyImportBatchRepository(uow.session)
        found = repo.find_by_sha256("deadbeef")
        assert found is not None
        assert found.file_sha256 == "deadbeef"
