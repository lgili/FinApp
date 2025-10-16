# Examples - FinApp

Small runnable examples to demonstrate common flows in the FinApp project.

Prerequisites
- Python 3.11+ (project uses 3.13 in CI but examples work on 3.11+)
- A virtualenv in `.venv` with project dependencies installed (see `requirements.txt`)

Quick start (zsh)

```bash
# from project root
cd "$(pwd)"
source .venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"

# Run examples individually
python3 examples/01_setup_accounts.py
python3 examples/02_create_transactions.py
python3 examples/03_import_csv.py
python3 examples/04_query_data.py
python3 examples/05_full_workflow.py --reset
```

If you prefer a one-shot runner, use `examples/run_all.sh` (it will activate `.venv`).

Notes
- Examples create a local SQLite DB at `backend/finlite.db` and will call `models.Base.metadata.create_all` if needed.
- The examples are written to be idempotent when possible (re-running shouldn't fail).
# FinApp - Exemplos Práticos

Esta pasta contém exemplos executáveis para testar e aprender a usar o FinApp.

## 📋 Estrutura

```
examples/
├── README.md                    # Este arquivo
├── 01_setup_accounts.py        # Criar estrutura de contas
├── 02_create_transactions.py   # Criar transações manualmente
├── 03_import_csv.py            # Importar extrato CSV
├── 04_query_data.py            # Consultar e analisar dados
├── 05_full_workflow.py         # Workflow completo
└── data/
    ├── nubank_example.csv      # CSV exemplo do Nubank
    └── itau_example.csv        # CSV exemplo do Itaú
```

## 🚀 Como Usar

### 1. Preparar o ambiente

```bash
# Voltar para a raiz do projeto
cd /Users/lgili/Documents/01\ -\ Codes/01\ -\ Github/finapp

# Ativar ambiente virtual
source backend/venv/bin/activate  # ou seu caminho do venv

# Garantir que o banco está criado
cd backend
alembic upgrade head
cd ..
```

### 2. Executar exemplos em ordem

```bash
# Exemplo 1: Criar estrutura de contas
python examples/01_setup_accounts.py

# Exemplo 2: Criar transações
python examples/02_create_transactions.py

# Exemplo 3: Importar CSV
python examples/03_import_csv.py

# Exemplo 4: Consultar dados
python examples/04_query_data.py

# Exemplo 5: Workflow completo (tudo junto)
python examples/05_full_workflow.py
```

### 3. Visualizar dados no Prisma Studio

```bash
cd backend
# Se tiver Prisma configurado
prisma studio

# Ou use o SQLite diretamente
sqlite3 finlite.db
```

## 📝 Descrição dos Exemplos

### 01_setup_accounts.py
Cria uma estrutura hierárquica de contas realista:
- Assets (Ativos)
  - Bank (Bancos)
    - Nubank
    - Itaú
  - Cash (Dinheiro)
- Expenses (Despesas)
  - Food (Alimentação)
  - Transport (Transporte)
  - Housing (Moradia)
- Income (Receitas)
  - Salary (Salário)

### 02_create_transactions.py
Demonstra como criar transações:
- Transferências entre contas
- Despesas com múltiplas categorias
- Receitas
- Transactions com tags

### 03_import_csv.py
Importa extrato CSV do Nubank:
- Lê arquivo CSV de exemplo
- Cria import batch
- Processa entries
- Detecta duplicatas

### 04_query_data.py
Exemplos de consultas:
- Buscar transactions por período
- Calcular saldo de contas
- Listar transactions por categoria
- Estatísticas gerais

### 05_full_workflow.py
Workflow completo de ponta a ponta:
1. Cria contas
2. Importa CSV
3. Cria transactions manuais
4. Gera relatórios

## 💡 Dicas

- Execute os exemplos em ordem na primeira vez
- Cada exemplo é independente e pode ser rodado múltiplas vezes
- Os dados são persistidos no banco `backend/finlite.db`
- Use `--reset` para limpar o banco antes de executar (onde disponível)

## 🔧 Troubleshooting

### Erro: "No module named 'finlite'"

```bash
# Adicione o backend ao PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"
```

### Erro: "Database not found"

```bash
cd backend
alembic upgrade head
```

### Erro ao importar CSV

Verifique se o arquivo CSV existe em `examples/data/` e tem o formato correto.

## 📚 Mais Informações

Consulte o arquivo `EXAMPLES.md` na raiz do projeto para documentação completa da API.
