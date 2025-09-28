from typer.testing import CliRunner

from finlite.cli.app import app

runner = CliRunner()
args = [
    "txn",
    "add",
    "Salary",
    "-p",
    "Assets=1000 BRL",
    "-p",
    "Income:Salary=-1000 BRL",
    "--occurred-at",
    "2025-08-01T08:00:00+00:00",
    "--reference",
    "payroll",
]
res = runner.invoke(app, args)
print("exit", res.exit_code)
print("exc", res.exception)
print("stdout:\n", res.stdout)
print("stderr:\n", res.stderr)
