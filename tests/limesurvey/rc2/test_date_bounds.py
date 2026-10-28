"""Fixed LimeSurvey date limits use the existing portable date validation."""

from limesurvey_connector.limesurvey.normalization import build_survey_structure


def convert(attributes):
    return build_survey_structure(
        {
            "survey": {"sid": "123"},
            "questions": [
                {
                    "qid": "100",
                    "sid": "123",
                    "parent_qid": "0",
                    "title": "BIRTH",
                    "type": "D",
                    "question": "Birth date",
                    "attributes": attributes,
                },
            ],
        }
    )


def test_iso_date_bounds_become_portable_validation():
    result = convert({"date_min": "1940-01-01", "date_max": "1998-01-01"})
    assert result["survey"]["fields"][0]["responseValidation"] == {
        "dateMin": "1940-01-01",
        "dateMax": "1998-01-01",
    }
    assert not [
        issue
        for issue in result["issues"]
        if issue.get("details", {}).get("rule") in {"date_min", "date_max"}
    ]


def test_slash_dates_use_documented_month_day_year_order():
    result = convert({"date_min": "01/01/1919", "date_max": "01/01/2001"})
    assert result["survey"]["fields"][0]["responseValidation"] == {
        "dateMin": "1919-01-01",
        "dateMax": "2001-01-01",
    }


def test_dynamic_or_invalid_bound_stays_reported():
    result = convert({"date_min": "-10 years", "date_max": "2020-02-30"})
    assert result["survey"]["fields"][0].get("responseValidation") is None
    assert {issue["details"]["rule"] for issue in result["issues"]} == {"date_min", "date_max"}


def test_reversed_fixed_bounds_stay_reported():
    result = convert({"date_min": "2020-01-01", "date_max": "2000-01-01"})
    assert result["survey"]["fields"][0].get("responseValidation") is None
    assert {issue["details"]["rule"] for issue in result["issues"]} == {"date_min", "date_max"}


def test_calendar_bound_on_time_only_question_stays_reported():
    result = convert({"date_time_format": "HH:MM", "date_min": "2020-01-01"})
    assert result["survey"]["fields"][0]["dateValueType"] == "time"
    assert result["survey"]["fields"][0].get("responseValidation") is None
    assert [issue["details"]["rule"] for issue in result["issues"]] == ["date_min"]
