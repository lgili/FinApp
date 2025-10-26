"""
ImportOFXStatement Use Case - Imports OFX bank statement files.

Responsibilities:
- Validate OFX file
- Calculate SHA256 hash for deduplication
- Parse OFX transaction blocks (STMTTRN)
- Create ImportBatch and StatementEntries
- Persist via repositories
- Publish StatementImported event
- Structured logging
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
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
from finlite.ingest.utils import parse_amount, sha256_file
from finlite.shared.observability import get_logger

logger = get_logger(__name__)

# Regex for parsing OFX tags
_TAG_VAL_RE = re.compile(r"<([A-Z0-9_]+)>([^<\n\r]*)")


@dataclass
class ImportOFXStatementCommand:
    """
    Command to import OFX bank statement.

    Attributes:
        file_path: Path to OFX file
        default_currency: Default currency (USD, BRL, etc.)
        account_hint: Account hint for entries (optional)
    """

    file_path: Path
    default_currency: str = "BRL"
    account_hint: Optional[str] = None


@dataclass
class ImportOFXStatementResult:
    """
    Result of OFX import.

    Attributes:
        batch_id: UUID of created batch
        entries_count: Number of imported entries
        file_sha256: SHA256 hash of file
    """

    batch_id: UUID
    entries_count: int
    file_sha256: str


class ImportOFXStatement:
    """
    Use Case for importing OFX bank statements.

    Supports standard OFX format with STMTTRN transaction blocks.
    Extracts: DTPOSTED, TRNAMT, FITID, NAME, MEMO, CURRENCY fields.

    Examples:
        >>> cmd = ImportOFXStatementCommand(
        ...     file_path=Path("./statement.ofx"),
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
        Initialize use case with dependencies.

        Args:
            import_batch_repository: Repository for batches
            statement_entry_repository: Repository for entries
            event_bus: Event bus for publishing events
        """
        self._batch_repo = import_batch_repository
        self._entry_repo = statement_entry_repository
        self._event_bus = event_bus

    def execute(self, command: ImportOFXStatementCommand) -> ImportOFXStatementResult:
        """
        Execute OFX import.

        Args:
            command: Command with import parameters

        Returns:
            Result with batch_id and count

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is invalid
            DuplicateImportError: If file already imported

        Examples:
            >>> cmd = ImportOFXStatementCommand(file_path=Path("./statement.ofx"))
            >>> result = use_case.execute(cmd)
        """
        logger.info(
            "importing_ofx_statement",
            file_path=str(command.file_path),
            currency=command.default_currency,
        )

        try:
            # 1. Validate file
            if not command.file_path.exists():
                raise FileNotFoundError(f"File not found: {command.file_path}")

            # 2. Calculate hash for deduplication
            file_sha256 = sha256_file(command.file_path)
            logger.debug("calculated_file_hash", file_sha256=file_sha256)

            # 3. Check if already imported
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
                        source="ofx",
                        file_path=str(command.file_path),
                        error_message=error_msg,
                        error_type="duplicate",
                    )
                )
                raise DuplicateImportError(error_msg)

            # 4. Create batch
            batch = ImportBatch.create(
                source=ImportSource.OFX,
                filename=command.file_path.name,
                file_sha256=file_sha256,
                metadata={
                    "account_hint": command.account_hint,
                },
            )
            self._batch_repo.add(batch)
            logger.debug("batch_created", batch_id=str(batch.id))

            # 5. Parse OFX and create entries
            ofx_text = self._read_ofx_file(command.file_path)
            transactions = self._extract_transactions(ofx_text, command.default_currency)

            entries_count = 0
            for idx, txn in enumerate(transactions, start=1):
                entry = self._create_entry(
                    transaction=txn,
                    batch_id=batch.id,
                    file_name=command.file_path.name,
                    row_index=idx,
                    default_currency=command.default_currency,
                    account_hint=command.account_hint,
                )
                self._entry_repo.add(entry)
                entries_count += 1

            logger.debug("entries_created", count=entries_count)

            # 6. Mark batch as completed
            batch.mark_completed(transaction_count=entries_count)
            self._batch_repo.update(batch)

            # 7. Publish event
            self._event_bus.publish(
                StatementImported(
                    batch_id=batch.id,
                    source="ofx",
                    entries_count=entries_count,
                    file_sha256=file_sha256,
                    metadata={
                        "filename": command.file_path.name,
                        "account_hint": command.account_hint,
                    },
                )
            )

            logger.info(
                "ofx_statement_imported",
                batch_id=str(batch.id),
                entries_count=entries_count,
                file_sha256=file_sha256,
            )

            return ImportOFXStatementResult(
                batch_id=batch.id,
                entries_count=entries_count,
                file_sha256=file_sha256,
            )

        except DuplicateImportError:
            # Event already published before raising, just re-raise
            raise
        except Exception as exc:
            logger.error(
                "ofx_import_failed",
                file_path=str(command.file_path),
                error=str(exc),
                exc_info=True,
            )
            # Publish failure event
            self._event_bus.publish(
                StatementImportFailed(
                    source="ofx",
                    file_path=str(command.file_path),
                    error_message=str(exc),
                    error_type=type(exc).__name__,
                )
            )
            raise

    def _read_ofx_file(self, path: Path) -> str:
        """
        Read OFX file with encoding fallback.

        Args:
            path: Path to OFX file

        Returns:
            File contents as string
        """
        # Try UTF-8 first, fallback to Latin-1
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            logger.debug("utf8_decode_failed_fallback_to_latin1", path=str(path))
            return path.read_text(encoding="latin-1", errors="ignore")

    def _extract_transactions(
        self, ofx_text: str, default_currency: str
    ) -> list[dict[str, str]]:
        """
        Extract STMTTRN blocks from OFX text.

        Args:
            ofx_text: OFX file contents
            default_currency: Default currency for transactions

        Returns:
            List of transaction dicts with tag->value mappings
        """
        transactions: list[dict[str, str]] = []
        current: dict[str, str] | None = None
        header_currency: str | None = None

        for raw_line in ofx_text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            # Extract header-level currency (CURDEF)
            if header_currency is None and line.upper().startswith("<CURDEF>"):
                value = line.split(">", 1)[-1]
                header_currency = value.split("<", 1)[0].strip().upper()

            # Start of transaction block
            if line.upper().startswith("<STMTTRN>"):
                current = {}
                continue

            # End of transaction block
            if current is not None and line.upper().startswith("</STMTTRN>"):
                # Apply default currency if not specified
                if "CURRENCY" not in current:
                    current["CURRENCY"] = header_currency or default_currency
                transactions.append(current)
                current = None
                continue

            # Parse tag-value pairs within transaction block
            if current is not None:
                match = _TAG_VAL_RE.match(line)
                if match:
                    tag = match.group(1).upper()
                    val = match.group(2).strip()
                    current[tag] = val

        return transactions

    def _parse_ofx_datetime(self, value: str) -> datetime:
        """
        Parse OFX datetime string.

        OFX format: YYYYMMDDHHMMSS[.sss][Z|[+/-]hhmm]
        Timezone offsets are ignored and stored as UTC.

        Args:
            value: OFX datetime string

        Returns:
            Parsed datetime in UTC

        Raises:
            ValueError: If date format is invalid
        """
        match = re.match(r"^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})", value)
        if not match:
            # Fallback to current time if parse fails
            logger.warning("invalid_ofx_datetime_fallback_to_now", value=value)
            return datetime.now(UTC)

        year, month, day, hour, minute, second = map(int, match.groups())
        return datetime(year, month, day, hour, minute, second, tzinfo=UTC)

    def _create_entry(
        self,
        transaction: dict[str, str],
        batch_id: UUID,
        file_name: str,
        row_index: int,
        default_currency: str,
        account_hint: Optional[str],
    ) -> StatementEntry:
        """
        Create StatementEntry from OFX transaction dict.

        Args:
            transaction: Dict of OFX tags and values
            batch_id: UUID of batch
            file_name: Name of file
            row_index: Index of transaction (1-based)
            default_currency: Default currency
            account_hint: Account hint (optional)

        Returns:
            StatementEntry entity

        Raises:
            ValueError: If data is invalid
        """
        # Extract fields
        dt_posted = transaction.get("DTPOSTED", "")
        trn_amt = transaction.get("TRNAMT", "0")
        name = transaction.get("NAME", "")
        memo = transaction.get("MEMO", "")
        fitid = transaction.get("FITID", "")
        currency = transaction.get("CURRENCY", default_currency).upper()

        # Parse date
        try:
            occurred_at = self._parse_ofx_datetime(dt_posted) if dt_posted else datetime.now(UTC)
        except Exception as exc:
            raise ValueError(f"Invalid date in transaction {row_index}: {dt_posted}") from exc

        # Parse amount
        try:
            amount = Decimal(trn_amt)
        except (InvalidOperation, ValueError):
            try:
                amount = parse_amount(trn_amt)
            except Exception as exc:
                raise ValueError(f"Invalid amount in transaction {row_index}: {trn_amt}") from exc

        # Build description (NAME + MEMO)
        description = (name + (" - " if name and memo else "") + memo).strip()

        # External ID (use FITID or fallback to row index)
        external_id = fitid or f"{file_name}:row:{row_index}"

        # Create entry
        entry = StatementEntry.create(
            batch_id=batch_id,
            external_id=external_id,
            payee=name or None,
            memo=description or None,
            amount=amount,
            currency=currency,
            occurred_at=occurred_at,
            metadata={"account_hint": account_hint, "row_index": row_index, "fitid": fitid}
            if account_hint
            else {"row_index": row_index, "fitid": fitid},
        )

        return entry
