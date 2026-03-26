# Contributing to UATP

Thank you for your interest in contributing to UATP! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Pull Request Process](#pull-request-process)
- [Code Style](#code-style)
- [Testing](#testing)
- [Security](#security)

## Code of Conduct

This project adheres to the [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

### Types of Contributions

- **Bug fixes** — Fix issues in the [issue tracker](https://github.com/KayronCalloway/uatp/issues)
- **Features** — Implement features from the roadmap or propose new ones
- **Documentation** — Improve docs, fix typos, add examples
- **Tests** — Increase coverage, add edge cases
- **Security** — Report vulnerabilities (see [Security](#security))

### Good First Issues

Look for issues labeled [`good first issue`](https://github.com/KayronCalloway/uatp/labels/good%20first%20issue) — these are designed for newcomers.

## Development Setup

### Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend)
- Git

### Clone and Install

```bash
# Clone the repository
git clone https://github.com/KayronCalloway/uatp.git
cd uatp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Frontend (optional)
cd frontend && npm install && cd ..
```

### Running Locally

```bash
# Backend only
python run.py

# Full stack (backend + frontend)
./start-dev.sh

# Run tests
pytest

# Run specific test file
pytest tests/unit/test_capsule.py -v
```

## Making Changes

### Branch Naming

- `feature/` — New features (e.g., `feature/add-export-csv`)
- `fix/` — Bug fixes (e.g., `fix/capsule-validation`)
- `docs/` — Documentation (e.g., `docs/api-examples`)
- `refactor/` — Code refactoring (e.g., `refactor/simplify-auth`)

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description

[optional body]

[optional footer]
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Examples:**
```
feat(auth): add cookie-based authentication
fix(capsules): handle null owner_id in stats query
docs(readme): add web dashboard section
```

## Pull Request Process

1. **Fork** the repository
2. **Create** a feature branch from `main`
3. **Make** your changes with clear commits
4. **Test** your changes (`pytest` must pass)
5. **Lint** your code (`ruff check .` must pass)
6. **Push** to your fork
7. **Open** a Pull Request with:
   - Clear description of changes
   - Link to related issue(s)
   - Screenshots (for UI changes)

### PR Checklist

- [ ] Tests pass locally (`pytest`)
- [ ] Linting passes (`ruff check .`)
- [ ] New code has tests
- [ ] Documentation updated (if needed)
- [ ] CHANGELOG.md updated (for user-facing changes)

### Review Process

- PRs require at least one approval
- CI must pass (tests, lint, security scans)
- Address reviewer feedback promptly

## Code Style

### Python

- **Formatter:** `ruff format`
- **Linter:** `ruff check`
- **Type hints:** Required for all new code
- **Docstrings:** Google style

```python
def create_capsule(
    task: str,
    decision: str,
    reasoning: list[dict],
) -> Capsule:
    """Create a new signed capsule.

    Args:
        task: Description of the task
        decision: The decision made
        reasoning: List of reasoning steps

    Returns:
        Signed Capsule object

    Raises:
        ValidationError: If input is invalid
    """
```

### TypeScript/JavaScript

- **Formatter:** Prettier
- **Linter:** ESLint
- **Types:** Required (no `any` without justification)

### Pre-commit Hooks

Pre-commit runs automatically on commit:
- `ruff` — Python linting/formatting
- `pyupgrade` — Python syntax upgrades
- Trailing whitespace removal
- End-of-file fixes

## Testing

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific markers
pytest -m "not slow"
pytest -m integration
```

### Writing Tests

- Place tests in `tests/` mirroring `src/` structure
- Use `pytest` fixtures for setup
- Aim for >80% coverage on new code
- Include edge cases and error conditions

```python
def test_capsule_creation_with_valid_input():
    """Test that valid input creates a signed capsule."""
    result = create_capsule(
        task="Test task",
        decision="Test decision",
        reasoning=[{"step": 1, "thought": "Test"}],
    )
    assert result.signature is not None
    assert len(result.signature) == 128  # Ed25519 hex
```

## Security

### Reporting Vulnerabilities

**Do NOT open public issues for security vulnerabilities.**

Instead:
1. Email: Kayron@houseofcalloway.com
2. Use GitHub's [private vulnerability reporting](https://github.com/KayronCalloway/uatp/security/advisories/new)

See [SECURITY.md](SECURITY.md) for full policy.

### Security Considerations

When contributing:
- Never commit secrets, keys, or credentials
- Validate all user input
- Use parameterized queries (no SQL injection)
- Follow the principle of least privilege

## Questions?

- [GitHub Discussions](https://github.com/KayronCalloway/uatp/discussions) — General questions
- [Issues](https://github.com/KayronCalloway/uatp/issues) — Bug reports, feature requests
- Email: Kayron@houseofcalloway.com

---

Thank you for contributing to UATP!
