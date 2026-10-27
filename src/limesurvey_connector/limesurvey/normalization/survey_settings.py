"""Normalize survey navigation settings and group-level content and conditions."""

from typing import Any

from .condition_parser import parse_limesurvey_condition
from .condition_references import UnsupportedConditionError
from .source_values import _clean_html, _compact, _issue, _number, _optional_number, _text, _yes
from .visibility_normalizer import log_unsupported_condition


def normalize_groups(
    groups: list[dict[str, Any]],
    condition_references: dict[str, tuple[str, str | None]],
    issues: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Normalize in source order, then assign consecutive portable group positions."""
    normalized = [normalize_group(group, condition_references, issues) for group in groups]
    ordered = sorted(normalized, key=lambda group: group["order"])
    for index, group in enumerate(ordered):
        group["order"] = index
    return ordered


def normalize_group(
    group: dict[str, Any],
    condition_references: dict[str, tuple[str, str | None]],
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    result = {
        "id": _text(group.get("gid")),
        "order": _number(group.get("group_order"), 0),
    }
    title = _clean_html(group.get("group_name"))
    description = _clean_html(group.get("description"))
    if title:
        result["title"] = title
    if description:
        result["description"] = description
    relevance = _text(group.get("grelevance")).strip()
    group_id = _text(group.get("gid")).strip()
    if group_id or relevance:
        result["source"] = _compact(
            {
                "platform": "limesurvey",
                "groupId": group_id or None,
                "originDetails": (
                    [
                        {
                            "type": "limesurvey-group",
                            "version": "1.0.0",
                            "groupRelevanceExpression": relevance,
                        }
                    ]
                    if relevance
                    else None
                ),
            }
        )
    for rule in ("random_group", "randomization_group"):
        if not _text(group.get(rule)).strip():
            continue
        result["randomizationGroup"] = _text(group[rule]).strip()
    if relevance and relevance != "1":
        try:
            condition = parse_limesurvey_condition(relevance, condition_references)
            result["visibility"] = {
                "condition": condition
                if condition is not None
                else {"type": "constant", "value": True}
            }
        except UnsupportedConditionError as error:
            log_unsupported_condition(relevance, scope="group", owner=group_id)
            issues.append(
                _issue(
                    "warning",
                    error.issue_code,
                    str(error),
                    details={"sourceExpression": relevance, "scope": "group"},
                )
            )
    return result


def normalize_settings(survey: dict[str, Any], language: dict[str, Any]) -> dict[str, Any]:
    layout = {"A": "all", "G": "group", "S": "question"}.get(_text(survey.get("format")).upper())
    show_group = _text(survey.get("showgroupinfo")).upper()
    return _compact(
        {
            "layout": layout,
            "showWelcome": _yes(survey.get("showwelcome"))
            if survey.get("showwelcome") is not None
            else None,
            "showProgress": _yes(survey.get("showprogress"))
            if survey.get("showprogress") is not None
            else None,
            "allowPrevious": _yes(survey.get("allowprev"))
            if survey.get("allowprev") is not None
            else None,
            "showGroupName": show_group in {"B", "N"} if show_group else None,
            "showGroupDescription": show_group in {"B", "D"} if show_group else None,
            "questionIndex": {
                -1: "inherit",
                0: "disabled",
                1: "incremental",
                2: "full",
            }.get(int(_optional_number(survey.get("questionindex")) or 0)),
            # LimeSurvey can export -1 as an inherited/default sentinel. The
            # portable setting stores the effective non-negative delay instead.
            "navigationDelay": max(0, _optional_number(survey.get("navigationdelay")) or 0),
            "welcomeText": _clean_html(language.get("surveyls_welcometext")) or None,
            "endText": _clean_html(language.get("surveyls_endtext")) or None,
            "policyNotice": _clean_html(language.get("surveyls_policy_notice")) or None,
        }
    )
