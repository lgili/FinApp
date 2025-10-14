"""
Exemplo 03 - Importar CSV
==========================

Este script demonstra como importar um extrato CSV do Nubank.

Execução:
    python examples/03_import_csv.py
"""
"""
Exemplo 03 - Importar CSV
==========================

Este script demonstra como importar um extrato CSV do Nubank.

Execução:
    python examples/03_import_csv.py
"""

import sys
from pathlib import Path

# Adicionar backend ao path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from finlite.application.use_cases.import_nubank_statement import (
    ImportNubankStatement,
    ImportNubankStatementCommand,
)
from finlite.domain.exceptions import DuplicateImportError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from finlite.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from finlite.infrastructure.persistence.sqlalchemy import models
from finlite.infrastructure.persistence.sqlalchemy.repositories.import_batch_repository import (
    SqlAlchemyImportBatchRepository,
)
from finlite.infrastructure.persistence.sqlalchemy.repositories.statement_entry_repository import (
    SqlAlchemyStatementEntryRepository,
)
from finlite.shared.event_bus import InMemoryEventBus


def import_csv() -> bool:
    """Importa CSV de exemplo do Nubank."""

    # Path do CSV
    csv_file = Path(__file__).parent / "data" / "nubank_example.csv"

    if not csv_file.exists():
        print(f"❌ Arquivo não encontrado: {csv_file}")
        print("\n💡 O arquivo deveria estar em: examples/data/nubank_example.csv")
        return False

    print("📥 Importando extrato CSV do Nubank...")
    print("=" * 60)
    print(f"📄 Arquivo: {csv_file.name}")
    print(f"📍 Path: {csv_file}")
    print("=" * 60)

    engine = create_engine("sqlite:///backend/finlite.db", echo=False)
    models.Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    uow = SqlAlchemyUnitOfWork(session_factory)

    # Cria sessão que será usada para persistência durante o import
    repo_session = uow.session_factory()
    batch_repo = SqlAlchemyImportBatchRepository(repo_session)
    entry_repo = SqlAlchemyStatementEntryRepository(repo_session)
    event_bus = InMemoryEventBus()

    use_case = ImportNubankStatement(
        import_batch_repository=batch_repo,
        statement_entry_repository=entry_repo,
        event_bus=event_bus,
    )

    command = ImportNubankStatementCommand(
        file_path=csv_file,
        default_currency="BRL",
        account_hint="Assets:Bank:Nubank",
    )

    print("\n🔄 Processando CSV...")

    try:
        # Executar importação
        result = use_case.execute(command)

        # Commit para persistir alterações
        repo_session.commit()

        print("\n✅ Importação concluída com sucesso!")
        print("=" * 60)
        print(f"📦 Batch ID: {result.batch_id}")
        print(f"📊 Entries importadas: {result.entries_count}")
        print(f"🔐 SHA256: {result.file_sha256[:16]}...")
        print("=" * 60)

        # Buscar e mostrar algumas entries usando o repository
        print("\n📋 Primeiras 5 entries importadas:")
        print("-" * 60)

        entries = entry_repo.find_by_batch(result.batch_id)

        if not entries:
            print("(nenhuma entry encontrada)")
        else:
            for i, entry in enumerate(entries[:5], 1):
                print(f"\n{i}. {entry.memo}")
                print(f"   Data: {entry.occurred_at}")
                print(f"   Valor: R$ {abs(entry.amount):.2f}")
                print(f"   Moeda: {entry.currency}")
                print(f"   Status: {entry.status}")
                print(f"   External ID: {entry.external_id}")

            if len(entries) > 5:
                print(f"\n   ... e mais {len(entries) - 5} entries")

            # Estatísticas
            total_amount = sum(abs(e.amount) for e in entries)
            print("\n" + "=" * 60)
            print("📊 Estatísticas:")
            print(f"  • Total de transações: {len(entries)}")
            print(f"  • Valor total: R$ {total_amount:.2f}")
            print(
                f"  • Período: {min(e.occurred_at for e in entries)} até {max(e.occurred_at for e in entries)}"
            )
            print("=" * 60)

        # Tentar importar novamente para demonstrar detecção de duplicatas
        print("\n" + "=" * 60)
        print("🔄 Testando detecção de duplicatas...")
        print("-" * 60)

        try:
            _ = use_case.execute(command)
            print("❌ ERRO: Deveria ter detectado duplicata!")
            return False
        except DuplicateImportError:
            print("✅ Duplicata detectada corretamente!")
            print("   O sistema impediu a reimportação do mesmo arquivo")

        return True
    except DuplicateImportError as e:
        print(f"\n⚠️  Arquivo já foi importado anteriormente!")
        print(f"   SHA256: {e}")
        print("\n💡 Para reimportar:")
        print("   1. Apague o batch existente do banco")
        print("   2. Ou use um arquivo CSV diferente")
        return True
    except Exception as e:
        print(f"\n❌ Erro durante importação: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            repo_session.close()
        except Exception:
            pass


if __name__ == "__main__":
    print("""
FinApp - Importar CSV

Este exemplo importa um extrato CSV do Nubank e demonstra a
detecção automática de duplicatas via SHA256.
""")

    success = import_csv()

    if success:
        print("\n🎉 Próximo passo: python examples/04_query_data.py")
    else:
        print("\n❌ Falhou. Verifique os erros acima.")
        sys.exit(1)
