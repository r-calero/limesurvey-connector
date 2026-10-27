"""Publication checks for an already validated survey (port of ``getSurveyExecutionIssues``)."""

from __future__ import annotations

from typing import Any


def get_survey_execution_issues(survey: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not survey["fields"]:
        issues.append({"message": "Add at least one field before publishing."})

    def visit(fields: list[dict[str, Any]]) -> None:
        for field in fields:
            field_type = field["type"]
            empty = (
                ("options" in field and not field["options"] and not field.get("other"))
                or (field_type == "multiple-input" and not field["subquestions"])
                or (
                    field_type == "matrix"
                    and (not field["matrix"]["rows"] or not field["matrix"]["columns"])
                )
                or (field_type == "custom" and not field["childrenFields"])
            )
            code = field["code"]
            if empty:
                issues.append(
                    {
                        "fieldCode": code,
                        "message": f'Field "{code}" needs its options, rows or child fields before publishing.',
                    }
                )
            minimum = field.get("responseValidation", {}).get("minSelections")
            if "options" in field and minimum is not None:
                available = len(field["options"]) + (1 if field.get("other") else 0)
                if minimum > available:
                    issues.append(
                        {
                            "fieldCode": code,
                            "message": f'Field "{code}" requires {minimum} selections but only '
                            f"{available} are available.",
                        }
                    )
            if field_type == "custom":
                visit(field["childrenFields"])

    visit(survey["fields"])
    return issues
