

Descrição do Projeto

Nome: finlite
Propósito: App de finanças pessoais local-first com contabilidade de dupla entrada, ingestão bancária (Nubank/OFX), regras + IA local para classificação, relatórios gerenciais e módulo de investimentos (PM médio, proventos, P/L, IR mensal).
UX: 100% usável via CLI e TUI (terminal). UI Web (Vue) e API (FastAPI) entram depois sem reescrever o core.
Dados: SQLite (WAL + foreign_keys). Migrações com Alembic desde o dia 1.
Não-objetivos iniciais: nuvem, multiusuário, sync. (Possíveis no futuro sem quebrar o core.)

⸻

Arquitetura (visão geral)
	•	Core contábil: Account, Transaction, Posting (soma zero), multi-moeda preparado.
	•	Ingestão: ImportBatch, StatementEntry (+ dedupe, reconciliação).
	•	Rules Engine: condições (regex, valor, tempo) → ações (conta/tag). DSL e dry-run mais adiante.
	•	IA local (opcional): TF-IDF + LogisticRegression (fallback às regras), detecção de outliers.
	•	Relatórios: cashflow, por categoria, balanço/DRE; depois P/L e IR de investimentos.
	•	Investimentos: Security, Trade, Lot (PM médio), Price, CorporateAction, proventos.
	•	Interfaces:
	•	CLI (Typer): comandos determinísticos; fin ask (NL → intent) com --explain.
	•	TUI (Textual/Rich): Dashboard, Inbox (importados → postar), Ledger, Reports, Rules, Command Palette (Ctrl+K).
	•	Web (opcional): FastAPI (read-only primeiro) + Vue 3 + Vite + Tailwind/DaisyUI.

⸻

Qualidade e Não-funcionais (válidos em todas as fases)
	•	SQLite com WAL e PRAGMA foreign_keys=ON, synchronous=NORMAL.
	•	Migrations: Alembic desde a Fase 0.
	•	Testes: pytest (unit + integração); “golden files” para relatórios.
	•	Estilo e Tipos: ruff, mypy.
	•	Decimal em dinheiro; transações atômicas; idempotência de import.
	•	Logs & Auditoria: eventos “imported/rule_applied/posted/corrected” e hash de batches.
	•	Performance alvo: 50k postings → relatórios comuns < 2 s em SQLite.

⸻

Roadmap por Fases

Fase 0 — Fundamentos (0.5 semana)

Escopo
	•	Repo e toolchain: ruff, mypy, pytest, pre-commit.
	•	Config .env simples (caminho do DB, moeda padrão).
	•	Engine SQLite + Alembic ativo (primeira migration).
	•	Esqueleto de pacotes: core/, rules/, ingest/, reports/, cli/, tui/, nlp/ (pastas vazias documentadas).

Entregáveis
	•	fin init-db cria ~/.finlite/finlite.db.
	•	CI local (script) roda lint+types+tests.

Aceite
	•	Testes básicos verdes; migration inicial criada e aplicada.

Saída
	•	Base estável para iterar.

⸻

Fase 1 — Núcleo Contábil + CLI básica (1 semana)

Escopo
	•	Modelos: Account, Transaction, Posting (Decimal, soma zero, moeda por posting).
	•	CLI: fin accounts seed|list|add, fin txn add (postings explícitos), fin export beancount, fin report cashflow.

Entregáveis
	•	Lançar manualmente receitas/despesas; export Beancount.

Aceite
	•	3 cenários de teste (receita, despesa, transferência) batendo com relatório.

Saída
	•	Ledger confiável, pronto para ingestão.

⸻

Fase 2 — Ingestão Bancária + Regras (1 semana)

Escopo
	•	Importadores: fin import nubank <csv> (mapa de colunas configurável via YAML); OFX (opcional).
	•	StatementEntry com status: imported|matched|posted, external_id, dedupe por file_sha256 + heurística.
	•	Rules Engine (v1): fin rules add|list, fin rules-apply --auto (regex payee, amount_lt/gt, hora/dia).
	•	fin post pending --auto cria transações balanceadas (ativo vs despesas/receitas).

Entregáveis
	•	Pipeline: importar → sugerir → postar.

Aceite
	•	Dataset de exemplo com ≥90% das sugestões corretas via regras; reimport não duplica.

Saída
	•	Lançamento em massa com pouco atrito.

⸻

Fase 2A — CLI em Linguagem Natural (NL → Intent) (0.5–1 semana)

Escopo
	•	Módulo nlp/:
	•	Normalizador (dateparser PT-BR, valores, moeda),
	•	Regras/Gramáticas de intents de alta precisão (report_cashflow, report_by_category, import_file, post_pending, list_transactions, make_rule),
	•	Resolver (sinônimos → contas/categorias),
	•	Fallback (TF-IDF + LogisticRegression) com --explain.
	•	Comando: fin ask "<frase>" com preview do comando que será executado.

Entregáveis
	•	10–15 frases mapeadas (tests); fin ask -x mostra intent/slots → comando.

Aceite
	•	≥85% de acerto nas frases de catálogo; nenhuma ação destrutiva sem preview/confirm.

Saída
	•	UX “fale e faça” no terminal, sem LLM externo.

⸻

Fase 2B — TUI (Textual/Rich) + Command Palette (1 semana)

Escopo
	•	fin tui: layout base (Dashboard + Inbox).
	•	Command Palette (Ctrl+K) com fuzzy (rapidfuzz) e suporte a NL → intent (reuso do nlp/).
	•	Inbox: listar entries, aceitar/postar (A), editar (E), filtrar (/), aplicar regras (R).

Entregáveis
	•	TUI funcional p/ revisar e postar importados; palette com preview e confirmação.

Aceite
	•	Usabilidade fluida: navegar, aceitar/postar dezenas de entries sem sair do terminal.

Saída
	•	Experiência “app de desktop” inteiramente no terminal.

⸻

Fase 3 — Classificação Assistida (IA local) + Outliers (1 semana)

Escopo
	•	fin ml train (TF-IDF + LogisticRegression); fin ml suggest --threshold 0.8.
	•	Híbrido: regras > ML; ML só no residual.
	•	Outliers por categoria/período (IsolationForest opcional) → fin detect outliers --month.

Entregáveis
	•	Modelo serializado, métricas (fin ml report), sugestão com score; detector de anomalias.

Aceite
	•	Cobertura adicional ≥50% dos residuais com acurácia ≥80% (dataset pequeno).
	•	Nenhuma sugestão é aplicada sem confirmação/limiar.

Saída
	•	Menos correções manuais + alertas úteis.

⸻

Fase 4 — Cartão de Crédito (Liability) + Conciliação (1 semana)

Escopo
	•	Conta Liabilities:CreditCard:*, fechamento de fatura:
fin card build-statement --from --to --card Nubank
	•	Quitação: transferência de Assets:* p/ Liabilities:*.
	•	Reconciliação/fuzzy matching (data ±N dias, valor ±x%, payee similar) e duplicatas.

Entregáveis
	•	Fechamento/quitação fiel; reconciliação assistida.

Aceite
	•	Diferença ≤ R$ 0,01 em cenários de teste; duplicatas detectadas.

Saída
	•	Modelo de cartão correto e prático.

⸻

Fase 5 — Relatórios Pro + Orçamento (1 semana)

Escopo
	•	fin report balance --date, fin report income-statement --from --to.
	•	Orçamento por categoria/mês com rollover:
fin budget set "Expenses:Groceries" 1200 --month 2025-10,
fin budget report --month 2025-10.
	•	Export CSV/Markdown.

Entregáveis
	•	Balanço, DRE, orçamento; exportáveis.

Aceite
	•	Testes replicando cenários conhecidos; execução < 1 s em 10k postings.

Saída
	•	Visão gerencial fechada.

⸻

Fase 6 — Investimentos (Parte 1: Trades & Lotes) (2 semanas)

Escopo
	•	Tabelas: Security, Trade, Lot (PM médio BR), Price (stub), CorporateAction (stub).
	•	fin inv import-trades <csv> (começa por CSV consolidado).
	•	fin inv holdings, fin inv pnl --from --to.

Entregáveis
	•	PM médio robusto, P/L realizado por período.

Aceite
	•	Casos clássicos (compra, venda parcial, recompras) batem com referência (erro ≤ 0,01).

Saída
	•	Carteira funcional.

⸻

Fase 7 — Investimentos (Parte 2: Preços, Proventos, Ações Corporativas) (2 semanas)

Escopo
	•	fin inv prices sync --source csv:./precos.csv (primeiro local).
	•	Proventos: fin inv dividends import <csv> e fin inv dividends report --month.
	•	Splits/agrupamentos com ajuste de lotes/PM.
	•	Relatórios: alocação, evolução do patrimônio, yield on cost.

Entregáveis
	•	Marcação a mercado local, proventos e ajustes por splits.

Aceite
	•	Posições e YOC consistentes após eventos.

Saída
	•	Visão completa da carteira.

⸻

Fase 8 — IR Mensal de Investimentos + DARF (1 semana)

Escopo
	•	Cálculo de IR mensal (PM médio; compensação de prejuízos; isenção ≤20k).
	•	fin tax monthly --month 2025-09 --export csv.

Entregáveis
	•	Relatório de IR e base de DARF.

Aceite
	•	Casos de referência brasileiros batendo com tolerâncias mínimas.

Saída
	•	Fim da dor do IR mensal.

⸻

Fase 9 — DSL de Regras + Dry-Run Diff + Hooks (1 semana)

Escopo
	•	DSL legível p/ regras (arquivo .rule) com parser simples e validação.
	•	fin rules apply --dry-run mostra diff colorido (CLI/TUI) e undo imediato.
	•	Hooks pós-ação: fin hook add --on posted ./script.py.

Entregáveis
	•	Regras versionadas, auditáveis e seguras; extensibilidade por hooks.

Aceite
	•	Dry-run fiel; rollback; exemplos de hook funcionando.

Saída
	•	Governança e automação avançadas.

⸻

Fase 10 — Exportações & Interop (1 semana)

Escopo
	•	Export JSONL (eventos), Parquet (p/ notebooks), Beancount/CSV por intervalo.
	•	Template de planilha (CSV) para pivôs.

Entregáveis
	•	Ecossistema aberto.

Aceite
	•	Import no Sheets/Excel/Beancount funcionando; integridade preservada.

Saída
	•	Interoperabilidade.

⸻

Fase 11 (Opcional) — API FastAPI + UI Web (Vue 3) (2–3 semanas)

Escopo
	•	API (read-only primeiro): endpoints para Dashboard, Inbox, Ledger, Reports, Investimentos.
	•	Auth local (token no arquivo).
	•	UI (Vue + Vite + Tailwind/DaisyUI):
	•	Dashboard com gráficos (ECharts/Chart.js),
	•	Inbox (aceitar/editar/postar),
	•	Transações com busca avançada,
	•	Regras (lista/validação),
	•	Investimentos (posições, P/L, proventos).

Entregáveis
	•	Front bonito com paridade de leitura em relação ao CLI/TUI.

Aceite
	•	Build local (sem dependência externa) e leitura fluida de dados reais.

Saída
	•	Visualização rica quando/quiser — sem romper CLI/TUI.

⸻

Prioridades (se quiser acelerar valor)
	1.	F2 + F2A + F2B: ingestão + NL + TUI (ganho de usabilidade imediato).
	2.	F3: ML local e outliers (reduz correções).
	3.	F4: cartão como liability (fecha ciclo real de gastos).
	4.	F5: relatórios pro + orçamento.
	5.	F6–F8: investimentos + IR mensal (pacota a parte de patrimônio).
	6.	F9–F11: governança, interop e UI web.

⸻

Exemplos de uso (amarrando as interfaces)

CLI determinística

fin import nubank ./extrato.csv --account "Assets:Bank:Nubank"
fin rules-apply --auto
fin post pending --auto
fin report cashflow --month 2025-09
fin export beancount ~/Desktop/ledger.beancount

CLI em linguagem natural

fin ask "importe ./extrato.csv do nubank e lança tudo"
fin ask "quanto gastei com mercado em setembro?"
fin ask "listar transações acima de 500 reais dos últimos 7 dias"

TUI (Command Palette + Inbox)

fin tui
# Ctrl+K → "gasto mercado 9" → Enter (preview → executar)
# Inbox: A = aceitar/postar, E = editar, / = filtrar, R = aplicar regras


⸻

Riscos & Mitigações (resumo)
	•	CSV variável (bancos): mapeador YAML + testes por fonte.
	•	Classificação fraca no início: prioridade para regras; thresholds conservadores; explain sempre.
	•	Cartão (parcelas/estornos): regras específicas + cenários de teste.
	•	Performance: índices, queries agregadas por mês e, se necessário, views materializadas locais.

⸻

Duração estimada (referência)
	•	F0: 0.5 sem | F1: 1 | F2: 1 | F2A: 0.5–1 | F2B: 1 | F3: 1 | F4: 1 | F5: 1 |
	•	F6–F7: 4 | F8: 1 | F9: 1 | F10: 1 | F11: 2–3 (opcional)




------------
perfeito — dá sim pra deixar a CLI “turbinada” com uma LLM debaixo do capô usando Pydantic AI (o framework “agents” do Pydantic) e o clai (CLI oficial deles). A chave é: saída estruturada com validação Pydantic → converte linguagem natural em intents tipadas e executa tools com segurança (dry-run/preview).

Abaixo vai um desenho objetivo pra integrar isso no teu app.

O que usar
	•	Pydantic AI (agents) para orquestrar a LLM e tipar intenções/saídas.  ￼
	•	clai (CLI oficial) — ótimo pra depurar agentes no terminal e até rodar agentes customizados com --agent.  ￼
	•	(Opcional) Instructor ou Guardrails se quiser reforçar ainda mais a validação de JSON estruturado; ambos funcionam com Pydantic.  ￼
	•	(Opcional) TypeChat (ideia similar em TS/.NET) caso queira comparar o padrão “schema-first”.  ￼

Arquitetura NL → Ação (segura)
	1.	Schema das intents (Pydantic)
Defina modelos como:
	•	ImportFileIntent(source: Literal["nubank","ofx"], path: str, account: str, auto: bool)
	•	ReportCashflowIntent(month: date | None, from_: date | None, to: date | None, category: str | None)
	•	PostPendingIntent(auto: bool)
	2.	Agente com tools (funções reais da tua CLI):
	•	import_nubank(path, account), rules_apply(auto), post_pending(auto), report_cashflow(...).
Cada tool tem assinatura clara + docstring; o agente chama tool → você valida e executa.
	3.	Validação + preview
	•	LLM gera apenas um dos modelos Pydantic (intenção).
	•	Mostre um preview determinístico (comando equivalente) e peça confirmação para ações que escrevem no DB.
	4.	Fallback & guardrails
	•	Se a saída não validar, peça reformulação automática (loop curto).
	•	Para intents perigosas, exija --confirm ou digitar “yes”.

Fluxo de uso
	•	fin ask "importe ./extrato.csv do nubank e lança tudo"
→ valida ImportFileIntent + PostPendingIntent(auto=True) → preview:

fin import nubank ./extrato.csv --account "Assets:Bank:Nubank"
fin rules-apply --auto
fin post pending --auto

→ confirma → executa.

	•	fin ask "quanto gastei com mercado em setembro?"
→ ReportCashflowIntent(month=2025-09, category="Expenses:Groceries") → roda relatório (read-only).

Esqueleto (conceito)

# intents.py
from pydantic import BaseModel, Field
from typing import Literal, Union, Optional
from datetime import date

class ImportFileIntent(BaseModel):
    kind: Literal["import_file"] = "import_file"
    source: Literal["nubank","ofx"]
    path: str
    account: str
    auto: bool = True

class ReportCashflowIntent(BaseModel):
    kind: Literal["report_cashflow"] = "report_cashflow"
    month: Optional[str] = None
    from_: Optional[str] = Field(default=None, alias="from")
    to: Optional[str] = None
    category: Optional[str] = None

class PostPendingIntent(BaseModel):
    kind: Literal["post_pending"] = "post_pending"
    auto: bool = True

Intent = Union[ImportFileIntent, ReportCashflowIntent, PostPendingIntent]

# agent.py
from pydantic_ai import Agent, ModelRetry  # agente pydantic
from intents import Intent
from typing import Annotated

agent = Agent(
    "openai:gpt-4o-mini",   # ou anthropic/llama.cpp compatível
    instructions=(
      "Você é um parser de comandos de finanças. "
      "Retorne SOMENTE JSON válido que cumpra um dos modelos Pydantic chamados Intent. "
      "Nunca execute nada, apenas emita a intenção."
    ),
    result_type=Intent,  # <- valida saída no Pydantic
)

# tools (expostos ao agente)
@agent.tool
def import_nubank(path: str, account: str) -> str:
    "Importa extrato Nubank CSV e retorna batch id."
    ...

@agent.tool
def report_cashflow(month: str|None=None, from_: str|None=None, to: str|None=None, category: str|None=None) -> str:
    "Gera relatório e retorna caminho do CSV/MD."
    ...

@agent.tool
def post_pending(auto: bool=True) -> str:
    "Posta pendências."
    ...

# cli integration
import typer
from agent import agent
from intents import Intent

app = typer.Typer()

@app.command()
def ask(q: str, explain: bool=False, yes: bool=False):
    result = agent.run(q)            # LLM -> Intent tipada (ou ModelRetry)
    intent = result.data             # instancia Pydantic validada
    cmd_preview = render_preview(intent)  # mostre os comandos equivalentes

    print(cmd_preview)
    if not yes and is_destructive(intent):
        confirm = input("Executar? [y/N] ")
        if confirm.lower() != "y":
            raise SystemExit(0)
    execute(intent)                  # chama as funções reais (tools)

Observação: o clai também permite apontar para um agent customizado com --agent módulo:variável — ótimo pra debug durante o desenvolvimento.  ￼

Como rodar 100% local (sem nuvem)
	•	Use llama-cpp-python ou outro backend local compatível para o agent; se quiser reforçar JSON “na marra”, Instructor suporta structured output inclusive com modelos locais.  ￼
	•	Mantenha regra > ML: para intents ultra-comuns, detecte por gramática regex primeiro e só chame LLM quando a frase for ambígua.

Padrões de segurança (essenciais)
	•	Dry-run obrigatório para ações de escrita; log e “undo” simples.
	•	Whitelisting de tools: o agente só enxerga tools que você expuser.
	•	Limites (tokens, tempo) e retries com validação Pydantic; se falhar 2x, caia para comandos determinísticos.
	•	Auditoria: guarde prompt, intent json, preview, exec result no log.

Roadmap curto para integrar
	1.	Semana 1 — Criar intents Pydantic + fin ask com preview; gramáticas para 6 intents; fallback via agent.
	2.	Semana 2 — Expor tools principais ao agent; --yes/--dry-run; logs/auditoria.
	3.	Semana 3 — TUI: Command Palette chama fin ask; mostra preview e resultado em painel lateral.
	4.	Semana 4 — Modelos locais + modo “offline only”; métricas de acurácia das intents.

Se quiser, eu já escrevo o primeiro módulo intents + fin ask com preview e validação Pydantic, e deixo um agent de exemplo plugado no clai pra você testar no terminal.