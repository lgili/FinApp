"""
Statement Import Domain Events.

Eventos relacionados à importação e processamento de extratos bancários.
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from finlite.domain.events.base import DomainEvent


@dataclass(frozen=True)
class StatementImported(DomainEvent):
    """
    Evento disparado quando um batch de statements é importado com sucesso.

    Attributes:
        batch_id: UUID do batch importado
        source: Fonte da importação (nubank_csv, ofx, etc.)
        entries_count: Número de entries importados
        file_sha256: Hash SHA256 do arquivo
        metadata: Metadados adicionais
    """

    batch_id: UUID
    source: str
    entries_count: int
    file_sha256: str
    metadata: dict

    @property
    def event_type(self) -> str:
        """Tipo do evento."""
        return "statement.imported"


@dataclass(frozen=True)
class StatementMatched(DomainEvent):
    """
    Evento disparado quando um statement entry é reconciliado com transação existente.

    Attributes:
        entry_id: UUID do entry
        batch_id: UUID do batch
        transaction_id: UUID da transação existente com qual foi reconciliado
        matched_by: Método de matching usado (manual, rule, fuzzy, etc.)
        confidence: Confiança do match (0.0 a 1.0, opcional)
    """

    entry_id: UUID
    batch_id: UUID
    transaction_id: UUID
    matched_by: str
    confidence: float | None = None

    @property
    def event_type(self) -> str:
        """Tipo do evento."""
        return "statement.matched"


@dataclass(frozen=True)
class StatementPosted(DomainEvent):
    """
    Evento disparado quando um statement entry é convertido em transação contábil.

    Attributes:
        entry_id: UUID do entry
        batch_id: UUID do batch
        transaction_id: UUID da transação criada
        account_id: UUID da conta debitada/creditada
        amount: Valor da transação
        currency: Moeda
    """

    entry_id: UUID
    batch_id: UUID
    transaction_id: UUID
    account_id: UUID
    amount: str  # Decimal serializado como string
    currency: str

    @property
    def event_type(self) -> str:
        """Tipo do evento."""
        return "statement.posted"


@dataclass(frozen=True)
class StatementImportFailed(DomainEvent):
    """
    Evento disparado quando uma importação falha.

    Attributes:
        source: Fonte da importação
        file_path: Caminho do arquivo
        error_message: Mensagem de erro
        error_type: Tipo do erro (validation, parse, duplicate, etc.)
    """

    source: str
    file_path: str
    error_message: str
    error_type: str

    @property
    def event_type(self) -> str:
        """Tipo do evento."""
        return "statement.import_failed"
