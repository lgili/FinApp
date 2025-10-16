# GitHub Actions CI/CD

This directory contains GitHub Actions workflows for continuous integration and deployment.

## Workflows

### CI Pipeline (`ci.yml`)

Comprehensive continuous integration pipeline that runs on every push to `main` and on all pull requests.

#### Jobs

**1. Test Suite**
- Runs on: Python 3.11, 3.12, 3.13
- Steps:
  - Run unit tests with coverage
  - Run integration tests
  - Run smoke tests
  - Upload coverage to Codecov (Python 3.11 only)

**2. Code Quality**
- Linting with ruff
- Format checking with ruff
- Type checking with mypy

**3. Examples & Documentation**
- Syntax check for example scripts
- Run all example scripts (smoke test)
- Test CLI commands

**4. Security Scan**
- Dependency vulnerability check with safety
- Static security analysis with bandit

## Running Locally

To run the same checks locally:

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e backend/

# Run tests
export PYTHONPATH="${PWD}/backend"
pytest tests/ -v --cov=finlite --cov-report=term-missing

# Linting
ruff check backend/finlite
ruff format --check backend/finlite

# Type checking
mypy backend/finlite

# Run examples
bash examples/run_all.sh
```

## Badge Status

Add these badges to your README:

```markdown
[![CI](https://github.com/lgili/finapp/actions/workflows/ci.yml/badge.svg)](https://github.com/lgili/finapp/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-275%20passing-success)](https://github.com/lgili/finapp/actions)
[![Coverage](https://img.shields.io/badge/coverage-69%25-yellow)](https://github.com/lgili/finapp)
```

## Test Results

Current status:
- ✅ 275 tests passing
- ✅ 252 unit tests
- ✅ 23 integration tests
- ✅ 69% code coverage
- ✅ 0 linting errors
- ✅ Type check passing
