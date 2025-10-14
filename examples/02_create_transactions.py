"""
Exemplo 02 - Criar Transações
==============================

Este script demonstra como criar diferentes tipos de transações no FinApp.

Execução:
    python examples/02_create_transactions.py
"""

import sys
from pathlib import Path
from decimal import Decimal
from datetime import date, timedelta

# Adicionar backend ao path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from finlite.domain.entities.transaction import Transaction
from finlite.domain.value_objects.posting import Posting
from finlite.domain.value_objects.money import Money
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from finlite.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from finlite.infrastructure.persistence.sqlalchemy import models


def get_account_by_name(uow, name):
    """Helper para buscar conta por nome."""
    account = uow.accounts.find_by_name(name)
    if not account:
        raise ValueError(f"Conta '{name}' não encontrada. Execute 01_setup_accounts.py primeiro!")
    return account


def create_transactions():
    """Cria exemplos de transações."""
    
    engine = create_engine("sqlite:///backend/finlite.db", echo=False)
    models.Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    uow = SqlAlchemyUnitOfWork(session_factory)
    
    print("💸 Criando transações de exemplo...")
    print("=" * 60)
    
    try:
        with uow:
            # Buscar contas necessárias
            print("\n🔍 Buscando contas...")
            nubank = get_account_by_name(uow, "Assets:Bank:Nubank")
            itau = get_account_by_name(uow, "Assets:Bank:Itau")
            cash = get_account_by_name(uow, "Assets:Cash")
            salary = get_account_by_name(uow, "Income:Salary")
            restaurant = get_account_by_name(uow, "Expenses:Food:Restaurant")
            groceries = get_account_by_name(uow, "Expenses:Food:Groceries")
            uber = get_account_by_name(uow, "Expenses:Transport:Uber")
            rent = get_account_by_name(uow, "Expenses:Housing:Rent")
            utilities = get_account_by_name(uow, "Expenses:Housing:Utilities")
            entertainment = get_account_by_name(uow, "Expenses:Entertainment")
            
            print("✅ Contas encontradas!")
            
            # ============================================
            # 1. Recebimento de Salário
            # ============================================
            print("\n💰 1. Recebimento de Salário")
            print("-" * 60)
            
            salary_date = date.today() - timedelta(days=5)
            salary_txn = Transaction.create(
                description="Salário Outubro 2025",
                date=salary_date,
                postings=[
                    Posting(
                        account_id=nubank.id,
                        amount=Money(Decimal("5000.00"), "BRL"),
                        notes="Depósito salário",
                    ),
                    Posting(
                        account_id=salary.id,
                        amount=Money(Decimal("-5000.00"), "BRL"),
                        notes="Salário mensal",
                    ),
                ],
                tags=["salary", "income", "monthly"],
            )
            uow.transactions.add(salary_txn)
            print(f"✅ {salary_txn.description}")
            print(f"   Data: {salary_date}")
            print(f"   Valor: R$ 5.000,00")
            
            # ============================================
            # 2. Pagamento de Aluguel
            # ============================================
            print("\n🏠 2. Pagamento de Aluguel")
            print("-" * 60)
            
            rent_date = date.today() - timedelta(days=3)
            rent_txn = Transaction.create(
                description="Aluguel Outubro",
                date=rent_date,
                postings=[
                    Posting(
                        account_id=nubank.id,
                        amount=Money(Decimal("-1500.00"), "BRL"),
                        notes="Pagamento aluguel",
                    ),
                    Posting(
                        account_id=rent.id,
                        amount=Money(Decimal("1500.00"), "BRL"),
                        notes="Aluguel apartamento",
                    ),
                ],
                tags=["housing", "rent", "monthly", "fixed"],
            )
            uow.transactions.add(rent_txn)
            print(f"✅ {rent_txn.description}")
            print(f"   Data: {rent_date}")
            print(f"   Valor: R$ 1.500,00")
            
            # ============================================
            # 3. Compra no Supermercado (Split Transaction)
            # ============================================
            print("\n🛒 3. Compra no Supermercado (Multiple Categories)")
            print("-" * 60)
            
            grocery_date = date.today() - timedelta(days=2)
            grocery_txn = Transaction.create(
                description="Supermercado Extra",
                date=grocery_date,
                postings=[
                    Posting(
                        account_id=itau.id,
                        amount=Money(Decimal("-250.50"), "BRL"),
                        notes="Débito cartão Itaú",
                    ),
                    Posting(
                        account_id=groceries.id,
                        amount=Money(Decimal("200.00"), "BRL"),
                        notes="Compras do mês",
                    ),
                    Posting(
                        account_id=utilities.id,
                        amount=Money(Decimal("50.50"), "BRL"),
                        notes="Produtos de limpeza",
                    ),
                ],
                tags=["groceries", "monthly"],
            )
            uow.transactions.add(grocery_txn)
            print(f"✅ {grocery_txn.description}")
            print(f"   Data: {grocery_date}")
            print(f"   Total: R$ 250,50")
            print(f"   - Groceries: R$ 200,00")
            print(f"   - Utilities: R$ 50,50")
            
            # ============================================
            # 4. Jantar no Restaurante
            # ============================================
            print("\n🍽️  4. Jantar no Restaurante")
            print("-" * 60)
            
            dinner_date = date.today() - timedelta(days=1)
            dinner_txn = Transaction.create(
                description="Restaurante Japonês",
                date=dinner_date,
                postings=[
                    Posting(
                        account_id=cash.id,
                        amount=Money(Decimal("-120.00"), "BRL"),
                        notes="Pagamento em dinheiro",
                    ),
                    Posting(
                        account_id=restaurant.id,
                        amount=Money(Decimal("120.00"), "BRL"),
                        notes="Jantar com amigos",
                    ),
                ],
                tags=["food", "restaurant", "social"],
            )
            uow.transactions.add(dinner_txn)
            print(f"✅ {dinner_txn.description}")
            print(f"   Data: {dinner_date}")
            print(f"   Valor: R$ 120,00")
            
            # ============================================
            # 5. Corridas de Uber (Múltiplas)
            # ============================================
            print("\n🚗 5. Corridas de Uber")
            print("-" * 60)
            
            uber_dates = [
                date.today() - timedelta(days=7),
                date.today() - timedelta(days=5),
                date.today() - timedelta(days=2)
            ]
            uber_values = [Decimal("25.50"), Decimal("18.00"), Decimal("32.75")]
            
            for i, (uber_date, value) in enumerate(zip(uber_dates, uber_values), 1):
                uber_txn = Transaction.create(
                    description=f"Uber - Corrida #{i}",
                    date=uber_date,
                    postings=[
                        Posting(
                            account_id=nubank.id,
                            amount=Money(Decimal(str(-value)), "BRL"),
                            notes="Débito Nubank",
                        ),
                        Posting(
                            account_id=uber.id,
                            amount=Money(Decimal(str(value)), "BRL"),
                            notes=f"Corrida {i}",
                        ),
                    ],
                    tags=["transport", "uber"],
                )
                uow.transactions.add(uber_txn)
                print(f"✅ Corrida #{i}: R$ {value} ({uber_date})")
            
            # ============================================
            # 6. Transferência entre Contas
            # ============================================
            print("\n🔄 6. Transferência entre Contas")
            print("-" * 60)
            
            transfer_date = date.today()
            transfer_txn = Transaction.create(
                description="Transferência Nubank → Itaú",
                date=transfer_date,
                postings=[
                    Posting(
                        account_id=nubank.id,
                        amount=Money(Decimal("-1000.00"), "BRL"),
                        notes="Saída Nubank",
                    ),
                    Posting(
                        account_id=itau.id,
                        amount=Money(Decimal("1000.00"), "BRL"),
                        notes="Entrada Itaú",
                    ),
                ],
                tags=["transfer", "internal"],
            )
            uow.transactions.add(transfer_txn)
            print(f"✅ {transfer_txn.description}")
            print(f"   Data: {transfer_date}")
            print(f"   Valor: R$ 1.000,00")
            
            # ============================================
            # 7. Entretenimento (Netflix)
            # ============================================
            print("\n🎬 7. Assinatura Netflix")
            print("-" * 60)
            
            netflix_date = date.today() - timedelta(days=1)
            netflix_txn = Transaction.create(
                description="Netflix - Assinatura Mensal",
                date=netflix_date,
                postings=[
                    Posting(
                        account_id=nubank.id,
                        amount=Money(Decimal("-45.90"), "BRL"),
                        notes="Débito automático",
                    ),
                    Posting(
                        account_id=entertainment.id,
                        amount=Money(Decimal("45.90"), "BRL"),
                        notes="Plano premium",
                    ),
                ],
                tags=["entertainment", "subscription", "monthly"],
            )
            uow.transactions.add(netflix_txn)
            print(f"✅ {netflix_txn.description}")
            print(f"   Data: {netflix_date}")
            print(f"   Valor: R$ 45,90")
            
            # Commit tudo
            uow.commit()
            
            print("\n" + "=" * 60)
            print("✅ Transações criadas com sucesso!")
            print("=" * 60)
            
            # Estatísticas
            all_transactions = uow.transactions.list_all()
            print(f"\n📊 Total de transações no sistema: {len(all_transactions)}")
            
            print("\n💡 Resumo:")
            print(f"  • Receitas: R$ 5.000,00")
            print(f"  • Despesas: R$ {1500 + 250.50 + 120 + 25.50 + 18 + 32.75 + 45.90:.2f}")
            print(f"  • Transferências: R$ 1.000,00 (não afeta saldo)")
            
            return True
            
    except ValueError as e:
        print(f"\n❌ Erro: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Erro ao criar transações: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Session handled by UnitOfWork context manager
        pass


if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║              FinApp - Criar Transações                        ║
    ║                                                               ║
    ║  Este exemplo demonstra como criar diferentes tipos de       ║
    ║  transações: receitas, despesas, transferências, etc.        ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    success = create_transactions()
    
    if success:
        print("\n🎉 Próximo passo: python examples/03_import_csv.py")
    else:
        print("\n❌ Falhou. Execute 01_setup_accounts.py primeiro!")
        sys.exit(1)
