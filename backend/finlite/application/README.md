# Application Layer

Esta camada contém os **Use Cases** (Application Services) que orquestram a lógica de negócio.

## Princípios

- ✅ **Um use case = uma ação do usuário** (ex: "importar Nubank")
- ✅ **Orquestra entidades + repositories** (não contém lógica de negócio)
- ✅ **Agnóstico de interface** (CLI, API, TUI usam os mesmos use cases)
- ✅ **Transacional via UnitOfWork**
- ✅ **Emite eventos de domínio**

## Estrutura

```
application/
├── accounts/
│   ├── create_account.py
│   ├── list_accounts.py
│   └── seed_default_chart.py
│
├── transactions/
│   ├── create_transaction.py
│   └── list_transactions.py
│
├── ingestion/
│   ├── import_nubank.py
│   ├── import_ofx.py
│   ├── apply_rules.py
│   └── post_pending.py
│
├── reports/
│   ├── generate_cashflow.py
│   └── generate_category_report.py
│
├── export/
│   └── export_beancount.py
│
└── nlp/
    ├── parse_intent.py
    └── execute_intent.py
```

## Exemplo: Import Nubank Use Case

```python
from dataclasses import dataclass
from pathlib import Path
from finlite.domain.repositories import UnitOfWork
from finlite.infrastructure.events import EventBus, ImportCompletedEvent

@dataclass
class ImportNubankCommand:
    file_path: Path
    account_hint: str | None
    default_currency: str

@dataclass
class ImportNubankResult:
    batch_id: int
    entries_count: int
    duplicates_skipped: int

def import_nubank(
    cmd: ImportNubankCommand,
    uow: UnitOfWork,
    event_bus: EventBus,
) -> ImportNubankResult:
    """Import Nubank CSV and create statement entries."""
    
    with uow:
        # 1. Validar arquivo
        if not cmd.file_path.exists():
            raise FileNotFoundError(f"File not found: {cmd.file_path}")
        
        # 2. Verificar duplicatas
        digest = sha256_file(cmd.file_path)
        existing = uow.import_batches.find_by_digest(digest)
        if existing:
            raise DuplicateImportError(f"Batch already imported: {cmd.file_path.name}")
        
        # 3. Parse CSV (helper puro)
        entries = parse_nubank_csv(cmd.file_path, cmd.default_currency)
        
        # 4. Criar batch (domain entity)
        batch = ImportBatch.create(
            source="nubank_csv",
            external_id=cmd.file_path.name,
            file_sha256=digest,
        )
        
        # 5. Persistir
        saved_batch = uow.import_batches.save(batch)
        for entry in entries:
            uow.statement_entries.save(entry.with_batch_id(saved_batch.id))
        
        # 6. Commit transação
        uow.commit()
        
        # 7. Emitir evento (auditoria)
        event_bus.publish(ImportCompletedEvent(
            batch_id=saved_batch.id,
            entries_count=len(entries),
            timestamp=datetime.now(UTC),
        ))
        
        return ImportNubankResult(
            batch_id=saved_batch.id,
            entries_count=len(entries),
            duplicates_skipped=0,
        )
```

## CLI Integration (thin adapter)

```python
# interfaces/cli/commands/import.py
@import_app.command("nubank")
def import_nubank_cmd(
    file_path: Path,
    account: str | None = None,
):
    """Import Nubank CSV file."""
    container = get_container()
    
    # CLI apenas constrói comando e chama use case
    result = container.import_nubank_use_case()(
        ImportNubankCommand(
            file_path=file_path,
            account_hint=account,
            default_currency=container.config().default_currency,
        )
    )
    
    # Apresentação (presenter)
    console.print(f"✓ Imported {result.entries_count} entries (batch #{result.batch_id})")
```

## Testes

Use cases são testados **mockando repositories**:

```python
def test_import_nubank_rejects_duplicate(tmp_path):
    # Arrange
    mock_uow = MockUnitOfWork()
    mock_uow.import_batches.add(existing_batch)  # simula duplicata
    event_bus = InMemoryEventBus()
    
    # Act & Assert
    with pytest.raises(DuplicateImportError):
        import_nubank(
            ImportNubankCommand(...),
            uow=mock_uow,
            event_bus=event_bus,
        )
```

## Regras

1. **Use cases não retornam entities** - retornam DTOs/Results
2. **Sempre usar UnitOfWork** - controle explícito de transação
3. **Emitir eventos** - para auditoria e extensibilidade (hooks)
4. **Não acessar infra diretamente** - apenas via repositories/services injetados

---

**Ver também**: `domain/` (entities), `infrastructure/` (repositories), `interfaces/` (CLI/API)
