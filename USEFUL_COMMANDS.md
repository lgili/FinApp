# 🛠️ Comandos Úteis — Nova Arquitetura

## 📦 Instalação

```bash
cd backend

# Instalar dependências (inclui novas: dependency-injector, structlog, pytest-mock)
pip install -e '.[dev]'

# Instalar dependências AI (opcional)
pip install -e '.[ai]'

# Verificar instalação
python -c "import finlite; print(finlite.__version__)"  # Should print 0.2.0
```

---

## 🧪 Testes

```bash
# Rodar testes legados (devem continuar funcionando)
PYTHONPATH=. pytest tests_legacy/ -v

# Rodar novos testes (ainda vazios por enquanto)
pytest tests/ -v

# Rodar apenas testes unitários (rápidos, sem DB)
pytest tests/unit/ -v

# Rodar testes de integração (com DB)
pytest tests/integration/ -v

# Rodar testes E2E (CLI completo)
pytest tests/e2e/ -v

# Coverage
pytest tests/ --cov=finlite --cov-report=html
open htmlcov/index.html
```

---

## 🔍 Lint & Type Check

```bash
# Lint
ruff check finlite/

# Format
ruff format finlite/

# Type check
mypy finlite/

# Tudo junto (CI)
make ci  # ou: ruff check . && ruff format --check . && mypy . && pytest
```

---

## 📂 Navegação

```bash
# Ver estrutura completa
ls -R finlite/

# Ver apenas domínios
ls -R finlite/domain/

# Ver código legado (backup)
ls -R finlite_legacy/

# Contar linhas de código
find finlite/ -name "*.py" | xargs wc -l | tail -1

# Ver tamanho de cada camada
du -sh finlite/domain finlite/application finlite/infrastructure finlite/interfaces
```

---

## 🗄️ Database

```bash
# Inicializar DB (quando CLI estiver migrado)
fin init-db

# Rodar migrations
alembic upgrade head

# Criar nova migration
alembic revision --autogenerate -m "description"

# Ver status das migrations
alembic current
alembic history
```

---

## 🔄 Comparar com Legado

```bash
# Diff entre novo e legado
diff -r finlite/domain/ finlite_legacy/core/

# Ver o que mudou em um arquivo específico
diff finlite/domain/entities/account.py finlite_legacy/core/accounts.py

# Copiar arquivo do legado para referência
cp finlite_legacy/db/models.py finlite/infrastructure/persistence/sqlalchemy/models.py.bak
```

---

## 📝 Documentação

```bash
# Ler arquitetura
cat ARCHITECTURE.md | less

# Ver roadmap
cat MIGRATION_ROADMAP.md | less

# Ver estrutura de pastas
cat FOLDER_STRUCTURE.md | less

# Ver status atual
cat STATUS_REPORT.md | less

# Quick start
cat backend/QUICKSTART_NEW_ARCH.md | less
```

---

## 🎯 Migração

### Começar Fase 1 (Domain)

```bash
cd backend

# 1. Criar primeira entity
touch finlite/domain/entities/account.py
touch finlite/domain/entities/transaction.py

# 2. Criar value objects
touch finlite/domain/value_objects/money.py
touch finlite/domain/value_objects/posting.py

# 3. Criar exceptions
touch finlite/domain/exceptions/accounting.py

# 4. Criar repository interfaces
touch finlite/domain/repositories/account.py
touch finlite/domain/repositories/transaction.py
touch finlite/domain/repositories/unit_of_work.py

# 5. Criar testes
touch tests/unit/domain/test_account.py
touch tests/unit/domain/test_transaction.py
touch tests/unit/domain/test_money.py
```

### Começar Fase 2 (Infrastructure)

```bash
# 1. Copiar models do legado (base)
cp finlite_legacy/db/models.py finlite/infrastructure/persistence/sqlalchemy/models.py

# 2. Criar repositories
touch finlite/infrastructure/persistence/sqlalchemy/repositories.py

# 3. Criar UnitOfWork
touch finlite/infrastructure/persistence/sqlalchemy/unit_of_work.py

# 4. Criar mappers
touch finlite/infrastructure/persistence/sqlalchemy/mappers.py

# 5. Criar testes
touch tests/integration/test_repositories.py
touch tests/integration/test_unit_of_work.py
```

### Começar Fase 3 (Application)

```bash
# 1. Criar use case
touch finlite/application/ingestion/import_nubank.py

# 2. Criar DTOs
touch finlite/application/ingestion/dtos.py

# 3. Criar testes
touch tests/unit/application/test_import_nubank.py
```

### Começar Fase 4 (Interfaces)

```bash
# 1. Criar CLI command
touch finlite/interfaces/cli/commands/import.py

# 2. Criar presenter
touch finlite/interfaces/cli/presenters/import_presenter.py

# 3. Criar DI container
touch finlite/shared/di.py

# 4. Criar testes E2E
touch tests/e2e/test_import_workflow.py
```

---

## 🐛 Debug

```bash
# Rodar com debug
python -m pdb -m pytest tests/unit/domain/test_transaction.py

# Ver traceback completo
pytest tests/ -vv --tb=long

# Rodar apenas um teste
pytest tests/unit/domain/test_account.py::test_account_creation

# Ver prints (não captura output)
pytest tests/ -s

# Rodar com ipdb (breakpoint interativo)
# Adicione no código: import ipdb; ipdb.set_trace()
pytest tests/
```

---

## 🎨 Git Workflow

```bash
# Criar branch para Fase 1
git checkout -b feat/phase-1-domain

# Commitar progresso
git add finlite/domain/
git commit -m "feat(domain): add Account entity with validation"

# Ver status da migração
git log --oneline --graph --decorate

# Comparar com main
git diff main...HEAD

# Push branch
git push -u origin feat/phase-1-domain
```

---

## 📊 Métricas

```bash
# Contar arquivos por camada
find finlite/domain -name "*.py" | wc -l
find finlite/application -name "*.py" | wc -l
find finlite/infrastructure -name "*.py" | wc -l
find finlite/interfaces -name "*.py" | wc -l

# Ver progresso do roadmap
grep -c "\[x\]" MIGRATION_ROADMAP.md  # Completos
grep -c "\[ \]" MIGRATION_ROADMAP.md  # Pendentes

# Cobertura de testes
pytest --cov=finlite --cov-report=term-missing | grep TOTAL
```

---

## 🚀 Atalhos Make

```bash
# Se criar Makefile com targets úteis:

make domain        # Criar estrutura domain
make infra         # Criar estrutura infrastructure
make app           # Criar estrutura application
make interfaces    # Criar estrutura interfaces

make test-domain   # Rodar apenas testes domain
make test-app      # Rodar apenas testes application
make test-all      # Rodar todos os testes

make docs          # Gerar docs (Sphinx)
make lint-fix      # Auto-fix lint issues
```

---

## 🔥 Comandos Avançados

```bash
# Encontrar TODOs/FIXMEs
grep -r "TODO\|FIXME" finlite/

# Ver dependências entre módulos
pydeps finlite/ --max-bacon=2

# Gerar diagrama de classes (pyreverse)
pyreverse -o png -p finlite finlite/
open classes_finlite.png

# Profile performance
python -m cProfile -o profile.stats -m pytest tests/integration/
snakeviz profile.stats

# Ver imports não usados
pylint finlite/ --disable=all --enable=unused-import
```

---

## 📦 Build & Deploy

```bash
# Build wheel
python -m build

# Instalar wheel
pip install dist/finlite-0.2.0-py3-none-any.whl

# Verificar package
twine check dist/*

# (Futuro) Publish to PyPI
twine upload dist/*
```

---

## 🔍 Busca Rápida

```bash
# Buscar por padrão no código
rg "class.*Repository" finlite/

# Buscar por uso de função
rg "import_nubank" finlite/ tests/

# Ver todas as entities
fd "entity" finlite/domain/

# Ver todos os use cases
fd . finlite/application/
```

---

**Dica:** Adicione estes comandos como aliases no seu `.zshrc`:

```bash
alias fintest="pytest tests/ -v"
alias fintest-fast="pytest tests/unit/ -v"
alias finlint="ruff check finlite/ && mypy finlite/"
alias finformat="ruff format finlite/"
alias fincov="pytest --cov=finlite --cov-report=html && open htmlcov/index.html"
```

---

**Última atualização:** 2025-10-11
