"""Explicit question codes must survive optional concatenated response aliases."""

import pytest

from limesurvey_connector.limesurvey.normalization import build_survey_structure
from limesurvey_connector.limesurvey.normalization.condition_references import (
    UnsupportedConditionError,
    build_condition_references,
    resolve_reference,
)


@pytest.mark.parametrize("reverse", [False, True])
def test_explicit_question_code_wins_over_concatenated_child_alias(reverse):
    questions = [
        {"qid": "20622", "gid": "364", "title": "q0r862", "type": "Y"},
        {"qid": "21023", "gid": "364", "title": "q0r86", "type": "P"},
        {"qid": "30000", "parent_qid": "21023", "title": "2"},
    ]
    references = build_condition_references(questions[::-1] if reverse else questions, "921577")

    assert resolve_reference("q0r862.NAOK", references) == ("q0r862", None)
    assert resolve_reference("q0r86_2.NAOK", references) == ("q0r86", "2")
    assert resolve_reference("921577X364X210232.NAOK", references) == ("q0r86", "2")


@pytest.mark.parametrize("reverse", [False, True])
def test_collisions_between_derived_aliases_remain_ambiguous(reverse):
    questions = [
        {"qid": "10", "title": "Q", "type": "M"},
        {"qid": "11", "parent_qid": "10", "title": "12"},
        {"qid": "20", "title": "Q1", "type": "M"},
        {"qid": "21", "parent_qid": "20", "title": "2"},
    ]
    references = build_condition_references(questions[::-1] if reverse else questions, "100")

    with pytest.raises(UnsupportedConditionError, match="more than one"):
        resolve_reference("Q12.NAOK", references)
    assert resolve_reference("Q_12.NAOK", references) == ("Q", "12")
    assert resolve_reference("Q1_2.NAOK", references) == ("Q1", "2")


@pytest.mark.parametrize("reverse", [False, True])
def test_duplicate_explicit_question_codes_are_still_reported(reverse):
    questions = [
        {"qid": "10", "title": "DUPLICATE", "type": "S"},
        {"qid": "20", "title": "DUPLICATE", "type": "S"},
    ]
    result = build_survey_structure(
        {
            "survey": {"sid": "100"},
            "questions": questions[::-1] if reverse else questions,
        }
    )

    assert len(result["survey"]["fields"]) == 1
    assert any(
        issue["code"] == "DUPLICATE_QUESTION_CODE" and issue["level"] == "error"
        for issue in result["issues"]
    )
