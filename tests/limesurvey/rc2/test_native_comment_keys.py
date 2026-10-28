from limesurvey_connector.limesurvey.normalization import build_survey_structure


def test_native_comment_keys_and_other_are_not_reformatted():
    result = build_survey_structure(
        {
            "survey": {"sid": "1"},
            "questions": [
                {
                    "qid": "1",
                    "title": "Q001",
                    "type": "O",
                    "answeroptions": {"A": {"answer": "A"}},
                    "other": "Y",
                },
                {"qid": "2", "title": "Q002", "type": "P", "other": "Y"},
                {"qid": "3", "title": "A1", "type": "T", "parent_qid": "2"},
            ],
        }
    )
    first, second = result["survey"]["fields"]
    # limesurvey-column-names: LimeSurvey exports Q001_comment and Q001_other (rc2-api: Q001comment, Q001other).
    assert first["commentResponseKey"] == "Q001_comment"
    assert first["other"]["textResponseKey"] == "Q001_other"
    assert second["options"][0]["commentResponseKey"] == "Q002_A1comment"
    assert second["other"]["commentResponseKey"] == "Q002_othercomment"


def test_dual_scale_fallback_uses_survey_language_and_preserves_custom_headers():
    question = {
        "qid": "1",
        "title": "M",
        "type": "1",
        "result": {
            "answeroptions_multiscale": {"0": {"A": {"answer": "A"}}, "1": {"B": {"answer": "B"}}}
        },
    }
    for language, expected in [("es", "Escala"), ("en", "Scale")]:
        result = build_survey_structure(
            {
                "survey": {"sid": "1", "language": language},
                "questions": [
                    question,
                    {"qid": "2", "parent_qid": "1", "title": "A1", "type": "T"},
                ],
            }
        )
        assert [c["label"] for c in result["survey"]["fields"][0]["matrix"]["columns"]] == [
            expected + " 1",
            expected + " 2",
        ]


def test_dual_scale_preserves_the_authored_headers_in_both_languages():
    for language in ["es", "en"]:
        result = build_survey_structure(
            {
                "survey": {"sid": "1", "language": language},
                "questions": [
                    {
                        "qid": "1",
                        "title": "M",
                        "type": "1",
                        "attributes": {
                            "dualscale_headerA": "Frecuencia",
                            "dualscale_headerB": "Intensidad",
                        },
                        "result": {
                            "answeroptions_multiscale": {
                                "0": {"A": {"answer": "A"}},
                                "1": {"B": {"answer": "B"}},
                            }
                        },
                    },
                    {"qid": "2", "parent_qid": "1", "title": "A1", "type": "T"},
                ],
            }
        )
        assert [c["label"] for c in result["survey"]["fields"][0]["matrix"]["columns"]] == [
            "Frecuencia",
            "Intensidad",
        ]
