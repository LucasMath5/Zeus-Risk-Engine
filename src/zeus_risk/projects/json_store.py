"""Strict, versioned JSON adapter for local desktop projects."""

from __future__ import annotations

import json
import os
import tempfile
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Never, cast

from zeus_risk import __version__
from zeus_risk.domain import (
    PROJECT_SCHEMA_VERSION,
    DesktopProject,
    DomainValidationError,
    EmpiricalQuantileMethod,
    HistoricalVaRConfiguration,
    ReturnMethod,
    ValidationIssue,
    ValidationSeverity,
)
from zeus_risk.exceptions import ProjectFileError

_MAX_PROJECT_BYTES = 1_000_000
_ROOT_FIELDS = {
    "schema_version",
    "software_version",
    "name",
    "portfolio",
    "market_data",
    "risk",
}
_PORTFOLIO_FIELDS = {"path", "worksheet_name"}
_MARKET_DATA_FIELDS = {"path"}
_RISK_FIELDS = {
    "model",
    "return_method",
    "confidence_level",
    "horizon_days",
    "window",
    "quantile_method",
}


class _DuplicateProjectFieldError(ValueError):
    pass


class JsonProjectStore:
    """Persist and restore one exact desktop-project JSON schema."""

    def save(self, project: DesktopProject, path: str | Path) -> Path:
        """Atomically save a validated project and return its resolved destination."""

        if not isinstance(project, DesktopProject):
            raise TypeError("project must be a DesktopProject")
        destination = Path(path).resolve()
        source_name = str(destination)
        if not destination.parent.is_dir():
            _raise_project_error(
                "PROJECT_DIRECTORY_NOT_FOUND",
                "Project destination directory was not found.",
                field="path",
                item=str(destination.parent),
                source_name=source_name,
            )
        _require_reference_file(
            project.portfolio_path,
            code="PROJECT_PORTFOLIO_FILE_NOT_FOUND",
            field="portfolio.path",
            source_name=source_name,
        )
        _require_reference_file(
            project.market_data_path,
            code="PROJECT_MARKET_DATA_FILE_NOT_FOUND",
            field="market_data.path",
            source_name=source_name,
        )

        payload = _serialize_project(project, destination.parent)
        content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="\n",
                prefix=f".{destination.name}.",
                suffix=".tmp",
                dir=destination.parent,
                delete=False,
            ) as temporary:
                temporary.write(content)
                temporary.flush()
                os.fsync(temporary.fileno())
                temporary_path = Path(temporary.name)
            os.replace(temporary_path, destination)
        except OSError as error:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass
            raise _project_error(
                "PROJECT_WRITE_ERROR",
                "Project JSON file could not be written.",
                field="path",
                item=source_name,
                source_name=source_name,
            ) from error
        return destination

    def load(self, path: str | Path) -> DesktopProject:
        """Read, strictly validate, and resolve one project JSON file."""

        source = Path(path).resolve()
        source_name = str(source)
        try:
            if source.stat().st_size > _MAX_PROJECT_BYTES:
                _raise_project_error(
                    "PROJECT_FILE_TOO_LARGE",
                    "Project JSON exceeds the one-megabyte safety limit.",
                    field="path",
                    item=source_name,
                    source_name=source_name,
                )
            content = source.read_text(encoding="utf-8")
        except FileNotFoundError as error:
            raise _project_error(
                "PROJECT_FILE_NOT_FOUND",
                "Project JSON file was not found.",
                field="path",
                item=source_name,
                source_name=source_name,
            ) from error
        except UnicodeDecodeError as error:
            raise _project_error(
                "INVALID_PROJECT_ENCODING",
                "Project JSON must use UTF-8 encoding.",
                field="path",
                item=source_name,
                source_name=source_name,
            ) from error
        except OSError as error:
            raise _project_error(
                "PROJECT_READ_ERROR",
                "Project JSON file could not be read.",
                field="path",
                item=source_name,
                source_name=source_name,
            ) from error

        try:
            raw: object = json.loads(content, object_pairs_hook=_unique_object)
        except _DuplicateProjectFieldError as error:
            raise _project_error(
                "DUPLICATE_PROJECT_FIELD",
                "Project JSON contains a duplicate object field.",
                field="json",
                item=str(error),
                source_name=source_name,
            ) from error
        except json.JSONDecodeError as error:
            raise _project_error(
                "INVALID_PROJECT_JSON",
                "Project file does not contain valid JSON.",
                field="json",
                item=f"line={error.lineno},column={error.colno}",
                source_name=source_name,
            ) from error

        root = _require_object(raw, field="project", source_name=source_name)
        _require_exact_fields(root, _ROOT_FIELDS, field="project", source_name=source_name)
        schema_version = _require_string(
            root["schema_version"],
            field="schema_version",
            source_name=source_name,
        )
        if schema_version != PROJECT_SCHEMA_VERSION:
            _raise_project_error(
                "UNSUPPORTED_PROJECT_SCHEMA_VERSION",
                "Project schema version is not supported by this application.",
                field="schema_version",
                item=f"expected={PROJECT_SCHEMA_VERSION},actual={schema_version}",
                source_name=source_name,
            )
        _require_string(
            root["software_version"],
            field="software_version",
            source_name=source_name,
        )

        project = _deserialize_project(root, source.parent, source_name)
        _require_reference_file(
            project.portfolio_path,
            code="PROJECT_PORTFOLIO_FILE_NOT_FOUND",
            field="portfolio.path",
            source_name=source_name,
        )
        _require_reference_file(
            project.market_data_path,
            code="PROJECT_MARKET_DATA_FILE_NOT_FOUND",
            field="market_data.path",
            source_name=source_name,
        )
        return project


def _serialize_project(project: DesktopProject, base_directory: Path) -> dict[str, object]:
    configuration = project.risk_configuration
    return {
        "schema_version": PROJECT_SCHEMA_VERSION,
        "software_version": __version__,
        "name": project.name,
        "portfolio": {
            "path": _serialize_reference(project.portfolio_path, base_directory),
            "worksheet_name": project.worksheet_name,
        },
        "market_data": {
            "path": _serialize_reference(project.market_data_path, base_directory),
        },
        "risk": {
            "model": "historical",
            "return_method": project.return_method.value,
            "confidence_level": str(configuration.confidence_level),
            "horizon_days": configuration.horizon_days,
            "window": configuration.window,
            "quantile_method": configuration.quantile_method.value,
        },
    }


def _deserialize_project(
    root: dict[str, object],
    base_directory: Path,
    source_name: str,
) -> DesktopProject:
    portfolio = _require_object(root["portfolio"], field="portfolio", source_name=source_name)
    market_data = _require_object(root["market_data"], field="market_data", source_name=source_name)
    risk = _require_object(root["risk"], field="risk", source_name=source_name)
    _require_exact_fields(
        portfolio,
        _PORTFOLIO_FIELDS,
        field="portfolio",
        source_name=source_name,
    )
    _require_exact_fields(
        market_data,
        _MARKET_DATA_FIELDS,
        field="market_data",
        source_name=source_name,
    )
    _require_exact_fields(risk, _RISK_FIELDS, field="risk", source_name=source_name)

    model = _require_string(risk["model"], field="risk.model", source_name=source_name)
    if model != "historical":
        _raise_project_error(
            "UNSUPPORTED_PROJECT_RISK_MODEL",
            "Project risk model is not supported in this phase.",
            field="risk.model",
            item=model,
            source_name=source_name,
        )
    return_method = _parse_return_method(risk["return_method"], source_name)
    quantile_method = _parse_quantile_method(risk["quantile_method"], source_name)
    confidence = _parse_confidence(risk["confidence_level"], source_name)
    horizon_days = _require_integer(
        risk["horizon_days"], field="risk.horizon_days", source_name=source_name
    )
    window = _require_integer(risk["window"], field="risk.window", source_name=source_name)
    worksheet_name = _require_optional_string(
        portfolio["worksheet_name"],
        field="portfolio.worksheet_name",
        source_name=source_name,
    )
    try:
        configuration = HistoricalVaRConfiguration(
            confidence_level=confidence,
            horizon_days=horizon_days,
            window=window,
            quantile_method=quantile_method,
        )
        return DesktopProject(
            name=_require_string(root["name"], field="name", source_name=source_name),
            portfolio_path=_resolve_reference(
                _require_string(portfolio["path"], field="portfolio.path", source_name=source_name),
                base_directory,
            ),
            market_data_path=_resolve_reference(
                _require_string(
                    market_data["path"], field="market_data.path", source_name=source_name
                ),
                base_directory,
            ),
            risk_configuration=configuration,
            worksheet_name=worksheet_name,
            return_method=return_method,
        )
    except DomainValidationError as error:
        raise ProjectFileError(*error.issues, source_name=source_name) from error


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateProjectFieldError(key)
        result[key] = value
    return result


def _require_object(value: object, *, field: str, source_name: str) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        _raise_project_error(
            "INVALID_PROJECT_OBJECT",
            "Project field must be a JSON object.",
            field=field,
            source_name=source_name,
        )
    return cast(dict[str, object], value)


def _require_exact_fields(
    value: dict[str, object],
    expected: set[str],
    *,
    field: str,
    source_name: str,
) -> None:
    missing = sorted(expected - value.keys())
    if missing:
        _raise_project_error(
            "MISSING_PROJECT_FIELD",
            "Project JSON is missing required fields.",
            field=field,
            item=", ".join(missing),
            source_name=source_name,
        )
    unknown = sorted(value.keys() - expected)
    if unknown:
        _raise_project_error(
            "UNKNOWN_PROJECT_FIELD",
            "Project JSON contains unsupported fields.",
            field=field,
            item=", ".join(unknown),
            source_name=source_name,
        )


def _require_string(value: object, *, field: str, source_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _raise_project_error(
            "INVALID_PROJECT_STRING",
            "Project field must be a non-empty string.",
            field=field,
            source_name=source_name,
        )
    return value.strip()


def _require_optional_string(
    value: object,
    *,
    field: str,
    source_name: str,
) -> str | None:
    if value is None:
        return None
    return _require_string(value, field=field, source_name=source_name)


def _require_integer(value: object, *, field: str, source_name: str) -> int:
    if type(value) is not int:
        _raise_project_error(
            "INVALID_PROJECT_INTEGER",
            "Project field must be an integer.",
            field=field,
            item=str(value),
            source_name=source_name,
        )
    return value


def _parse_confidence(value: object, source_name: str) -> Decimal:
    text = _require_string(
        value,
        field="risk.confidence_level",
        source_name=source_name,
    )
    try:
        return Decimal(text)
    except InvalidOperation as error:
        raise _project_error(
            "INVALID_PROJECT_CONFIDENCE",
            "Project confidence level must be a decimal string.",
            field="risk.confidence_level",
            item=text,
            source_name=source_name,
        ) from error


def _parse_return_method(value: object, source_name: str) -> ReturnMethod:
    text = _require_string(value, field="risk.return_method", source_name=source_name)
    try:
        return ReturnMethod(text)
    except ValueError as error:
        raise _project_error(
            "UNSUPPORTED_PROJECT_RETURN_METHOD",
            "Project return method is not supported.",
            field="risk.return_method",
            item=text,
            source_name=source_name,
        ) from error


def _parse_quantile_method(value: object, source_name: str) -> EmpiricalQuantileMethod:
    text = _require_string(value, field="risk.quantile_method", source_name=source_name)
    try:
        return EmpiricalQuantileMethod(text)
    except ValueError as error:
        raise _project_error(
            "UNSUPPORTED_PROJECT_QUANTILE_METHOD",
            "Project quantile method is not supported.",
            field="risk.quantile_method",
            item=text,
            source_name=source_name,
        ) from error


def _resolve_reference(value: str, base_directory: Path) -> Path:
    reference = Path(value)
    if reference.is_absolute():
        return reference.resolve()
    return (base_directory / reference).resolve()


def _serialize_reference(reference: Path, base_directory: Path) -> str:
    resolved = reference.resolve()
    try:
        relative = resolved.relative_to(base_directory.resolve())
    except ValueError:
        return str(resolved)
    return relative.as_posix()


def _require_reference_file(
    path: Path,
    *,
    code: str,
    field: str,
    source_name: str,
) -> None:
    try:
        is_file = path.is_file()
    except OSError:
        is_file = False
    if not is_file:
        _raise_project_error(
            code,
            "Referenced project file was not found.",
            field=field,
            item=str(path),
            source_name=source_name,
        )


def _project_error(
    code: str,
    message: str,
    *,
    field: str | None = None,
    item: str | None = None,
    source_name: str | None = None,
) -> ProjectFileError:
    return ProjectFileError(
        ValidationIssue(
            severity=ValidationSeverity.ERROR,
            code=code,
            message=message,
            field=field,
            item=item,
        ),
        source_name=source_name,
    )


def _raise_project_error(
    code: str,
    message: str,
    *,
    field: str | None = None,
    item: str | None = None,
    source_name: str | None = None,
) -> Never:
    raise _project_error(
        code,
        message,
        field=field,
        item=item,
        source_name=source_name,
    )
