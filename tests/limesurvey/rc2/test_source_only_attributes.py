import pytest

from limesurvey_connector.limesurvey.normalization import build_survey_structure


@pytest.mark.parametrize(
    ("attribute", "value"),
    [
        ("page_break", "1"),
        ("scale_export", "1"),
        ("statistics_showgraph", "0"),
        ("statistics_showgraph", "1"),
        ("statistics_showmap", "0"),
        ("statistics_graphtype", "1"),
        ("public_statistics", "1"),
    ],
)
def test_printing_export_and_statistics_are_preserved_without_answer_warnings(attribute, value):
    result = build_survey_structure(
        {
            "survey": {"sid": "1", "surveyls_title": "Test", "language": "es"},
            "language": "es",
            "groups": [{"gid": "1", "group_name": "Group"}],
            "questions": [
                {
                    "qid": "1",
                    "gid": "1",
                    "parent_qid": "0",
                    "type": "S",
                    "title": "Q",
                    "question": "Text",
                    "attributes": {attribute: value},
                }
            ],
        }
    )
    assert result["issues"] == []
    assert (
        result["survey"]["fields"][0]["source"]["originDetails"][0]["unconvertedAttributes"][
            attribute
        ]
        == value
    )


def test_unknown_answer_setting_still_warns():
    result = build_survey_structure(
        {
            "survey": {"sid": "1", "surveyls_title": "Test", "language": "es"},
            "language": "es",
            "groups": [{"gid": "1", "group_name": "Group"}],
            "questions": [
                {
                    "qid": "1",
                    "gid": "1",
                    "parent_qid": "0",
                    "type": "S",
                    "title": "Q",
                    "question": "Text",
                    "attributes": {"future_response_rule": "1"},
                }
            ],
        }
    )
    assert result["issues"][0]["code"] == "UNCONVERTED_SOURCE_PROPERTY"
