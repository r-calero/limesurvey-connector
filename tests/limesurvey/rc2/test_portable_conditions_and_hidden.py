from limesurvey_connector.limesurvey.normalization import build_survey_structure


def test_regex_condition_and_regexmatch_use_one_text_response():
    questions = [
        {"qid": "1", "title": "CODE", "type": "S"},
        {
            "qid": "2",
            "title": "FIRST",
            "type": "S",
            "relevance": r'regexMatch("/^(?:cat|dog)$/i", CODE.NAOK)',
        },
        {"qid": "3", "title": "SECOND", "type": "S", "relevance": 'CODE.NAOK REGEXP "^[0-9]{3}"'},
        {
            "qid": "4",
            "title": "GUI",
            "type": "S",
            "relevance": "regexMatch(/^[A-Z]{1,3}$/, CODE.NAOK)",
        },
    ]
    result = build_survey_structure({"survey": {"sid": "1"}, "questions": questions})
    fields = {field["code"]: field for field in result["survey"]["fields"]}
    assert fields["FIRST"]["visibility"]["condition"] == {
        "type": "pattern-match",
        "responseReference": {"fieldCode": "CODE"},
        "pattern": "^(?:cat|dog)$",
        "patternFlags": "i",
    }
    assert fields["SECOND"]["visibility"]["condition"]["pattern"] == "^[0-9]{3}"
    assert fields["GUI"]["visibility"]["condition"]["pattern"] == "^[A-Z]{1,3}$"
    assert not result["issues"]


def test_unsupported_pattern_or_missing_question_keeps_warning():
    questions = [
        {"qid": "1", "title": "CODE", "type": "S"},
        {
            "qid": "2",
            "title": "NO",
            "type": "S",
            "relevance": r'regexMatch("/\Aabc\z/", CODE.NAOK)',
        },
        {
            "qid": "3",
            "title": "MISSING",
            "type": "S",
            "relevance": r'regexMatch("/abc/", ABSENT.NAOK)',
        },
    ]
    result = build_survey_structure({"survey": {"sid": "1"}, "questions": questions})
    assert len(result["issues"]) == 2
    assert [issue["code"] for issue in result["issues"]] == [
        "UNSUPPORTED_SOURCE_EXPRESSION",
        "MISSING_CONDITION_REFERENCE",
    ]


def test_hidden_question_keeps_its_fixed_default_without_display_warning():
    result = build_survey_structure(
        {
            "survey": {"sid": "1"},
            "questions": [
                {
                    "qid": "1",
                    "title": "FOLIO",
                    "type": "S",
                    "defaultvalue": "ABC123",
                    "attributes": {"hidden": "1"},
                }
            ],
        }
    )
    field = result["survey"]["fields"][0]
    assert field["rendering"]["hidden"] is True
    assert field["defaultValue"] == "ABC123"
    assert not result["issues"]


def test_hidden_date_stays_hidden_when_its_display_order_is_mapped():
    result = build_survey_structure(
        {
            "survey": {"sid": "1"},
            "questions": [
                {
                    "qid": "1",
                    "title": "DATE",
                    "type": "D",
                    "attributes": {"hidden": "1", "date_time_format": "H:i d/m/Y"},
                }
            ],
        }
    )
    assert result["survey"]["fields"][0]["rendering"] == {
        "hidden": True,
        "dateOrder": "time-date",
    }


def test_k_limit_can_use_direct_numeric_question_only():
    result = build_survey_structure(
        {
            "survey": {"sid": "1"},
            "questions": [
                {"qid": "1", "title": "TOTAL", "type": "N"},
                {
                    "qid": "2",
                    "title": "AMOUNTS",
                    "type": "K",
                    "attributes": {
                        "max_num_value": "TOTAL.NAOK",
                        "min_num_value_n": "{TOTAL.NAOK}",
                        "equals_num_value": "TOTAL.NAOK + 1",
                    },
                },
                {"qid": "3", "parent_qid": "2", "title": "A", "type": "K"},
            ],
        }
    )
    field = next(field for field in result["survey"]["fields"] if field["code"] == "AMOUNTS")
    assert field["responseValidation"]["sumMaxReference"] == "TOTAL"
    assert field["responseValidation"]["itemMinReference"] == "TOTAL"
    assert "sumEqualsReference" not in field["responseValidation"]
    assert any(
        issue.get("details", {}).get("rule") == "equals_num_value" for issue in result["issues"]
    )


def test_documented_pattern_keeps_common_elements_in_validation_and_condition():
    pattern = r"/^(rojo|azul)-[a-z]{2}[0-9]{3}(?:-[a-z]+)?$/i"
    result = build_survey_structure(
        {
            "survey": {"sid": "1"},
            "questions": [
                {"qid": "1", "title": "PREGUNTA1", "type": "S", "preg": pattern},
                {
                    "qid": "2",
                    "title": "PREGUNTA2",
                    "type": "S",
                    "relevance": f'regexMatch("{pattern}", PREGUNTA1.NAOK)',
                },
            ],
        }
    )
    first, second = result["survey"]["fields"]
    assert not result["issues"]
    assert first["responseValidation"] == {
        "responseFormatPattern": pattern[1:-2],
        "patternFlags": "i",
    }
    assert second["visibility"]["condition"] == {
        "type": "pattern-match",
        "responseReference": {"fieldCode": "PREGUNTA1"},
        "pattern": pattern[1:-2],
        "patternFlags": "i",
    }
