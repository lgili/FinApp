# Contributing guide

1. Create a feature branch.
2. Install dev dependencies (`pip install -e .[dev]` inside `backend/`).
3. Run quality gates locally:
   - `ruff check .`
   - `mypy .`
   - `pytest`
4. Format with `ruff format`.
5. Submit a PR referencing the roadmap phase.
