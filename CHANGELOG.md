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

### Notes

- Version `0.1.0` identifies the current pre-alpha codebase; no release tag has been
  published yet.
- VaR, Expected Shortfall, and graphical-interface behavior are not implemented yet.
