"""Select localized source rows without discarding same-language duplicates."""

from __future__ import annotations

from typing import Any


class SurveyLanguageError(ValueError):
    """The requested language or a required translation is unavailable."""


def select_language_rows(
    rows: list[dict[str, Any]], language: str | None, id_key: str
) -> list[dict[str, Any]]:
    if not language:
        return rows
    selected = [row for row in rows if not row.get("language") or row["language"] == language]
    selected_ids = {str(row.get(id_key)) for row in selected}
    missing = {str(row.get(id_key)) for row in rows} - selected_ids
    if missing:
        raise SurveyLanguageError(
            f"Missing {language} translation for {id_key}: {', '.join(sorted(missing))}."
        )
    return selected
