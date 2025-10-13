# Contributing to Finlite

Thank you for your interest in contributing to Finlite! This guide will help you get started.

---

## 🎯 Ways to Contribute

- 🐛 **Report Bugs**: Found an issue? Let us know!
- 💡 **Suggest Features**: Have an idea? We'd love to hear it!
- 📖 **Improve Documentation**: Help others understand Finlite better
- 🔧 **Submit Code**: Fix bugs or implement features
- ✅ **Write Tests**: Help us maintain quality
- 🎨 **Improve UX**: Make the CLI more user-friendly

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- Basic understanding of double-entry accounting (helpful but not required)

### Development Setup

1. **Fork the repository** on GitHub

2. **Clone your fork**:
```bash
git clone https://github.com/YOUR_USERNAME/finapp.git
cd finapp/backend
```

3. **Create a virtual environment**:
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

4. **Install development dependencies**:
```bash
pip install -e ".[dev]"
```

5. **Run tests to verify setup**:
```bash
pytest tests/
```

---

## 📋 Development Workflow

### 1. Create a Branch

Always create a new branch for your changes:

```bash
git checkout -b feature/my-amazing-feature
# or
git checkout -b fix/bug-description
```

**Branch naming conventions**:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `test/` - Test additions/improvements
- `refactor/` - Code refactoring

### 2. Make Your Changes

Follow our [code style guidelines](#code-style) and write tests for your changes.

### 3. Run Quality Checks

Before committing, ensure all checks pass:

```bash
# Run tests
pytest tests/

# Type checking
mypy finlite

# Linting
ruff check .

# Format code
ruff format .
```

### 4. Commit Your Changes

Write clear, descriptive commit messages:

```bash
git add .
git commit -m "feat: add account deactivation feature"
```

**Commit message format**:
```
type(scope): subject

body (optional)

footer (optional)
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions/improvements
- `refactor`: Code refactoring
- `style`: Code style changes (formatting, etc.)
- `chore`: Maintenance tasks

**Examples**:
```bash
feat(accounts): add multi-currency support
fix(transactions): validate posting balance correctly
docs(readme): update installation instructions
test(domain): add transaction validation tests
```

### 5. Push and Create Pull Request

```bash
git push origin feature/my-amazing-feature
```

Then open a Pull Request on GitHub with:
- Clear description of changes
- Link to related issues
- Screenshots (if applicable)

---

## 🧪 Testing Guidelines

### Writing Tests

- Write tests for all new features
- Maintain or improve test coverage
- Use descriptive test names
- Follow the existing test structure

### Test Structure

```python
def test_create_account_with_valid_data():
    """Test account creation with valid parameters."""
    # Arrange
    account_repo = Mock(spec=IAccountRepository)
    event_bus = Mock(spec=IEventBus)
    use_case = CreateAccountUseCase(account_repo, event_bus)
    
    # Act
    account = use_case.execute(
        code="TEST",
        name="Test Account",
        account_type=AccountType.ASSET,
    )
    
    # Assert
    assert account.code == "TEST"
    assert account.name == "Test Account"
    account_repo.save.assert_called_once()
```

### Running Tests

```bash
# All tests
pytest tests/

# Specific test file
pytest tests/unit/domain/test_account.py

# Specific test
pytest tests/unit/domain/test_account.py::test_create_account

# With coverage
pytest tests/ --cov=finlite --cov-report=html

# Watch mode (requires pytest-watch)
ptw tests/
```

---

## 📐 Code Style

### Python Style Guide

Finlite follows **PEP 8** with some modifications enforced by **Ruff**.

**Key points**:
- Line length: 100 characters
- Use type hints for all functions
- Docstrings for public APIs
- F-strings for string formatting

### Type Hints

Always use type hints:

```python
# ✅ Good
def create_account(
    code: str,
    name: str,
    account_type: AccountType,
) -> Account:
    """Create a new account."""
    ...

# ❌ Bad
def create_account(code, name, account_type):
    """Create a new account."""
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def calculate_balance(
    account_id: UUID,
    as_of_date: date | None = None,
) -> Decimal:
    """Calculate account balance up to a specific date.
    
    Args:
        account_id: The account UUID.
        as_of_date: Date to calculate balance up to. Defaults to now.
    
    Returns:
        The account balance as a Decimal.
    
    Raises:
        AccountNotFoundError: If account doesn't exist.
    """
    ...
```

### Import Organization

Follow this order:
1. Standard library
2. Third-party packages
3. Local imports

```python
# Standard library
from datetime import datetime
from decimal import Decimal
from uuid import UUID

# Third-party
from sqlalchemy.orm import Session

# Local
from finlite.domain.entities import Account
from finlite.domain.repositories import IAccountRepository
```

---

## 🏗️ Architecture Guidelines

Finlite follows **Clean Architecture**. Please respect layer boundaries:

### Domain Layer

- **No external dependencies**
- Pure business logic
- Entities, value objects, domain events

```python
# ✅ Good - Pure domain logic
@dataclass
class Account:
    id: UUID
    code: str
    name: str
    
    def deactivate(self) -> None:
        """Deactivate the account."""
        self.is_active = False

# ❌ Bad - Don't reference infrastructure in domain
@dataclass
class Account:
    def save_to_database(self, session: Session) -> None:
        # NO! Domain shouldn't know about database
        ...
```

### Application Layer

- Orchestrate business operations
- Use cases are the entry points
- Depend on domain and repository interfaces

```python
# ✅ Good - Use case coordinates
class CreateAccountUseCase:
    def __init__(
        self,
        account_repo: IAccountRepository,  # Interface, not implementation
        event_bus: IEventBus,
    ):
        self._account_repo = account_repo
        self._event_bus = event_bus
    
    def execute(self, code: str, name: str) -> Account:
        account = Account.create(code, name)
        self._account_repo.save(account)
        self._event_bus.publish(AccountCreated(...))
        return account
```

### Infrastructure Layer

- Implement repository interfaces
- Database, external APIs, file system
- Can depend on domain

```python
# ✅ Good - Implements interface
class SQLAlchemyAccountRepository(IAccountRepository):
    def __init__(self, session: Session):
        self._session = session
    
    def save(self, account: Account) -> None:
        model = AccountModel.from_entity(account)
        self._session.add(model)
        self._session.commit()
```

---

## 📝 Documentation

### Code Documentation

- Add docstrings to public APIs
- Use type hints extensively
- Comment complex logic

### User Documentation

When adding features, update:
- `docs/` - MkDocs documentation
- `CLI_GUIDE.md` - CLI usage examples
- `README.md` - If applicable

---

## 🐛 Reporting Bugs

### Before Reporting

1. Check [existing issues](https://github.com/lgili/finapp/issues)
2. Try the latest version
3. Gather relevant information

### Bug Report Template

```markdown
## Bug Description
Clear description of the bug.

## Steps to Reproduce
1. Run `fin accounts create ...`
2. Run `fin transactions create ...`
3. Error occurs

## Expected Behavior
What should happen.

## Actual Behavior
What actually happens.

## Environment
- OS: macOS 14.0
- Python: 3.11.5
- Finlite: 0.1.0

## Additional Context
Any other relevant information.
```

---

## 💡 Feature Requests

### Feature Request Template

```markdown
## Feature Description
Clear description of the feature.

## Use Case
Why is this feature needed? What problem does it solve?

## Proposed Solution
How should it work? (Optional)

## Alternatives Considered
Other approaches you've thought about. (Optional)

## Additional Context
Any other relevant information.
```

---

## 🔍 Code Review Process

### For Contributors

- Be patient and respectful
- Respond to feedback promptly
- Make requested changes
- Keep PR scope focused

### For Reviewers

- Be constructive and kind
- Explain the "why" behind suggestions
- Approve when ready
- Merge after approval

---

## ✅ Pull Request Checklist

Before submitting a PR, ensure:

- [ ] Code follows style guidelines
- [ ] All tests pass (`pytest tests/`)
- [ ] Type checking passes (`mypy finlite`)
- [ ] Linting passes (`ruff check .`)
- [ ] Code is formatted (`ruff format .`)
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] Commit messages follow convention
- [ ] PR description is clear

---

## 🎓 Learning Resources

### Clean Architecture

- [Clean Architecture Overview](../architecture/overview.md)
- [Domain Layer](../architecture/domain.md)
- [Application Layer](../architecture/application.md)

### Double-Entry Accounting

- [Double-Entry Guide](../user-guide/double-entry.md)
- [Accounting Basics](https://www.investopedia.com/terms/d/double-entry.asp)

### Python & Tools

- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Pytest Documentation](https://docs.pytest.org/)
- [Ruff Linter](https://docs.astral.sh/ruff/)

---

## 📞 Getting Help

Need help contributing?

- 💬 [GitHub Discussions](https://github.com/lgili/finapp/discussions)
- 🐛 [Issue Tracker](https://github.com/lgili/finapp/issues)
- 📖 [Documentation](https://lgili.github.io/finapp/)

---

## 📜 Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for all.

### Expected Behavior

- Be respectful and inclusive
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards others

### Unacceptable Behavior

- Harassment or discrimination
- Trolling or insulting comments
- Public or private harassment
- Publishing others' private information

### Enforcement

Violations may result in temporary or permanent ban from the project.

---

## 🏆 Recognition

Contributors are recognized in:
- `CONTRIBUTORS.md` file
- Release notes
- GitHub contributors page

Thank you for making Finlite better! 🎉

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
