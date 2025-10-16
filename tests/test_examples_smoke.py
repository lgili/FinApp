import os
import subprocess
import sys
import pytest


HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, ".."))


@pytest.mark.parametrize(
    "script",
    [
        "examples/01_setup_accounts.py",
        "examples/02_create_transactions.py",
        "examples/03_import_csv.py",
        "examples/04_query_data.py",
    ],
)
def test_run_example_scripts(script):
    """Smoke test: execute example scripts as subprocesses and expect zero exit code."""
    env = os.environ.copy()
    env["PYTHONPATH"] = env.get("PYTHONPATH", "") + ":" + os.path.join(ROOT, "backend")

    # Use python executable from the environment
    cmd = [sys.executable, os.path.join(ROOT, script)]
    proc = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
    out = proc.stdout.decode(errors="replace")
    # On failure, include output for debugging
    assert proc.returncode == 0, f"Script {script} failed with exit {proc.returncode}\nOutput:\n{out}"
