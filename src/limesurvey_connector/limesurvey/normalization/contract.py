"""Contract validation of normalized LimeSurvey output with the Python survey_structure port.

Replaces the Node subprocess used by limesurvey-rc2-api; errors keep the shape that
adapter's validator reported (path, code, message, params).
"""

from __future__ import annotations

from typing import Any

from survey_structure import (
    ParseResult,
    safe_parse_survey_load_result,
    safe_parse_survey_structure,
)


class SurveyStructureContractError(RuntimeError):
    """The normalizer produced a value that violates the shared SurveyStructure contract."""

    def __init__(self, message: str, errors: list[dict[str, Any]] | None = None) -> None:
        super().__init__(message)
        self.errors = errors or []


def validate_survey_structure(value: dict[str, Any]) -> dict[str, Any]:
    return _check("SurveyStructure", value, safe_parse_survey_structure(value))


def validate_survey_load_result(value: dict[str, Any]) -> dict[str, Any]:
    return _check("SurveyLoadResult", value, safe_parse_survey_load_result(value))


def _check(contract_name: str, value: dict[str, Any], result: ParseResult) -> dict[str, Any]:
    if result.success:
        return value
    errors = [
        {
            "path": issue["path"],
            "code": issue["code"],
            "message": _describe(issue),
            "params": issue.get("params"),
        }
        for issue in result.issues
    ]
    first = errors[0]
    location = ".".join(str(part) for part in first["path"]) or "<root>"
    raise SurveyStructureContractError(
        f"{contract_name} output violates the shared contract at {location}: {first['message']}",
        errors,
    )


def _describe(issue: dict[str, Any]) -> str:
    if issue["code"] != "invalid_union":
        return str(issue["message"])
    # Prefer the branch closest to the supplied variant, as the reference validator does.
    branch = min(issue["unionErrors"], key=len)
    return "; ".join(_describe(child) for child in branch)
