import pytest

from limesurvey_connector.limesurvey.normalization import build_survey_structure


def convert(native_type, attributes):
    return build_survey_structure(
        {
            "survey": {"sid": "1", "surveyls_title": "Presentation", "language": "es"},
            "language": "es",
            "groups": [{"gid": "1", "group_name": "Group"}],
            "questions": [
                {
                    "qid": "1",
                    "gid": "1",
                    "parent_qid": "0",
                    "type": native_type,
                    "title": "Q",
                    "question": "Choice",
                    "mandatory": "Y",
                    "attributes": attributes,
                }
            ],
        }
    )


@pytest.mark.parametrize(
    ("native_type", "property_name", "value", "widget"),
    [
        ("Y", "display_type", "0", "button-group"),
        ("Y", "display_type", "1", "radio-group"),
        ("G", "display_type", "0", "button-group"),
        ("G", "display_type", "1", "radio-group"),
        ("5", "slider_rating", "0", "radio-group"),
        ("5", "slider_rating", "1", "rating"),
        ("5", "slider_rating", "2", "emoticon-slider"),
    ],
)
def test_native_presentation_preserves_answer_codes(native_type, property_name, value, widget):
    result = convert(native_type, {property_name: value})
    field = result["survey"]["fields"][0]
    assert field["rendering"]["widget"] == widget
    assert field["required"] is True
    assert [option["code"] for option in field["options"]] == {
        "Y": ["Y", "N"],
        "G": ["F", "M"],
        "5": ["1", "2", "3", "4", "5"],
    }[native_type]
    assert result["issues"] == []


@pytest.mark.parametrize(
    ("native_type", "attributes"),
    [("Y", {"display_type": "3"}), ("5", {"slider_rating": "3"}), ("S", {"display_type": "0"})],
)
def test_unrecognized_or_inapplicable_presentation_still_warns(native_type, attributes):
    result = convert(native_type, attributes)
    assert result["issues"][0]["code"] == "UNCONVERTED_SOURCE_PROPERTY"


def test_default_presentation_and_hidden_are_both_preserved():
    result = convert("Y", {"hidden": "1"})
    assert result["survey"]["fields"][0]["rendering"] == {"widget": "button-group", "hidden": True}
