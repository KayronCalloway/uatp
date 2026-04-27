# Contributing to UATP

## Quick Start

```bash
git clone https://github.com/KayronCalloway/uatp.git
cd uatp
python -m venv venv && source venv/bin/activate
pip install -e ".[dev]"
cd frontend && npm install && cd ..
```

Run tests: `pytest`
Run backend: `python -m uvicorn src.main:app --reload`
Run frontend: `cd frontend && npm run dev`

## What We Need

- **Bug fixes** — Check [open issues](https://github.com/KayronCalloway/uatp/issues)
- **Features** — See [ROADMAP.md](ROADMAP.md) or propose new ones
- **Documentation** — Fix typos, add examples, clarify unclear sections
- **Tests** — Edge cases, integration paths, failure modes

Look for [`good first issue`](https://github.com/KayronCalloway/uatp/labels/good%20first%20issue) labels.

## Making Changes

**Branch naming:**
- `feature/description` — New features
- `fix/description` — Bug fixes
- `docs/description` — Documentation

**Commits:** Follow [Conventional Commits](https://www.conventionalcommits.org/):
```
feat(scope): description
fix(scope): description
docs(scope): description
```

**Before opening a PR:**
- `pytest` passes
- `ruff check .` passes
- New code has tests
- Documentation updated if user-facing

## Code Style

**Python:** `ruff format` and `ruff check`. Type hints required. Google-style docstrings.

**TypeScript:** Prettier + ESLint. No `any` without justification.

## Security

**Do not open public issues for security vulnerabilities.**

Email: **Kayron@houseofcalloway.com** or use [GitHub private reporting](https://github.com/KayronCalloway/uatp/security/advisories/new)

See [SECURITY.md](SECURITY.md) for the full policy.

## Questions

- [GitHub Discussions](https://github.com/KayronCalloway/uatp/discussions) — General questions
- [Issues](https://github.com/KayronCalloway/uatp/issues) — Bug reports, feature requests
