"""
ImportNubankStatement Use Case - Importa extrato CSV do Nubank.

Responsabilidades:
- Validar arquivo CSV
- Calcular hash SHA256 para deduplicação
- Parsear linhas do CSV
- Criar ImportBatch e StatementEntries
- Persistir via repositories
- Publicar StatementImported event
- Logging estruturado
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional
from uuid import UUID

from finlite.domain.entities.import_batch import ImportBatch, ImportSource, ImportStatus
from finlite.domain.entities.statement_entry import StatementEntry
from finlite.domain.events.statement_events import StatementImported, StatementImportFailed
from finlite.domain.exceptions import DuplicateImportError
from finlite.domain.repositories.import_batch_repository import IImportBatchRepository
from finlite.domain.repositories.statement_entry_repository import IStatementEntryRepository
from finlite.infrastructure.events.event_bus import IEventBus
from finlite.ingest.utils import parse_amount, read_csv_rows, sha256_file
from finlite.shared.observability import get_logger

logger = get_logger(__name__)

# Column aliases (case-insensitive)
ALIASES = {
    "date": {"data", "date"},
    "description": {"descricao", "descrição", "description"},
    "amount": {"valor", "amount"},
    "id": {"id", "identificador", "external_id"},
    "currency": {"moeda", "currency"},
}


def _alias_lookup(row: dict[str, str], key: str) -> str | None:
    """Busca valor por aliases de coluna."""
    for candidate in ALIASES[key]:
        if candidate in row and row[candidate] != "":
            return row[candidate]
    return None


@dataclass
class ImportNubankStatementCommand:
    """
    Command para importar extrato CSV do Nubank.

    Attributes:
        file_path: Caminho do arquivo CSV
        default_currency: Moeda padrão (BRL)
        account_hint: Dica de conta para os entries (opcional)
    """

    file_path: Path
    default_currency: str = "BRL"
    account_hint: Optional[str] = None


@dataclass
class ImportNubankStatementResult:
    """
    Resultado da importação.

    Attributes:
        batch_id: UUID do batch criado
        entries_count: Número de entries importados
        file_sha256: Hash SHA256 do arquivo
    """

    batch_id: UUID
    entries_count: int
    file_sha256: str


class ImportNubankStatement:
    """
    Use Case para importar extratos CSV do Nubank.

    Examples:
        >>> cmd = ImportNubankStatementCommand(
        ...     file_path=Path("./extrato.csv"),
        ...     default_currency="BRL",
        ... )
        >>> result = use_case.execute(cmd)
        >>> print(f"Imported batch {result.batch_id} with {result.entries_count} entries")
    """

    def __init__(
        self,
        import_batch_repository: IImportBatchRepository,
        statement_entry_repository: IStatementEntryRepository,
        event_bus: IEventBus,
    ) -> None:
        """
        Inicializa use case com dependencies.

        Args:
            import_batch_repository: Repository de batches
            statement_entry_repository: Repository de entries
            event_bus: Event bus para publicar eventos
        """
        self._batch_repo = import_batch_repository
        self._entry_repo = statement_entry_repository
        self._event_bus = event_bus

    def execute(self, command: ImportNubankStatementCommand) -> ImportNubankStatementResult:
        """
        Executa importação do extrato.

        Args:
            command: Comando com parâmetros de importação

        Returns:
            Resultado com batch_id e contagem

        Raises:
            FileNotFoundError: Se arquivo não existir
            ValueError: Se arquivo for inválido
            DuplicateImportError: Se arquivo já foi importado

        Examples:
            >>> cmd = ImportNubankStatementCommand(file_path=Path("./extrato.csv"))
            >>> result = use_case.execute(cmd)
        """
        logger.info(
            "importing_nubank_statement",
            file_path=str(command.file_path),
            currency=command.default_currency,
        )

        try:
            # 1. Validar arquivo
            if not command.file_path.exists():
                raise FileNotFoundError(f"File not found: {command.file_path}")

            # 2. Calcular hash para deduplicação
            file_sha256 = sha256_file(command.file_path)
            logger.debug("calculated_file_hash", file_sha256=file_sha256)

            # 3. Verificar se já foi importado
            existing_batch = self._batch_repo.find_by_sha256(file_sha256)
            if existing_batch is not None:
                logger.warning(
                    "duplicate_import_detected",
                    existing_batch_id=str(existing_batch.id),
                    file_sha256=file_sha256,
                )
                error_msg = f"File already imported as batch {existing_batch.id}"
                self._event_bus.publish(
                    StatementImportFailed(
                        source="nubank_csv",
                        file_path=str(command.file_path),
                        error_message=error_msg,
                        error_type="duplicate",
                    )
                )

                raise DuplicateImportError(error_msg)

            # 4. Criar batch
            batch = ImportBatch.create(
                source=ImportSource.NUBANK_CSV,
                filename=command.file_path.name,
                file_sha256=file_sha256,
                metadata={
                    "account_hint": command.account_hint,
                },
            )
            self._batch_repo.add(batch)
            logger.debug("batch_created", batch_id=str(batch.id))

            # 5. Parsear CSV e criar entries
            entries_count = 0
            for idx, row in enumerate(read_csv_rows(command.file_path), start=1):
                entry = self._parse_row(
                    row=row,
                    batch_id=batch.id,
                    file_name=command.file_path.name,
                    row_index=idx,
                    default_currency=command.default_currency,
                    account_hint=command.account_hint,
                )
                self._entry_repo.add(entry)
                entries_count += 1

            logger.debug("entries_created", count=entries_count)

            # 6. Marcar batch como completo
            batch.mark_completed(transaction_count=entries_count)
            self._batch_repo.update(batch)

            # 7. Publicar evento
            self._event_bus.publish(
                StatementImported(
                    batch_id=batch.id,
                    source="nubank_csv",
                    entries_count=entries_count,
                    file_sha256=file_sha256,
                    metadata={
                        "filename": command.file_path.name,
                        "account_hint": command.account_hint,
                    },
                )
            )

            logger.info(
                "nubank_statement_imported",
                batch_id=str(batch.id),
                entries_count=entries_count,
                file_sha256=file_sha256,
            )

            return ImportNubankStatementResult(
                batch_id=batch.id,
                entries_count=entries_count,
                file_sha256=file_sha256,
            )

        except DuplicateImportError:
            # Event already published before raising, just re-raise
            raise
        except Exception as exc:
            logger.error(
                "nubank_import_failed",
                file_path=str(command.file_path),
                error=str(exc),
                exc_info=True,
            )
            # Publicar evento de falha
            self._event_bus.publish(
                StatementImportFailed(
                    source="nubank_csv",
                    file_path=str(command.file_path),
                    error_message=str(exc),
                    error_type=type(exc).__name__,
                )
            )
            raise

    def _parse_row(
        self,
        row: dict[str, str],
        batch_id: UUID,
        file_name: str,
        row_index: int,
        default_currency: str,
        account_hint: Optional[str],
    ) -> StatementEntry:
        """
        Parseia linha do CSV em StatementEntry.

        Args:
            row: Linha do CSV (dict de colunas)
            batch_id: UUID do batch
            file_name: Nome do arquivo
            row_index: Índice da linha (1-based)
            default_currency: Moeda padrão
            account_hint: Dica de conta (opcional)

        Returns:
            StatementEntry entity

        Raises:
            ValueError: Se dados forem inválidos
        """
        date_str = _alias_lookup(row, "date")
        desc = _alias_lookup(row, "description") or ""
        amt_str = _alias_lookup(row, "amount") or "0"
        ext_id = _alias_lookup(row, "id") or f"{file_name}:row:{row_index}"
        currency = (_alias_lookup(row, "currency") or default_currency).upper()

        # Parse date (try ISO first, then Brazilian format)
        try:
            occurred_at = datetime.fromisoformat(date_str or "")
        except Exception:
            try:
                occurred_at = datetime.strptime((date_str or ""), "%d/%m/%Y")
            except Exception as exc:
                raise ValueError(f"Invalid date format in row {row_index}: {date_str}") from exc

        if occurred_at.tzinfo is None:
            occurred_at = occurred_at.replace(tzinfo=UTC)

        # Parse amount
        try:
            amount = parse_amount(amt_str)
        except Exception as exc:
            raise ValueError(f"Invalid amount in row {row_index}: {amt_str}") from exc

        # Create entry
        entry = StatementEntry.create(
            batch_id=batch_id,
            external_id=ext_id,
            memo=desc,
            amount=amount,
            currency=currency,
            occurred_at=occurred_at,
            metadata={"account_hint": account_hint, "row_index": row_index}
            if account_hint
            else {"row_index": row_index},
        )

        return entry
