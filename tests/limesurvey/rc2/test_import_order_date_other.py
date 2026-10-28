from limesurvey_connector.limesurvey.normalization import build_survey_structure


def test_dates_and_random_order_are_converted_without_property_warnings():
    value = build_survey_structure(
        {
            "survey": {"sid": "1", "language": "es"},
            "groups": [
                {
                    "gid": "10",
                    "group_name": "Dates",
                    "group_order": 0,
                    "randomization_group": "sections",
                }
            ],
            "questions": [
                {
                    "qid": "11",
                    "gid": "10",
                    "sid": "1",
                    "parent_qid": "0",
                    "title": "DATE",
                    "type": "D",
                    "question": "Date",
                    "attributes": {
                        "dropdown_dates": "1",
                        "dropdown_dates_month_style": "2",
                        "reverse": "1",
                        "random_group": "dates",
                        "dropdown_dates_year_min": "2000",
                        "dropdown_dates_year_max": "2026",
                    },
                }
            ],
        }
    )
    rendering = value["survey"]["fields"][0]["rendering"]
    assert rendering["dateDropdowns"] is True
    assert rendering["monthLabelStyle"] == "numeric"
    assert rendering["reverseYearOrder"] is True
    assert (rendering["yearMin"], rendering["yearMax"]) == (2000, 2026)
    assert value["survey"]["groups"][0]["randomizationGroup"] == "sections"
    assert value["issues"] == []


def test_other_count_keeps_the_condition_and_missing_references_have_their_own_code():
    questions = [
        {
            "qid": "10",
            "sid": "1",
            "title": "PICKS",
            "type": "M",
            "question": "Choices",
            "other": "Y",
            "parent_qid": "0",
        },
        {"qid": "11", "sid": "1", "title": "A", "question": "A", "parent_qid": "10"},
        {"qid": "12", "sid": "1", "title": "B", "question": "B", "parent_qid": "10"},
        {
            "qid": "20",
            "sid": "1",
            "title": "DETAIL",
            "type": "S",
            "question": "Details",
            "parent_qid": "0",
            "relevance": "count(that.PICKS.NAOK)>2",
        },
        {
            "qid": "30",
            "sid": "1",
            "title": "MISSING_DETAIL",
            "type": "S",
            "question": "Missing",
            "parent_qid": "0",
            "relevance": "MISSING.NAOK == 1",
        },
    ]
    result = build_survey_structure(
        {"survey": {"sid": "1", "language": "es"}, "questions": questions}
    )
    fields = {f["code"]: f for f in result["survey"]["fields"]}
    assert fields["DETAIL"]["visibility"]["condition"]["type"] == "answered-count"
    assert [i["code"] for i in result["issues"]] == ["MISSING_CONDITION_REFERENCE"]
