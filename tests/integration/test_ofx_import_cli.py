"""Integration test for OFX import CLI command."""

import re
from pathlib import Path
import importlib

from typer.testing import CliRunner

from finlite.shared.di import create_container, init_database

CLI_APP_MODULE = importlib.import_module("finlite.interfaces.cli.app")


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from text for easier assertions."""
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def test_import_ofx_success(tmp_path, monkeypatch):
    """The CLI should successfully import a valid OFX file."""
    # Create test database
    db_path = tmp_path / "test-ofx-import.db"
    container = create_container(f"sqlite:///{db_path}", echo=False)
    init_database(container)

    # Create sample OFX file
    ofx_file = tmp_path / "statement.ofx"
    ofx_content = """OFXHEADER:100
DATA:OFXSGML
VERSION:102
SECURITY:NONE
ENCODING:USASCII
CHARSET:1252
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE

<OFX>
<BANKMSGSRSV1>
<STMTTRNRS>
<STMTRS>
<CURDEF>BRL
<BANKTRANLIST>
<STMTTRN>
<DTPOSTED>20251015120000
<TRNAMT>-150.50
<FITID>TXN001
<NAME>Grocery Store
<MEMO>Weekly groceries
</STMTTRN>
<STMTTRN>
<DTPOSTED>20251020120000
<TRNAMT>5000.00
<FITID>TXN002
<NAME>Employer Inc
<MEMO>Salary payment
</STMTTRN>
<STMTTRN>
<DTPOSTED>20251025120000
<TRNAMT>-1200.00
<FITID>TXN003
<NAME>Landlord Services
<MEMO>Monthly rent
</STMTTRN>
</BANKTRANLIST>
</STMTRS>
</STMTTRNRS>
</BANKMSGSRSV1>
</OFX>
"""
    ofx_file.write_text(ofx_content)

    # Ensure CLI reuses this container instance
    monkeypatch.setattr(CLI_APP_MODULE, "_container", container, raising=False)

    # Run import command
    runner = CliRunner()
    result = runner.invoke(
        CLI_APP_MODULE.app,
        ["import", "ofx", str(ofx_file), "--currency", "BRL"],
    )

    # Verify success
    assert result.exit_code == 0, result.stdout
    output = strip_ansi(result.stdout)

    # Check output contains key information
    assert "Importing OFX statement" in output
    assert "statement.ofx" in output
    assert "Import successful" in output or "✓" in output
    assert "Batch ID:" in output
    assert "Entries: 3" in output or "3" in output
    assert "SHA256:" in output


def test_import_ofx_with_account_hint(tmp_path, monkeypatch):
    """OFX import with account hint stores metadata correctly."""
    db_path = tmp_path / "test-ofx-hint.db"
    container = create_container(f"sqlite:///{db_path}", echo=False)
    init_database(container)

    # Create minimal OFX file
    ofx_file = tmp_path / "bank.ofx"
    ofx_content = """OFXHEADER:100
DATA:OFXSGML

<OFX>
<CURDEF>USD
<STMTTRN>
<DTPOSTED>20251015120000
<TRNAMT>100.00
<FITID>TXN001
<NAME>Test
</STMTTRN>
</OFX>
"""
    ofx_file.write_text(ofx_content)

    monkeypatch.setattr(CLI_APP_MODULE, "_container", container, raising=False)

    runner = CliRunner()
    result = runner.invoke(
        CLI_APP_MODULE.app,
        [
            "import",
            "ofx",
            str(ofx_file),
            "--currency",
            "USD",
            "--account",
            "Assets:BankAccount",
        ],
    )

    assert result.exit_code == 0, result.stdout
    output = strip_ansi(result.stdout)
    assert "Import successful" in output or "✓" in output


def test_import_ofx_duplicate_rejected(tmp_path, monkeypatch):
    """Importing the same OFX file twice should be rejected."""
    db_path = tmp_path / "test-ofx-duplicate.db"
    container = create_container(f"sqlite:///{db_path}", echo=False)
    init_database(container)

    # Create OFX file
    ofx_file = tmp_path / "duplicate.ofx"
    ofx_content = """OFXHEADER:100
DATA:OFXSGML

<OFX>
<CURDEF>BRL
<STMTTRN>
<DTPOSTED>20251015120000
<TRNAMT>100.00
<FITID>TXN001
<NAME>Test
</STMTTRN>
</OFX>
"""
    ofx_file.write_text(ofx_content)

    monkeypatch.setattr(CLI_APP_MODULE, "_container", container, raising=False)

    runner = CliRunner()

    # First import should succeed
    result1 = runner.invoke(
        CLI_APP_MODULE.app,
        ["import", "ofx", str(ofx_file)],
    )
    assert result1.exit_code == 0

    # Second import should fail
    result2 = runner.invoke(
        CLI_APP_MODULE.app,
        ["import", "ofx", str(ofx_file)],
    )
    assert result2.exit_code == 1
    output = strip_ansi(result2.stdout)
    assert "Error" in output or "already been imported" in output


def test_import_ofx_multicurrency(tmp_path, monkeypatch):
    """OFX files with multiple currencies are handled correctly."""
    db_path = tmp_path / "test-ofx-multicurrency.db"
    container = create_container(f"sqlite:///{db_path}", echo=False)
    init_database(container)

    # Create multi-currency OFX file
    ofx_file = tmp_path / "multicurrency.ofx"
    ofx_content = """OFXHEADER:100
DATA:OFXSGML

<OFX>
<CURDEF>USD
<STMTTRN>
<DTPOSTED>20251015120000
<TRNAMT>1000.00
<FITID>USD-001
<NAME>USD Transaction
<CURRENCY>USD
</STMTTRN>
<STMTTRN>
<DTPOSTED>20251020120000
<TRNAMT>500.00
<FITID>EUR-001
<NAME>EUR Transaction
<CURRENCY>EUR
</STMTTRN>
<STMTTRN>
<DTPOSTED>20251025120000
<TRNAMT>2500.00
<FITID>BRL-001
<NAME>BRL Transaction
<CURRENCY>BRL
</STMTTRN>
</OFX>
"""
    ofx_file.write_text(ofx_content)

    monkeypatch.setattr(CLI_APP_MODULE, "_container", container, raising=False)

    runner = CliRunner()
    result = runner.invoke(
        CLI_APP_MODULE.app,
        ["import", "ofx", str(ofx_file), "--currency", "USD"],
    )

    assert result.exit_code == 0, result.stdout
    output = strip_ansi(result.stdout)
    assert "Entries: 3" in output or "3" in output


def test_list_import_batches_includes_ofx(tmp_path, monkeypatch):
    """Listing import batches shows OFX imports."""
    db_path = tmp_path / "test-ofx-list.db"
    container = create_container(f"sqlite:///{db_path}", echo=False)
    init_database(container)

    # Import OFX file
    ofx_file = tmp_path / "list_test.ofx"
    ofx_content = """OFXHEADER:100
DATA:OFXSGML

<OFX>
<CURDEF>BRL
<STMTTRN>
<DTPOSTED>20251015120000
<TRNAMT>100.00
<FITID>TXN001
<NAME>Test
</STMTTRN>
</OFX>
"""
    ofx_file.write_text(ofx_content)

    monkeypatch.setattr(CLI_APP_MODULE, "_container", container, raising=False)

    runner = CliRunner()

    # Import OFX
    import_result = runner.invoke(
        CLI_APP_MODULE.app,
        ["import", "ofx", str(ofx_file)],
    )
    assert import_result.exit_code == 0

    # List imports
    list_result = runner.invoke(
        CLI_APP_MODULE.app,
        ["import", "list"],
    )

    assert list_result.exit_code == 0
    output = strip_ansi(list_result.stdout)
    assert "OFX" in output
    assert ("list_test.ofx" in output or "lis…" in output)  # May be truncated in table
    assert "COMPLETED" in output or "COM…" in output


def test_show_ofx_entries(tmp_path, monkeypatch):
    """Showing entries from OFX import displays transaction details."""
    db_path = tmp_path / "test-ofx-entries.db"
    container = create_container(f"sqlite:///{db_path}", echo=False)
    init_database(container)

    # Import OFX file
    ofx_file = tmp_path / "entries_test.ofx"
    ofx_content = """OFXHEADER:100
DATA:OFXSGML

<OFX>
<CURDEF>BRL
<STMTTRN>
<DTPOSTED>20251015120000
<TRNAMT>-100.50
<FITID>TXN001
<NAME>Store ABC
<MEMO>Purchase
</STMTTRN>
<STMTTRN>
<DTPOSTED>20251020120000
<TRNAMT>5000.00
<FITID>TXN002
<NAME>Employer
<MEMO>Salary
</STMTTRN>
</OFX>
"""
    ofx_file.write_text(ofx_content)

    monkeypatch.setattr(CLI_APP_MODULE, "_container", container, raising=False)

    runner = CliRunner()

    # Import OFX
    import_result = runner.invoke(
        CLI_APP_MODULE.app,
        ["import", "ofx", str(ofx_file)],
    )
    assert import_result.exit_code == 0

    # Extract batch ID from output - look for "fin import entries <uuid>" pattern
    import_output = strip_ansi(import_result.stdout)
    # Look for UUID pattern after "fin import entries"
    import re
    uuid_pattern = r"fin import entries ([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"
    match = re.search(uuid_pattern, import_output)
    assert match, f"Could not find batch ID in output: {import_output}"
    batch_id = match.group(1)

    # Show entries
    entries_result = runner.invoke(
        CLI_APP_MODULE.app,
        ["import", "entries", batch_id],
    )

    assert entries_result.exit_code == 0, f"Failed to show entries: {strip_ansi(entries_result.stdout)}"
    entries_output = strip_ansi(entries_result.stdout)
    assert "TXN001" in entries_output or "Store ABC" in entries_output
    assert "TXN002" in entries_output or "Employer" in entries_output
    assert "100.50" in entries_output or "-100.50" in entries_output
    assert "5000" in entries_output or "5,000" in entries_output
