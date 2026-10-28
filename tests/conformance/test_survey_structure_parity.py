import pytest

from survey_structure import (
    FIELD_WIDGET_COMPATIBILITY,
    SURVEY_STRUCTURE_VERSION,
    calculate_survey_score,
    get_survey_execution_issues,
    grade_survey_answer,
    is_month_day,
    is_numeric_text,
    month_day_count,
    number_character_length,
    parse_survey_structure,
    resolve_survey_diagnostic_locale,
    safe_parse_survey_load_result,
    safe_parse_survey_structure,
)
from survey_structure.language import is_valid_language_tag
from tests.support.conformance import CONFORMANCE, GOLDENS, read_json, validation_cases

pytestmark = pytest.mark.conformance

GOLDEN = GOLDENS / "survey-structure"
CASES = validation_cases()
PARSERS = {
    "SurveyStructure": safe_parse_survey_structure,
    "SurveyLoadResult": safe_parse_survey_load_result,
}
PATTERN_CASES = read_json(GOLDEN / "pattern-cases.json")
DIVERGENCES = read_json(CONFORMANCE / "known-divergences.json")
DIVERGENT_PATTERNS = {
    (case["pattern"], flags)
    for case in DIVERGENCES["cases"]
    if case["divergent"]
    for flags in ("", "i", "m", "s")
} | {(case["pattern"], case["flags"]) for case in DIVERGENCES["flagged"]}
EDGE = read_json(CONFORMANCE / "fixtures" / "contract-cases.json")
EMPTY_SURVEY = {"surveyStructureVersion": SURVEY_STRUCTURE_VERSION, "id": "language", "fields": []}


def _pattern_survey(pattern, value, flags=""):
    validation = {"responseFormatPattern": pattern}
    if flags:
        validation["patternFlags"] = flags
    field = {
        "id": "q1",
        "code": "Q01",
        "type": "short-text",
        "label": "Pattern",
        "responseValidation": validation,
        "defaultValue": value,
    }
    return {**EMPTY_SURVEY, "fields": [field]}


def _compact(issue):
    compact = {"path": issue["path"], "code": issue["code"]}
    reason = issue.get("params", {}).get("reason")
    if reason:
        compact["reason"] = reason
    return compact


@pytest.mark.parametrize("case", CASES, ids=[case["name"] for case in CASES])
def test_validation_matches_reference(case):
    result = PARSERS[case["contract"]](case["value"])
    assert result.success is case["success"]
    assert result.issues == case["issues"]
    if result.success and "executionIssues" in case:
        assert get_survey_execution_issues(result.data) == case["executionIssues"]


@pytest.mark.parametrize(
    "case", read_json(GOLDEN / "language-tags.json"), ids=lambda case: repr(case["tag"])
)
def test_language_tags_match_reference(case):
    assert is_valid_language_tag(case["tag"]) is case["valid"]


def test_patterns_match_reference_or_are_rejected_conservatively():
    mismatches = []
    for case in PATTERN_CASES:
        survey = _pattern_survey(case["pattern"], case["value"], case["flags"])
        issues = [_compact(issue) for issue in safe_parse_survey_structure(survey).issues]
        if (case["pattern"], case["flags"]) in DIVERGENT_PATTERNS:
            expected = {
                "path": ["fields", 0, "responseValidation", "responseFormatPattern"],
                "code": "custom",
                "reason": "invalid-validation-pattern",
            }
            if expected not in issues:
                mismatches.append(case)
        elif issues != case["issues"]:
            mismatches.append(case)
    assert mismatches == []


def test_every_listed_divergence_is_valid_ecmascript_and_rejected():
    for case in [*DIVERGENCES["cases"], *DIVERGENCES["flagged"]]:
        survey = _pattern_survey(case["pattern"], "a", case.get("flags", ""))
        reasons = [
            issue.get("params", {}).get("reason")
            for issue in safe_parse_survey_structure(survey).issues
        ]
        assert "invalid-validation-pattern" in reasons, case["pattern"]


@pytest.mark.parametrize(
    "case", read_json(GOLDEN / "url-cases.json"), ids=lambda case: repr(case["url"])
)
def test_image_urls_match_reference(case):
    field = {
        "id": "q1",
        "code": "Q01",
        "type": "display",
        "label": "Image",
        "images": [{"url": case["url"], "alt": ""}],
    }
    result = safe_parse_survey_structure({**EMPTY_SURVEY, "fields": [field]})
    assert [_compact(issue) for issue in result.issues] == case["issues"]


@pytest.mark.parametrize(
    "case", read_json(GOLDEN / "date-bound-cases.json"), ids=lambda case: case["bound"]
)
def test_date_bounds_match_reference(case):
    field = {
        "id": "q1",
        "code": "Q01",
        "type": "date",
        "dateValueType": "date",
        "label": "Date",
        "responseValidation": {"dateMin": case["bound"]},
    }
    result = safe_parse_survey_structure({**EMPTY_SURVEY, "fields": [field]})
    assert [_compact(issue) for issue in result.issues] == case["issues"]


def test_helpers_match_reference():
    helpers = read_json(GOLDEN / "helpers.json")
    assert [is_numeric_text(case["value"]) for case in helpers["isNumericText"]] == [
        case["result"] for case in helpers["isNumericText"]
    ]
    assert [
        number_character_length(case["value"]) for case in helpers["numberCharacterLength"]
    ] == [case["result"] for case in helpers["numberCharacterLength"]]
    assert [is_month_day(case.get("value")) for case in helpers["isMonthDay"]] == [
        case["result"] for case in helpers["isMonthDay"]
    ]
    assert [month_day_count(case["month"]) for case in helpers["monthDayCount"]] == [
        case["result"] for case in helpers["monthDayCount"]
    ]


def test_grading_matches_reference():
    # Inputs come from the fixture: JSON.stringify writes -0 as 0 in the golden.
    golden = read_json(GOLDEN / "grading.json")
    fixture = EDGE["grading"]
    survey = parse_survey_structure(fixture["survey"])
    scores = iter(golden["score"])
    for answers in fixture["answers"]:
        for field_codes in fixture["fieldCodes"]:
            assert calculate_survey_score(survey, answers, field_codes) == next(scores)["result"]
    for case, expected in zip(fixture["gradeAnswer"], golden["gradeAnswer"], strict=True):
        result = grade_survey_answer(
            case["grading"], case["value"], case.get("multiple", False), case.get("selected", True)
        )
        assert result == expected["result"]


def test_translated_examples_are_valid_ecmascript_and_accepted():
    for case in DIVERGENCES["translated"]:
        assert case["ecmascript"], case["pattern"]
        result = safe_parse_survey_structure(_pattern_survey(case["pattern"], "a"))
        reasons = [issue.get("params", {}).get("reason") for issue in result.issues]
        assert "invalid-validation-pattern" not in reasons, case["pattern"]


def test_widget_compatibility_matches_reference():
    assert read_json(GOLDEN / "widget-compatibility.json") == FIELD_WIDGET_COMPATIBILITY


@pytest.mark.parametrize("case", read_json(GOLDEN / "diagnostic-locales.json"))
def test_diagnostic_locale_matches_reference(case):
    assert resolve_survey_diagnostic_locale(case["locale"]) == case["resolved"]


def test_reference_load_results_are_accepted():
    for path in (GOLDENS / "limesurvey").rglob("*.json"):
        golden = read_json(path)
        if golden["ok"]:
            assert safe_parse_survey_load_result(golden["result"]).success, path.name


@pytest.mark.parametrize("case", CASES, ids=[case["name"] for case in CASES])
def test_localized_messages_match_reference(case):
    from survey_structure import localize_survey_validation_issue

    for locale in ("en", "es"):
        assert [
            localize_survey_validation_issue(issue, locale) for issue in case["issues"]
        ] == case["messages"][locale]
