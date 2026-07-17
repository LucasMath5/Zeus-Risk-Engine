# Zeus Risk Engine

> **Temporary visual identity:** the desktop header uses the letter Z while a final,
> distributable icon set remains intentionally deferred.

[![Quality](https://github.com/LucasMath5/Zeus-Risk-Engine/actions/workflows/quality.yml/badge.svg)](https://github.com/LucasMath5/Zeus-Risk-Engine/actions/workflows/quality.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-0B7285.svg)](LICENSE)

Zeus Risk Engine is a modular desktop application for importing, validating,
analyzing, and monitoring the risk of financial portfolios. It is designed as a
professional software-engineering and quantitative-finance portfolio project, with
an emphasis on reproducibility, auditability, clear assumptions, and learning.

**Current status:** Phase 10 — projects and configurations. The desktop workflow now
saves and reopens strict, versioned `*.zeus.json` project files that restore portfolio
and local-price references plus the complete historical-risk configuration.

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
- immutable `Currency`, `Instrument`, `Position`, and `Portfolio` domain models;
- structured validation issues with stable machine-readable codes;
- signed and gross market values separated by currency;
- net and gross position weights with explicit denominator conventions;
- validated UTF-8 CSV import with controlled delimiter detection;
- resource-bounded XLSX import with explicit worksheet selection;
- Portuguese and English header aliases, row-level status, and partial results;
- formula and unsupported-cell rejection without executing workbook content;
- immutable daily price-series, observation, metadata, and result contracts;
- offline long-format CSV market-data provider with explicit missing-price policy;
- deterministic intersection/union alignment without implicit price filling;
- SHA-256-addressed, schema-versioned JSON market-data cache with atomic writes;
- simple and logarithmic asset returns with complete-data enforcement;
- constant signed net-weight portfolio returns for single-currency portfolios;
- sample/population variance, volatility, covariance, and correlation;
- explicit daily annualization, cumulative wealth, drawdown, and maximum drawdown;
- gross-weight Herfindahl concentration and effective position count;
- immutable analytics results and structured failures without `NaN` success states;
- immutable historical VaR configuration and result contracts;
- rolling simple/log horizon scenarios with deterministic recent-window selection;
- positive-loss nearest-rank historical VaR with explicit tail-resolution safeguards;
- historical Expected Shortfall over ranks beyond VaR with deterministic tie handling;
- reconciled VaR/ES results preserving raw loss thresholds, tail means, and samples;
- a Qt Widgets desktop entry point with a guided portfolio-to-risk workflow;
- read-only model/view tables for accepted positions and structured validation issues;
- explicit confidence, horizon, window, price-source, readiness, success, and failure states;
- a PySide-free application service that composes import, market data, analytics, VaR, and ES;
- headless GUI tests for bootstrap, table models, workflow success, and structured failures;
- immutable `DesktopProject` snapshots and strict schema `1.0` JSON persistence;
- atomic project saves, exact-field validation, duplicate detection, and size safeguards;
- relative references for files inside the project tree and explicit missing-file errors;
- desktop open/save/save-as actions and a visible unsaved-change marker;
- a ready-to-open synthetic project reproducing the historical-risk example;
- synthetic offline portfolio/price samples and generated XLSX test workbooks;
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

- interactive portfolio column mapping;
- parametric VaR, parametric Expected Shortfall, and EWMA;
- richer result exploration and charts;
- backtesting, stress testing, SQLite history, and reproducible reports;
- Monte Carlo simulation and controlled model extensibility.

The complete sequence and exit criteria are documented in the
[development roadmap](docs/development/roadmap.md).

## Demonstration

The [first desktop workflow tutorial](docs/tutorials/first-desktop-workflow.md) and
[project tutorial](docs/tutorials/save-and-reopen-project.md) use only synthetic files
in `assets/samples`. You can directly open
`assets/samples/historical-risk-demo.zeus.json` in the real application.

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
- internet access to install Python dependencies; execution remains offline.

Runtime dependencies are `openpyxl` and `defusedxml` for the XLSX adapter plus PySide6
for the desktop application. Basic commands, imports, tests, examples, and the local
risk workflow do not call external services.

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

## Execution

Start the desktop application:

```bash
zeus-risk-gui
```

The module entry point is equivalent:

```bash
python -m zeus_risk.app
```

The minimal CLI remains available for installation and version smoke tests:

```bash
zeus-risk --version
python -m zeus_risk --version
```

Follow the [desktop tutorial](docs/tutorials/first-desktop-workflow.md) to run the
included portfolio and price samples through VaR and Expected Shortfall.
The [project tutorial](docs/tutorials/save-and-reopen-project.md) explains save,
reopen, portability, and common schema errors.

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
- [Portfolio domain model](docs/models/portfolio-domain.md)
- [CSV portfolio format](docs/models/csv-portfolio-format.md)
- [XLSX portfolio format](docs/models/xlsx-portfolio-format.md)
- [Local market-data format and contracts](docs/models/market-data.md)
- [Versioned desktop-project format](docs/models/project-file.md)
- [Basic analytics formulas and conventions](docs/concepts/basic-analytics.md)
- [Historical VaR formulas and conventions](docs/concepts/historical-var.md)
- [Historical Expected Shortfall formulas](docs/concepts/historical-expected-shortfall.md)
- [First desktop workflow tutorial](docs/tutorials/first-desktop-workflow.md)
- [Save and reopen a project](docs/tutorials/save-and-reopen-project.md)
- [ADR-004: historical VaR conventions](docs/decisions/ADR-004-historical-var-conventions.md)
- [ADR-005: historical Expected Shortfall conventions](docs/decisions/ADR-005-historical-expected-shortfall-conventions.md)
- [ADR-006: initial desktop composition](docs/decisions/ADR-006-initial-desktop-composition.md)
- [ADR-007: versioned project JSON](docs/decisions/ADR-007-versioned-project-json.md)
- [Contribution guide](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## Roadmap

The next planned phase is **Phase 11 — parametric normal VaR**, introducing a second
risk model with an explicit normal-distribution assumption, portfolio covariance,
documented quantile convention, and numerical regression tests.

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
