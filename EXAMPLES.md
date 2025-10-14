# FinApp - Exemplos de Uso

Este documento contém exemplos práticos de como usar o FinApp após a implementação do sistema de UUID↔Integer conversion.

## 📋 Índice

1. [Trabalhando com Accounts](#trabalhando-com-accounts)
2. [Criando Transactions](#criando-transactions)
3. [Importando Statements](#importando-statements)
4. [Hierarquia de Contas](#hierarquia-de-contas)
5. [Consultando Dados](#consultando-dados)

---

## 🏦 Trabalhando com Accounts

### Criar uma conta

```python
from finlite.domain.entities.account import Account
from finlite.domain.value_objects.account_type import AccountType
from finlite.infrastructure.persistence.sqlalchemy.repositories.account_repository import SqlAlchemyAccountRepository

# Criar uma nova conta
account = Account.create(
    name="Assets:Bank:Checking",
    account_type=AccountType.ASSET,
    currency="BRL"
)

# Persistir no banco
with uow:
    uow.accounts.add(account)
    uow.commit()

print(f"Conta criada com ID: {account.id}")  # UUID
```

### Buscar uma conta

```python
# Buscar por ID (UUID)
account = uow.accounts.get(account_id)
print(f"Nome: {account.name}")
print(f"Tipo: {account.account_type}")
print(f"Moeda: {account.currency}")

# Buscar por nome
checking = uow.accounts.find_by_name("Assets:Bank:Checking")

# Listar todas as contas ativas
all_accounts = uow.accounts.list_all()
for acc in all_accounts:
    print(f"- {acc.name} ({acc.currency})")
```

### Atualizar uma conta

```python
# Carregar conta existente
account = uow.accounts.get(account_id)

# Modificar
account.rename("Assets:Bank:Checking:Main")

# Salvar
with uow:
    uow.accounts.update(account)
    uow.commit()
```

---

## 💸 Criando Transactions

### Transaction simples (2 postings)

```python
from finlite.domain.entities.transaction import Transaction
from finlite.domain.value_objects.posting import Posting
from decimal import Decimal
from datetime import date

# Criar postings
postings = [
    Posting.create(
        account_id=checking_account.id,
        amount=Decimal("-100.00"),
        notes="Pagamento café"
    ),
    Posting.create(
        account_id=expenses_coffee.id,
        amount=Decimal("100.00"),
        notes="Café na padaria"
    )
]

# Criar transaction
transaction = Transaction.create(
    description="Café da manhã",
    date=date.today(),
    postings=postings
)

# Persistir
with uow:
    uow.transactions.add(transaction)
    uow.commit()

print(f"Transaction criada: {transaction.id}")
```

### Transaction com múltiplos postings

```python
# Split transaction - compra com múltiplas categorias
postings = [
    Posting.create(
        account_id=credit_card.id,
        amount=Decimal("-250.50")
    ),
    Posting.create(
        account_id=expenses_food.id,
        amount=Decimal("150.00"),
        notes="Supermercado"
    ),
    Posting.create(
        account_id=expenses_household.id,
        amount=Decimal("100.50"),
        notes="Produtos de limpeza"
    )
]

transaction = Transaction.create(
    description="Compras do mês",
    date=date(2025, 10, 13),
    postings=postings,
    tags=["shopping", "monthly"]
)

with uow:
    uow.transactions.add(transaction)
    uow.commit()
```

---

## 📥 Importando Statements

### Importar extrato CSV do Nubank

```python
from finlite.application.use_cases.import_nubank_statement import (
    ImportNubankStatement,
    ImportNubankStatementCommand
)
from pathlib import Path

# Preparar comando
csv_file = Path("~/Downloads/nubank-2025-10.csv")
command = ImportNubankStatementCommand(
    file_path=csv_file,
    default_currency="BRL",
    account_hint="Assets:Nubank"  # opcional
)

# Executar importação
use_case = container.import_nubank_statement_use_case()
result = use_case.execute(command)

print(f"✅ Importado batch: {result.batch_id}")
print(f"📊 Total de entries: {result.entries_count}")
print(f"🔐 SHA256: {result.file_sha256}")
```

### Verificar entries importadas

```python
# Buscar entries do batch
entries = uow.statement_entries.find_by_batch(result.batch_id)

for entry in entries:
    print(f"Data: {entry.occurred_at}")
    print(f"Descrição: {entry.memo}")
    print(f"Valor: {entry.amount} {entry.currency}")
    print(f"Status: {entry.status}")
    print("---")

# Buscar entries pendentes (prontas para conversão)
pending = uow.statement_entries.find_pending(limit=100)
print(f"📋 {len(pending)} entries aguardando processamento")
```

### Evitar duplicatas

```python
# O sistema detecta automaticamente arquivos duplicados via SHA256
try:
    result = use_case.execute(command)
except DuplicateImportError as e:
    print(f"❌ Arquivo já foi importado: {e}")
    
# Ou verificar manualmente
existing_batch = uow.import_batches.find_by_sha256(file_sha256)
if existing_batch:
    print(f"⚠️  Batch existente: {existing_batch.id}")
```

---

## 🌳 Hierarquia de Contas

### Criar estrutura hierárquica

```python
# Criar conta pai
assets = Account.create(
    name="Assets",
    account_type=AccountType.ASSET,
    currency="BRL"
)

with uow:
    uow.accounts.add(assets)
    uow.commit()

# Criar conta filha
bank = Account.create(
    name="Assets:Bank",
    account_type=AccountType.ASSET,
    currency="BRL",
    parent_id=assets.id  # Referência ao pai
)

with uow:
    uow.accounts.add(bank)
    uow.commit()

# Criar subconta
checking = Account.create(
    name="Assets:Bank:Checking",
    account_type=AccountType.ASSET,
    currency="BRL",
    parent_id=bank.id
)

with uow:
    uow.accounts.add(checking)
    uow.commit()
```

### Navegar pela hierarquia

```python
# Buscar conta com parent carregado
checking = uow.accounts.get(checking_id)

# O parent_id é preservado corretamente
if checking.parent_id:
    parent = uow.accounts.get(checking.parent_id)
    print(f"Conta pai: {parent.name}")

# Estrutura completa
print(f"""
Hierarquia:
├── {assets.name}
│   └── {bank.name}
│       └── {checking.name}
""")
```

---

## 🔍 Consultando Dados

### Buscar transactions por conta

```python
from datetime import date, timedelta

# Transactions dos últimos 30 dias
end_date = date.today()
start_date = end_date - timedelta(days=30)

transactions = uow.transactions.find_by_account(
    account_id=checking_account.id,
    start_date=start_date,
    end_date=end_date
)

print(f"📊 {len(transactions)} transações encontradas")

# Calcular balanço
total = sum(
    posting.amount 
    for txn in transactions 
    for posting in txn.postings 
    if posting.account_id == checking_account.id
)
print(f"💰 Saldo do período: {total} BRL")
```

### Filtrar por tipo de conta

```python
# Todas as contas de despesa
expense_accounts = uow.accounts.find_by_type(AccountType.EXPENSE)

for account in expense_accounts:
    print(f"- {account.name}")
    
# Contar por tipo
asset_count = uow.accounts.count(account_type=AccountType.ASSET)
liability_count = uow.accounts.count(account_type=AccountType.LIABILITY)

print(f"Assets: {asset_count}")
print(f"Liabilities: {liability_count}")
```

### Buscar batches de importação

```python
# Listar todos os batches completos
completed_batches = uow.import_batches.find_by_status(ImportStatus.COMPLETED)

for batch in completed_batches:
    print(f"Batch {batch.id}")
    print(f"  Fonte: {batch.source}")
    print(f"  Arquivo: {batch.filename}")
    print(f"  Entries: {batch.transaction_count}")
    print(f"  Data: {batch.started_at}")
    print()
```

---

## 💡 Dicas Importantes

### 1. UUIDs são preservados

```python
# O UUID da entidade domain é preservado
account = Account.create(...)
original_uuid = account.id

with uow:
    uow.accounts.add(account)
    uow.commit()

# O UUID permanece o mesmo
assert account.id == original_uuid  # ✅ True
```

### 2. Queries sempre por UUID

```python
# ✅ Correto - query por UUID
account = uow.accounts.get(account_id)  # account_id é UUID

# ✅ Correto - find_by_sha256 para batches
batch = uow.import_batches.find_by_sha256(file_hash)

# ✅ Correto - find_by_batch com UUID
entries = uow.statement_entries.find_by_batch(batch.id)
```

### 3. Batch operations

```python
# Adicionar múltiplas contas
accounts = [
    Account.create("Assets:Cash", AccountType.ASSET, "BRL"),
    Account.create("Assets:Savings", AccountType.ASSET, "BRL"),
    Account.create("Expenses:Food", AccountType.EXPENSE, "BRL"),
]

with uow:
    for account in accounts:
        uow.accounts.add(account)
    uow.commit()  # Commit único
```

### 4. Error handling

```python
from finlite.domain.exceptions import (
    AccountNotFoundError,
    DuplicateImportError,
    InvalidTransactionError
)

try:
    account = uow.accounts.get(account_id)
except AccountNotFoundError:
    print(f"❌ Conta {account_id} não encontrada")

try:
    transaction = Transaction.create(...)  # postings não balanceiam
except InvalidTransactionError as e:
    print(f"❌ Transaction inválida: {e}")
```

---

## 🧪 Testing

### Unit tests com mocks

```python
from unittest.mock import Mock

def test_import_statement():
    # Arrange
    batch_repo = Mock()
    batch_repo.find_by_sha256.return_value = None
    
    use_case = ImportNubankStatement(
        batch_repo=batch_repo,
        entry_repo=Mock(),
        event_bus=Mock()
    )
    
    # Act
    result = use_case.execute(command)
    
    # Assert
    assert result.entries_count > 0
    batch_repo.add.assert_called_once()
```

### Integration tests

```python
def test_account_persistence(uow):
    # Criar
    account = Account.create("Test", AccountType.ASSET, "BRL")
    
    with uow:
        uow.accounts.add(account)
        uow.commit()
    
    # Verificar persistência
    retrieved = uow.accounts.get(account.id)
    assert retrieved.name == "Test"
    assert retrieved.account_type == AccountType.ASSET
```

---

## 📚 Referências

- **Domain Entities:** `/backend/finlite/domain/entities/`
- **Repositories:** `/backend/finlite/infrastructure/persistence/sqlalchemy/repositories/`
- **Use Cases:** `/backend/finlite/application/use_cases/`
- **Tests:** `/tests/`

---

**💡 Pro Tip:** Sempre use UnitOfWork para garantir transações ACID:

```python
with uow:
    # Múltiplas operações
    uow.accounts.add(account)
    uow.transactions.add(transaction)
    uow.commit()  # Commit atômico
    
# Rollback automático em caso de exceção
```
