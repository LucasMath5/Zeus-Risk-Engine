# Contributing to Zeus Risk Engine

Thank you for helping improve Zeus Risk Engine. Contributions should preserve the
project's educational character, quantitative transparency, and separation between
the user interface and the core.

Author: Lucas Silva

## Before contributing

Read the following documents first:

- [Product vision](docs/product-vision.md)
- [Scope](docs/scope.md)
- [Architecture overview](docs/architecture/overview.md)
- [Development roadmap](docs/development/roadmap.md)
- [Basic analytics formulas and conventions](docs/concepts/basic-analytics.md)
- [Historical VaR formulas and conventions](docs/concepts/historical-var.md)
- [Historical Expected Shortfall formulas](docs/concepts/historical-expected-shortfall.md)
- [ADR-001: separation of UI and core](docs/decisions/ADR-001-separation-of-ui-and-core.md)
- [ADR-004: historical VaR conventions](docs/decisions/ADR-004-historical-var-conventions.md)
- [ADR-005: Expected Shortfall conventions](docs/decisions/ADR-005-historical-expected-shortfall-conventions.md)

Do not implement a later phase merely because it is listed in the roadmap. Each
change should have a bounded objective, acceptance criteria, tests, documentation,
and an explicit relationship to the active phase.

## Development setup

Zeus Risk Engine requires Python 3.11 or newer.

```bash
python -m venv .venv
```

Activate the environment on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Or on Linux and macOS:

```bash
source .venv/bin/activate
```

Install the package and development tools:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Required quality checks

Run the same checks used by continuous integration:

```bash
python -m ruff check .
python -m ruff format --check .
python -m mypy src tests
python -m pytest --cov=zeus_risk --cov-report=term-missing
python -m build
```

Ruff is both the linter and formatter. Black is intentionally not configured to
avoid overlapping formatters. Mypy runs in strict mode for the package and tests.

## Code guidelines

- Use type hints for public and internal application code.
- Prefer small functions, dataclasses, protocols, enums, and composition.
- Keep domain and quantitative code independent of PySide6.
- Do not place business rules or financial formulas in widgets or controllers.
- Use explicit, domain-specific exceptions when an operation cannot fulfill its
  contract.
- Represent expected validation problems as structured values with stable codes.
- Avoid global dependencies, silent exception handling, and premature abstractions.
- Add a dependency only when a current use case needs it and document why.

## Quantitative changes

A change that introduces or modifies a formula must document:

1. definition and notation;
2. formula and sign convention;
3. assumptions and supported parameter domain;
4. a manually verifiable example;
5. interpretation and limitations;
6. edge cases and failure behavior;
7. numerical tolerance and test strategy.

Use synthetic or public data. Unit tests must not call external services. Fixed
seeds are required whenever randomness is involved.

## Tests

- Unit tests cover invariants, validation, and pure calculations.
- Integration tests cover package boundaries such as CLI, files, providers, and
  persistence.
- Regression tests preserve reviewed numerical examples.
- GUI tests cover presentation state and coordination, not every mathematical case.

Never remove or weaken a test merely to make the pipeline pass. If behavior changes
intentionally, explain the reason and update its documentation and changelog.

## Documentation and commits

Update documentation in the same change as the behavior it describes. Significant
architectural choices require a new ADR or an explicit superseding ADR.

Use Conventional Commits, for example:

```text
feat(portfolio): add immutable position model
fix(import): preserve row number in validation issues
docs: explain historical VaR sign convention
test(analytics): add volatility regression fixture
```

Keep commits focused and do not include generated build artifacts, local databases,
credentials, confidential portfolios, or API keys.

## Responsible use

This project is intended for educational, research, and portfolio purposes. It does
not constitute financial advice and must not be presented as a certified production
risk system.
