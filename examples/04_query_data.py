"""
Exemplo 04 - Consultar Dados
=============================

Este script demonstra como consultar e analisar dados no FinApp.

Execução:
    python examples/04_query_data.py
"""

import sys
from pathlib import Path
from datetime import date, timedelta
from decimal import Decimal

# Adicionar backend ao path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from finlite.domain.value_objects.account_type import AccountType
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from finlite.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from finlite.infrastructure.persistence.sqlalchemy import models
from finlite.infrastructure.persistence.sqlalchemy.repositories.statement_entry_repository import (
    SqlAlchemyStatementEntryRepository,
)


def query_data():
    """Consulta e analisa dados do FinApp."""
    
    engine = create_engine("sqlite:///backend/finlite.db", echo=False)
    models.Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    uow = SqlAlchemyUnitOfWork(session_factory)
    
    print("🔍 Consultando dados do FinApp...")
    print("=" * 60)
    
    try:
        with uow:
            # ============================================
            # 1. Listar todas as contas
            # ============================================
            print("\n📊 1. TODAS AS CONTAS")
            print("-" * 60)
            
            all_accounts = uow.accounts.list_all()
            print(f"Total de contas: {len(all_accounts)}\n")
            
            # Agrupar por tipo
            by_type = {}
            for account in all_accounts:
                acc_type = account.account_type.value
                if acc_type not in by_type:
                    by_type[acc_type] = []
                by_type[acc_type].append(account)
            
            for acc_type, accounts in by_type.items():
                print(f"{acc_type.upper()}: {len(accounts)} contas")
                for acc in accounts:
                    indent = "  " * acc.name.count(":")
                    print(f"  {indent}• {acc.name}")
            
            # ============================================
            # 2. Buscar contas específicas
            # ============================================
            print("\n\n🔎 2. BUSCAR CONTAS ESPECÍFICAS")
            print("-" * 60)
            
            # Por nome
            nubank = uow.accounts.find_by_name("Assets:Bank:Nubank")
            if nubank:
                print(f"✅ Encontrada: {nubank.name}")
                print(f"   ID: {nubank.id}")
                print(f"   Tipo: {nubank.account_type.value}")
                print(f"   Moeda: {nubank.currency}")
            
            # Por tipo
            print("\n🏦 Contas de ASSET:")
            asset_accounts = uow.accounts.find_by_type(AccountType.ASSET)
            for acc in asset_accounts[:5]:
                print(f"  • {acc.name}")
            if len(asset_accounts) > 5:
                print(f"  ... e mais {len(asset_accounts) - 5} contas")
            
            # ============================================
            # 3. Listar transações
            # ============================================
            print("\n\n💸 3. TRANSAÇÕES RECENTES")
            print("-" * 60)
            
            all_transactions = uow.transactions.list_all()
            print(f"Total de transações: {len(all_transactions)}\n")
            
            # Mostrar últimas 10
            recent = all_transactions[-10:] if len(all_transactions) > 10 else all_transactions
            
            for txn in reversed(recent):
                print(f"📅 {txn.date} - {txn.description}")
                for posting in txn.postings:
                    # Account may not exist (examples are idempotent); handle missing account
                    try:
                        account = uow.accounts.get(posting.account_id)
                        account_name = account.name
                    except Exception:
                        account_name = f"(account {posting.account_id} not found)"

                    # posting.amount is Money; use .amount (Decimal) for numeric ops
                    amt_decimal = getattr(posting.amount, "amount", posting.amount)
                    sign = "+" if amt_decimal > 0 else ""
                    # Format amount using Decimal; show absolute value
                    print(f"   {account_name}: {sign}R$ {amt_decimal:.2f}")
                if txn.tags:
                    print(f"   🏷️  Tags: {', '.join(txn.tags)}")
                print()
            
            # ============================================
            # 4. Calcular saldo de contas
            # ============================================
            print("\n💰 4. SALDO DAS CONTAS")
            print("-" * 60)
            
            # Função para calcular saldo (soma os valores Decimals dentro de Money)
            def calculate_balance(account_id):
                balance = Decimal("0")
                for txn in all_transactions:
                    for posting in txn.postings:
                        if posting.account_id == account_id:
                            # posting.amount is a Money value object; use .amount (Decimal)
                            amt = getattr(posting.amount, "amount", posting.amount)
                            balance += amt
                return balance
            
            # Calcular para contas principais
            bank_accounts = [acc for acc in all_accounts if "Bank" in acc.name and acc.name.count(":") == 2]
            
            print("Contas bancárias:")
            for acc in bank_accounts:
                balance = calculate_balance(acc.id)
                print(f"  {acc.name}: R$ {balance:.2f}")
            
            # ============================================
            # 5. Estatísticas por categoria
            # ============================================
            print("\n\n📈 5. GASTOS POR CATEGORIA")
            print("-" * 60)
            
            expense_accounts = uow.accounts.find_by_type(AccountType.EXPENSE)
            
            expenses_by_category = {}
            for acc in expense_accounts:
                total = calculate_balance(acc.id)
                if total > 0:
                    expenses_by_category[acc.name] = total
            
            # Ordenar por valor
            sorted_expenses = sorted(expenses_by_category.items(), key=lambda x: x[1], reverse=True)
            
            total_expenses = sum(expenses_by_category.values())
            print(f"Total de gastos: R$ {total_expenses:.2f}\n")
            
            for acc_name, amount in sorted_expenses[:10]:
                percentage = (amount / total_expenses * 100) if total_expenses > 0 else 0
                bar = "█" * int(percentage / 2)
                print(f"{acc_name:40s} R$ {amount:8.2f} ({percentage:5.1f}%) {bar}")
            
            # ============================================
            # 6. Batches de importação
            # ============================================
            print("\n\n📦 6. BATCHES DE IMPORTAÇÃO")
            print("-" * 60)
            
            # Tentar buscar batches
            # Buscar entries para ver batches. UnitOfWork may not expose statement_entries
            try:
                pending_entries = None
                if hasattr(uow, "statement_entries"):
                    pending_entries = uow.statement_entries.find_pending(limit=100)
                else:
                    # Fallback: use repository directly with a short-lived session
                    repo_session = uow.session_factory()
                    try:
                        entry_repo = SqlAlchemyStatementEntryRepository(repo_session)
                        pending_entries = entry_repo.find_pending(limit=100)
                    finally:
                        repo_session.close()

                if pending_entries:
                    print(f"✅ {len(pending_entries)} entries pendentes de processamento\n")

                    # Agrupar por batch
                    batches = {}
                    for entry in pending_entries:
                        if entry.batch_id not in batches:
                            batches[entry.batch_id] = []
                        batches[entry.batch_id].append(entry)

                    print(f"Batches encontrados: {len(batches)}")
                    for batch_id, entries in batches.items():
                        print(f"\n  Batch: {batch_id}")
                        print(f"  Entries: {len(entries)}")
                        if entries:
                            print(f"  Período: {min(e.occurred_at for e in entries)} até {max(e.occurred_at for e in entries)}")
                            total = sum(abs(e.amount) for e in entries)
                            print(f"  Total: R$ {total:.2f}")
                else:
                    print("ℹ️  Nenhuma entry pendente encontrada")
                    print("   Execute 03_import_csv.py para importar dados")

            except Exception:
                print(f"ℹ️  Nenhum batch de importação encontrado")
                print(f"   Execute 03_import_csv.py para importar dados")
            
            # ============================================
            # 7. Resumo geral
            # ============================================
            print("\n\n📊 7. RESUMO GERAL")
            print("=" * 60)
            
            # Contar por tipo
            asset_count = len([a for a in all_accounts if a.account_type == AccountType.ASSET])
            expense_count = len([a for a in all_accounts if a.account_type == AccountType.EXPENSE])
            income_count = len([a for a in all_accounts if a.account_type == AccountType.INCOME])
            liability_count = len([a for a in all_accounts if a.account_type == AccountType.LIABILITY])
            
            print(f"📁 Contas:")
            print(f"  • Assets: {asset_count}")
            print(f"  • Expenses: {expense_count}")
            print(f"  • Income: {income_count}")
            print(f"  • Liabilities: {liability_count}")
            print(f"  • Total: {len(all_accounts)}")
            
            print(f"\n💸 Transações: {len(all_transactions)}")
            
            # Calcular totais
            total_income = sum(
                calculate_balance(acc.id)
                for acc in all_accounts
                if acc.account_type == AccountType.INCOME
            )
            
            print(f"\n💰 Totais:")
            print(f"  • Receitas: R$ {abs(total_income):.2f}")
            print(f"  • Despesas: R$ {total_expenses:.2f}")
            print(f"  • Saldo: R$ {abs(total_income) - total_expenses:.2f}")
            
            print("=" * 60)
            
            return True
            
    except Exception as e:
        print(f"\n❌ Erro ao consultar dados: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Session handled by UnitOfWork
        pass


if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║              FinApp - Consultar Dados                         ║
    ║                                                               ║
    ║  Este exemplo mostra como consultar e analisar seus dados    ║
    ║  financeiros usando o FinApp.                                 ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    success = query_data()
    
    if success:
        print("\n🎉 Próximo passo: python examples/05_full_workflow.py")
    else:
        print("\n❌ Falhou. Execute os exemplos anteriores primeiro!")
        sys.exit(1)
