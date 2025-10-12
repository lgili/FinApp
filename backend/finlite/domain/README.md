# Domain Layer

Esta camada contém a **lógica de negócio pura** do Finlite, independente de frameworks e infraestrutura.

## Princípios

- ✅ **Sem dependências externas** (apenas stdlib + type hints)
- ✅ **Imutável quando possível** (`@dataclass(frozen=True)`)
- ✅ **Validações no construtor** (fail-fast)
- ✅ **Sem I/O** (sem DB, sem arquivo, sem network)
- ✅ **Testável sem mocks** (pure functions)

## Estrutura

```
domain/
├── entities/              # Entidades com identidade (id)
│   ├── account.py         # Account
│   ├── transaction.py     # Transaction
│   ├── statement.py       # ImportBatch, StatementEntry
│   └── rule.py            # MapRule
│
├── value_objects/         # Objetos sem identidade (comparados por valor)
│   ├── money.py           # Money(amount, currency)
│   ├── account_name.py    # AccountName(hierarchical path)
│   └── posting.py         # Posting(account_id, money, memo)
│
├── exceptions/            # Erros de domínio
│   ├── __init__.py
│   └── accounting.py      # UnbalancedError, InsufficientPostingsError
│
└── repositories/          # Interfaces (ABC) para persistência
    ├── __init__.py
    ├── account.py         # AccountRepository (ABC)
    ├── transaction.py     # TransactionRepository (ABC)
    └── statement.py       # StatementRepository (ABC)
```

## Exemplo: Transaction Entity

```python
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime

@dataclass(frozen=True, slots=True)
class Transaction:
    id: int | None
    description: str
    occurred_at: datetime
    postings: tuple[Posting, ...]
    reference: str | None = None
    
    @classmethod
    def create(
        cls,
        description: str,
        occurred_at: datetime,
        postings: list[Posting],
        reference: str | None = None,
    ) -> "Transaction":
        # Validação soma zero
        totals = {}
        for posting in postings:
            currency = posting.money.currency
            totals[currency] = totals.get(currency, Decimal("0")) + posting.money.amount
        
        imbalanced = {cur: amt for cur, amt in totals.items() if amt != 0}
        if imbalanced:
            raise UnbalancedTransactionError(f"Unbalanced: {imbalanced}")
        
        if len(postings) < 2:
            raise InsufficientPostingsError("Minimum 2 postings required")
        
        return cls(
            id=None,
            description=description,
            occurred_at=occurred_at,
            postings=tuple(postings),
            reference=reference,
        )
```

## Testes

Testes de domínio são **unitários puros** (sem DB, sem mocks):

```python
def test_transaction_rejects_unbalanced():
    with pytest.raises(UnbalancedTransactionError):
        Transaction.create(
            description="Test",
            occurred_at=datetime.now(UTC),
            postings=[
                Posting(account_id=1, money=Money(Decimal("100"), "BRL")),
                Posting(account_id=2, money=Money(Decimal("-50"), "BRL")),
            ],
        )
```

## Regras

1. **Entidades sempre válidas** - construtor valida; se passar, está correto
2. **Imutabilidade** - usar `frozen=True` quando possível
3. **Sem lógica de infra** - nada de SQL, JSON, HTTP aqui
4. **Repositories são interfaces** - implementação fica em `infrastructure/`

---

**Ver também**: `application/` (use cases que orquestram entities)
