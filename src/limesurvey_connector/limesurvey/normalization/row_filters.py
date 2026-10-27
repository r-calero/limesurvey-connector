"""Portable matrix filters; never guess undeclared question or answer codes."""

from __future__ import annotations

from typing import Any

from .source_values import _record, _text


def apply_matrix_filters(
    field: dict[str, Any], attributes: dict[str, Any], references: Any
) -> set[str]:
    if field["type"] not in {"matrix", "multiple-choice", "multiple-choice-with-comments"}:
        return set()
    converted: set[str] = set()
    antecedents: dict[str, list[str]] = {"array_filter": [], "array_filter_exclude": []}

    def collect(current: dict[str, Any], stack: set[str]) -> None:
        for rule in antecedents:
            for source_code in [
                code.strip() for code in _text(current.get(rule)).split(";") if code.strip()
            ]:
                if source_code in stack:
                    raise ValueError("Cyclic array filter")
                if source_code in antecedents[rule]:
                    continue
                antecedents[rule].append(source_code)
                source = getattr(references, "questions", {}).get(source_code)
                if source:
                    source_attributes = _record(
                        _record(source.get("result")).get("attributes") or source.get("attributes")
                    )
                    collect(source_attributes, stack | {source_code})

    try:
        collect(attributes, {field["code"]})
    except ValueError:
        return set()
    all_sources = [
        getattr(references, "questions", {}).get(code)
        for codes in antecedents.values()
        for code in codes
    ]
    if any(
        not source or source.get("type") not in {"M", "P", "Q", "K", "A", "B", "C", "E", "F", "H"}
        for source in all_sources
    ):
        return set()
    for attribute in ("array_filter", "array_filter_exclude"):
        codes = antecedents[attribute]
        if not codes:
            continue
        sources: list[Any] = [getattr(references, "questions", {}).get(code) for code in codes]
        for row in field["matrix"]["rows"] if field["type"] == "matrix" else field["options"]:
            predicates = []
            for code, source in zip(codes, sources, strict=False):
                if row["code"] not in references.response_items.get(code, []):
                    continue
                reference = {"fieldCode": code, "responseItemCode": row["code"]}
                predicates.append(
                    {
                        "type": "comparison",
                        "responseReference": reference,
                        "operator": "equals",
                        "value": "Y",
                    }
                    if source["type"] in {"M", "P"}
                    else {"type": "answered", "responseReference": reference}
                )
            if not predicates:
                continue
            if attribute == "array_filter_exclude":
                predicates = [{"type": "not", "condition": predicate} for predicate in predicates]
            condition = (
                predicates[0] if len(predicates) == 1 else {"type": "all", "conditions": predicates}
            )
            previous = row.get("visibility", {}).get("condition")
            row["visibility"] = {
                "condition": {"type": "all", "conditions": [previous, condition]}
                if previous
                else condition
            }
        if _text(attributes.get(attribute)).strip():
            converted.add(attribute)
    return converted


def apply_exclusive_options(field: dict[str, Any], attributes: dict[str, Any]) -> set[str]:
    if field["type"] not in {"multiple-choice", "multiple-choice-with-comments"}:
        return set()
    converted: set[str] = set()
    declared = {option["code"] for option in field["options"]}
    for rule in ("exclude_all_others", "exclusive_option"):
        codes = set(code.strip() for code in _text(attributes.get(rule)).split(";") if code.strip())
        if not codes or not codes.issubset(declared):
            continue
        for option in field["options"]:
            if option["code"] in codes:
                option["exclusive"] = True
        converted.add(rule)
    return converted
