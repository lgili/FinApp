# 📚 Índice de Documentação — Finlite v0.2

**Bem-vindo à refatoração Clean Architecture do Finlite!**

Este índice te guia por toda a documentação criada.

---

## 🚀 Start Here (Comece Aqui)

1. **[STATUS_REPORT.md](STATUS_REPORT.md)** ⭐
   - **O que é:** Resumo executivo da refatoração
   - **Quando ler:** PRIMEIRO - para entender o que foi feito
   - **Tempo:** 5 min

2. **[backend/QUICKSTART_NEW_ARCH.md](backend/QUICKSTART_NEW_ARCH.md)** ⭐
   - **O que é:** Guia rápido de início
   - **Quando ler:** SEGUNDO - para decidir próximos passos
   - **Tempo:** 3 min

---

## 📖 Documentação Principal

### Arquitetura

| Arquivo | Descrição | Quando Ler |
|---------|-----------|------------|
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | Visão geral da Clean Architecture<br>✅ Diagramas, fluxos, exemplos | Antes de começar a codar |
| **[FOLDER_STRUCTURE.md](FOLDER_STRUCTURE.md)** | Árvore visual de pastas<br>✅ Navegação estruturada | Para entender organização |

### Planejamento

| Arquivo | Descrição | Quando Ler |
|---------|-----------|------------|
| **[MIGRATION_ROADMAP.md](MIGRATION_ROADMAP.md)** | Checklist de 7 fases (100+ tarefas)<br>✅ Progresso trackável | Ao planejar sprints |
| **[plan.md](plan.md)** | Plano original do projeto<br>✅ Visão de longo prazo | Contexto geral |

### Referência

| Arquivo | Descrição | Quando Ler |
|---------|-----------|------------|
| **[USEFUL_COMMANDS.md](USEFUL_COMMANDS.md)** | Comandos prontos (testes, lint, git)<br>✅ Copy-paste friendly | Durante desenvolvimento |

---

## 📂 Documentação por Camada

Cada camada tem seu próprio README explicando responsabilidades:

```
backend/finlite/
├── domain/README.md              # Entities, Value Objects, validações
├── application/README.md         # Use Cases, orquestração
├── infrastructure/README.md      # DB, LLM, eventos, observability
└── interfaces/README.md          # CLI, API, TUI
```

**Como usar:**
1. Leia o README da camada ANTES de criar código nela
2. Veja exemplos de código nos READMEs
3. Copie estruturas de teste sugeridas

---

## 🗺️ Fluxo de Leitura Recomendado

### Para Entender a Refatoração (30 min)

```
1. STATUS_REPORT.md          (5 min)  ← O que foi feito
2. ARCHITECTURE.md           (15 min) ← Como funciona
3. MIGRATION_ROADMAP.md      (10 min) ← O que falta fazer
```

### Para Começar a Codar (1h)

```
1. backend/QUICKSTART_NEW_ARCH.md     (5 min)
2. FOLDER_STRUCTURE.md                (10 min)
3. finlite/domain/README.md           (15 min)
4. finlite/application/README.md      (15 min)
5. finlite/infrastructure/README.md   (15 min)
```

### Para Migrar Código (por demanda)

```
1. Ver MIGRATION_ROADMAP.md (fase relevante)
2. Ler README da camada onde vai trabalhar
3. Ver código legado em finlite_legacy/
4. Implementar na nova estrutura
5. Marcar checkbox no ROADMAP
```

---

## 🎯 Decisões Rápidas

### "Quero entender a arquitetura"
→ Leia **[ARCHITECTURE.md](ARCHITECTURE.md)**

### "Quero começar a migrar código"
→ Leia **[MIGRATION_ROADMAP.md](MIGRATION_ROADMAP.md)** Fase 1

### "Preciso de um comando específico"
→ Veja **[USEFUL_COMMANDS.md](USEFUL_COMMANDS.md)**

### "Onde fica cada coisa?"
→ Veja **[FOLDER_STRUCTURE.md](FOLDER_STRUCTURE.md)**

### "Qual o status atual?"
→ Veja **[STATUS_REPORT.md](STATUS_REPORT.md)**

### "Como funciona [camada X]?"
→ Veja `finlite/[camada]/README.md`

---

## 📋 Checklists

### Antes de Codar
- [ ] Li `STATUS_REPORT.md`
- [ ] Li `ARCHITECTURE.md`
- [ ] Entendi separação de camadas
- [ ] Instalei dependências: `pip install -e '.[dev]'`

### Durante a Migração
- [ ] Consultei `MIGRATION_ROADMAP.md` para a fase
- [ ] Li README da camada relevante
- [ ] Vi código legado em `finlite_legacy/`
- [ ] Criei testes antes/durante implementação
- [ ] Rodei `make ci` (lint+type+test)
- [ ] Marquei checkbox no ROADMAP

### Ao Completar uma Fase
- [ ] Todos os testes passando
- [ ] Coverage mantido (≥80%)
- [ ] Documentação atualizada
- [ ] Commit com mensagem descritiva
- [ ] Push da branch `feat/phase-X-...`

---

## 🔍 Busca Rápida

### Por Tópico

| Tópico | Arquivo | Seção |
|--------|---------|-------|
| Clean Architecture | `ARCHITECTURE.md` | Visão Geral |
| Domain Entities | `finlite/domain/README.md` | Entities |
| Repositories | `finlite/domain/README.md` | Repositories |
| Use Cases | `finlite/application/README.md` | Use Cases |
| UnitOfWork | `finlite/infrastructure/README.md` | UnitOfWork |
| Dependency Injection | `finlite/interfaces/README.md` | DI |
| Event Bus | `finlite/infrastructure/README.md` | Events |
| Testes | `ARCHITECTURE.md` | Estratégia de Testes |
| CLI thin adapters | `finlite/interfaces/README.md` | CLI |

### Por Fase

| Fase | Arquivo | Página |
|------|---------|--------|
| Fase 0 (Estrutura) | `MIGRATION_ROADMAP.md` | Linha 10 |
| Fase 1 (Domain) | `MIGRATION_ROADMAP.md` | Linha 20 |
| Fase 2 (Infrastructure) | `MIGRATION_ROADMAP.md` | Linha 40 |
| Fase 3 (Application) | `MIGRATION_ROADMAP.md` | Linha 70 |
| Fase 4 (Interfaces) | `MIGRATION_ROADMAP.md` | Linha 110 |

---

## 🆘 FAQ Rápido

**P: Por onde começar?**  
R: `STATUS_REPORT.md` → `backend/QUICKSTART_NEW_ARCH.md` → `MIGRATION_ROADMAP.md` Fase 1

**P: O código antigo foi apagado?**  
R: NÃO! Está preservado em `finlite_legacy/` e `tests_legacy/`

**P: Posso voltar atrás?**  
R: SIM! Basta renomear as pastas de volta (`mv finlite_legacy finlite`)

**P: Quanto tempo vai levar?**  
R: Estimativa: 20-30 dias (veja `MIGRATION_ROADMAP.md`)

**P: Posso pedir um exemplo completo?**  
R: SIM! Peça "Cria import_nubank completo na nova arquitetura"

**P: Como testar sem DB?**  
R: Use testes unitários com mock repositories (veja `finlite/application/README.md`)

**P: Onde fica [arquivo X]?**  
R: Veja `FOLDER_STRUCTURE.md` para árvore completa

**P: Qual comando roda testes?**  
R: `pytest tests/` (veja `USEFUL_COMMANDS.md` para mais)

---

## 📊 Progresso Atual

```
Fase 0: ██████████ 100% ✅ COMPLETO
Fase 1: ░░░░░░░░░░   0% ← PRÓXIMA
Fase 2: ░░░░░░░░░░   0%
Fase 3: ░░░░░░░░░░   0%
Fase 4: ░░░░░░░░░░   0%
Fase 5: ░░░░░░░░░░   0%
Fase 6: ░░░░░░░░░░   0%
Fase 7: ░░░░░░░░░░   0%

Total: ██░░░░░░░░░ 14%
```

**Ver:** `MIGRATION_ROADMAP.md` para checklist detalhado

---

## 🌟 Arquivos Mais Importantes (Top 5)

1. **[STATUS_REPORT.md](STATUS_REPORT.md)** - Resumo executivo
2. **[ARCHITECTURE.md](ARCHITECTURE.md)** - Como funciona
3. **[MIGRATION_ROADMAP.md](MIGRATION_ROADMAP.md)** - O que fazer
4. **[finlite/domain/README.md](backend/finlite/domain/README.md)** - Domain layer
5. **[USEFUL_COMMANDS.md](USEFUL_COMMANDS.md)** - Comandos prontos

---

## 📝 Última Atualização

**Data:** 2025-10-11  
**Versão:** 0.2.0  
**Arquivos criados:** 11 documentos + 5 READMEs de camada  
**Total:** ~50KB de documentação

---

**Dica:** Bookmark esta página no seu editor! 📌

```bash
# Adicionar ao .zshrc:
alias findocs="cat /path/to/finapp/INDEX.md | less"
```
