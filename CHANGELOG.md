# Changelog

All notable changes to the Zeus Risk Engine will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project intends to follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial product vision, scope, use cases, glossary, architecture, roadmap, and ADRs.
- Installable `zeus_risk` package with version `0.1.0`.
- Minimal `zeus-risk` and `python -m zeus_risk` command-line entry points.
- Pytest, coverage, Ruff, mypy, packaging, and GitHub Actions configuration.
- Project README, MIT license, contribution guide, and repository hygiene files.
- Immutable currency, instrument, position, and portfolio domain models.
- Structured validation issues and domain failures with stable error codes.
- Decimal market valuation, long/short support, multi-currency safeguards, and explicit
  net/gross position weights.
- Mathematical portfolio-domain documentation and ADR-003 for numeric conventions.
- Validated UTF-8 CSV portfolio importer using only the Python standard library.
- Controlled delimiter detection, Portuguese/English aliases, row status, provenance,
  partial portfolio results, and structured import exceptions.
- Synthetic CSV sample, versioned fixtures, format documentation, and importer tests.
- Resource-bounded XLSX importer with worksheet listing and explicit selection.
- Shared tabular validation for CSV/XLSX, formula and cell-type rejection, archive
  safeguards, source provenance, and partial results.
- XLSX format documentation and synthetic workbook tests generated at test time.
- Immutable daily price observations, series, keys, source metadata, load results, and
  structured market-data failures.
- Offline long-format CSV market-data provider with Portuguese/English aliases,
  resource limits, content hashing, and explicit missing-price policy.
- Deterministic intersection and union alignment without implicit filling.
- Schema-versioned JSON market-data cache with atomic writes and full domain
  revalidation on load.
- Synthetic local price sample, format documentation, and unit/integration coverage for
  provider, alignment, cache, and domain invariants.
- Immutable return, descriptive-statistics, statistic-matrix, drawdown, and
  concentration result contracts with structured analytics failures.
- Simple/log asset returns and constant signed net-weight portfolio returns, including
  mathematically correct aggregation of log-return inputs.
- Sample/population variance, volatility with explicit annualization, covariance, and
  correlation with zero-variance safeguards.
- Cumulative wealth, drawdown episodes, maximum drawdown, gross-weight HHI, and
  effective position count.
- Mathematical analytics documentation plus unit, integration, and numerical
  regression tests over synthetic data.
- Immutable historical VaR configuration, loss-scenario, and result contracts.
- Nearest-rank historical VaR with positive-loss convention, exact tail-resolution
  validation, rolling simple/log horizons, and deterministic recent-window selection.
- Structured risk-calculation failures and reconciliation of sample, rank, quantile,
  non-negative VaR, unit, convention, and dates.
- ADR-004, mathematical documentation, manual example, and unit, integration, and
  numerical regression coverage for historical VaR.
- Immutable historical Expected Shortfall results composed with the exact VaR result
  and effective sample used.
- Rank-defined empirical tails, deterministic chronological tie-breaking, raw tail
  means, non-negative ES, and explicit `ES >= VaR` reconciliation.
- ADR-005, mathematical documentation, manual example, and unit, integration, and
  numerical regression coverage for historical Expected Shortfall.
- PySide6 6.11 desktop bootstrap, `zeus-risk-gui`, module entry point, main window,
  restrained application styling, and guided tabbed workflow.
- PySide-free `PortfolioRiskWorkflow` composing validated portfolio import, local
  prices, aligned returns, historical VaR, and Expected Shortfall.
- Read-only Qt table models for positions and validation issues, including source
  lines, stable codes, tooltips, textual severity, and accessible colors.
- Portfolio and risk pages with CSV/XLSX worksheet selection, input summaries,
  explicit parameters, readiness gates, structured failures, and auditable results.
- Reproducible matching portfolio/price samples, desktop tutorial, ADR-006, and
  offscreen GUI tests covering bootstrap, models, success, and failure paths.
- Immutable `DesktopProject`, `ProjectWorkflow`, structured `ProjectFileError`, and a
  strict JSON schema `1.0` adapter for local project persistence.
- Atomic UTF-8 project writes, one-megabyte input limit, exact-field validation,
  duplicate-key detection, decimal-string confidence, and domain revalidation.
- Relative references within the project directory, absolute external references,
  explicit missing-source failures, and a portable synthetic `*.zeus.json` example.
- Desktop open, save, save-as, `Ctrl+S`, unsaved-change marker, atomic restoration, and
  non-modal project-error presentation.
- ADR-007, project-format documentation, save/reopen tutorial, unit coverage,
  round-trip integration, and GUI restoration tests.

### Notes

- Version `0.1.0` identifies the current pre-alpha codebase; no release tag has been
  published yet.
- The first graphical workflow is synchronous by design and limited to small local
  files; background workers and cancellation remain deferred to Phase 14.
- Project schema `1.0` stores references and configuration only; it does not embed
  financial data, results, migrations, autosave, or execution history.
- Historical VaR is relative only; monetary conversion and additional empirical
  quantile methods remain deferred.
- Historical Expected Shortfall is relative and equally weighted; fractional boundary
  weights and alternative tail definitions remain deferred.
