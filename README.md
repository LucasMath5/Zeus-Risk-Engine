# Zeus Risk Engine

> **Temporary visual identity:** geometric lightning bolt + letter Z. A final logo
> will be introduced with the desktop assets, without blocking the engineering work.

[![Quality](https://github.com/LucasMath5/Zeus-Risk-Engine/actions/workflows/quality.yml/badge.svg)](https://github.com/LucasMath5/Zeus-Risk-Engine/actions/workflows/quality.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-0B7285.svg)](LICENSE)

Zeus Risk Engine is a modular desktop application for importing, validating,
analyzing, and monitoring the risk of financial portfolios. It is designed as a
professional software-engineering and quantitative-finance portfolio project, with
an emphasis on reproducibility, auditability, clear assumptions, and learning.

**Current status:** Phase 1 — repository foundation. The package and quality pipeline
are executable, but portfolio models and risk calculations have not been implemented.

Author: Lucas Silva

## Objectives

- provide a complete path from portfolio import to reproducible risk results;
- make validation errors and non-fatal warnings explicit and actionable;
- keep the quantitative engine independent from the PySide6 interface;
- accompany metrics with parameters, interpretation, assumptions, and limitations;
- use automated tests and reviewed numerical examples from the earliest model phases;
- preserve enough metadata to audit and reproduce analyses.

## Current functionality

The current foundation provides:

- an installable `zeus_risk` package at version `0.1.0`;
- `zeus-risk` and `python -m zeus_risk` command-line entry points;
- project metadata and a `src` package layout;
- automated tests, coverage, linting, formatting, and strict type checking;
- continuous integration on supported Python and operating-system combinations;
- product, scope, architecture, roadmap, glossary, and decision documentation.

Run the current entry point:

```text
$ zeus-risk --version
Zeus Risk Engine 0.1.0
```

## Planned functionality

The project will add capabilities incrementally:

- portfolio domain models and validation;
- CSV and XLSX portfolio import;
- local market-data providers and cache;
- returns, volatility, correlation, covariance, drawdown, and concentration;
- historical and parametric VaR, Expected Shortfall, and EWMA;
- PySide6 portfolio and results workflows;
- versioned projects and risk configurations;
- backtesting, stress testing, SQLite history, and reproducible reports;
- Monte Carlo simulation and controlled model extensibility.

The complete sequence and exit criteria are documented in the
[development roadmap](docs/development/roadmap.md).

## Demonstration and screenshots

Screenshots and a reproducible demonstration will be added when the first PySide6
workflow is implemented. The project deliberately avoids mock screenshots that could
be mistaken for currently available behavior.

## Architecture

Zeus Risk Engine is planned as a modular desktop monolith with inward-pointing
dependencies:

```text
PySide6 application  ──>  application use cases  ──>  domain + quantitative core
                                  ^                         ^
                                  │                         │
files / databases / APIs ──> adapters and infrastructure ──┘
```

The domain and quantitative core do not import PySide6. Files, market-data sources,
exporters, and future persistence are adapters behind internal contracts. Long-running
desktop tasks will wrap synchronous, testable use cases rather than placing Qt types in
the core.

See the [architecture overview](docs/architecture/overview.md) and
[ADR-001](docs/decisions/ADR-001-separation-of-ui-and-core.md) for the rationale and
enforceable dependency rules.

## Requirements

- Python 3.11 or newer;
- Git for cloning the repository;
- internet access only to install development packages.

The Phase 1 runtime has no third-party dependency. Basic commands and tests do not
call external services.

## Installation

Clone the repository and enter its directory:

```bash
git clone https://github.com/LucasMath5/Zeus-Risk-Engine.git
cd Zeus-Risk-Engine
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Or on Linux and macOS:

```bash
source .venv/bin/activate
```

Install only the application package:

```bash
python -m pip install -e .
```

For development, install the optional quality tools:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

PySide6 is intentionally absent from this phase and will be added with the first
graphical workflow.

## Execution

After installation, both commands are equivalent:

```bash
zeus-risk --version
python -m zeus_risk --version
```

Run either command without arguments to display the current help. Portfolio import and
risk commands are not exposed until their domain and use cases have automated tests.

## Tests and quality

Run the complete local verification:

```bash
python -m ruff check .
python -m ruff format --check .
python -m mypy src tests
python -m pytest --cov=zeus_risk --cov-report=term-missing
python -m build
```

The project does not impose an artificial coverage threshold during the foundation
phase. Coverage is reported so gaps can be reviewed, and thresholds can increase when
the domain and quantitative modules exist.

## Documentation

- [Product vision](docs/product-vision.md)
- [Scope](docs/scope.md)
- [Use cases](docs/use-cases.md)
- [Glossary](docs/glossary.md)
- [Architecture overview](docs/architecture/overview.md)
- [Development roadmap](docs/development/roadmap.md)
- [Architecture decisions](docs/decisions/)
- [Contribution guide](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## Roadmap

The next planned phase is **Phase 2 — Portfolio domain modeling**, covering
`Instrument`, `Position`, `Portfolio`, structured validation, market value, weights,
and their unit tests. Advanced models will only be introduced in their documented
phases.

## License

Zeus Risk Engine is available under the [MIT License](LICENSE).

Author: Lucas Silva

## Responsible-use notice

This project is intended for educational, research and portfolio purposes.
It does not constitute financial advice and should not be used as the sole
basis for investment or risk-management decisions.

Quantitative results depend on data quality, model assumptions, implementation
choices, and parameter suitability. A model result is not a guarantee of future loss
or performance.
