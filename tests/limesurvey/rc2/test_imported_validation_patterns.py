import pytest

from limesurvey_connector.limesurvey.normalization import build_survey_structure


def convert(pattern, native="S", attributes=None):
    return build_survey_structure(
        {
            "survey": {"sid": "test"},
            "questions": [
                {
                    "qid": "1",
                    "title": "Q",
                    "question": "Answer",
                    "type": native,
                    "preg": pattern,
                    "attributes": attributes or {},
                }
            ],
        }
    )


@pytest.mark.parametrize(
    ("pattern", "body", "flags"),
    [
        ("/^[0-9]+$/", "^[0-9]+$", ""),
        ("/^[0-9]{10}/", "^[0-9]{10}", ""),
        (r"/^.+?@.+?\..+$/", r"^.+?@.+?\..+$", ""),
        ("~abc~i", "abc", "i"),
        (r"/\d+\.[0-9]{1,2}\t/", r"\d+\.[0-9]{1,2}\t", ""),
        (r"/\\a\\u0041/", r"\\a\\u0041", ""),
        ("/a{65535}/", "a{65535}", ""),
        ("/a{1,65535}/", "a{1,65535}", ""),
        (r"/\{65536\}/", r"\{65536\}", ""),
        ("/[{65536}]/", "[{65536}]", ""),
    ],
)
def test_imports_text_patterns_without_adding_anchors_or_repairing_source(pattern, body, flags):
    result = convert(pattern, attributes={"maximum_chars": "20"})
    field = result["survey"]["fields"][0]
    assert not result["issues"]
    assert field["responseValidation"] == {
        "maxLength": 20,
        "responseFormatPattern": body,
        **({"patternFlags": flags} if flags else {}),
    }
    assert field["source"]["originDetails"][0]["nativeValidation"]["regularExpression"] == pattern


@pytest.mark.parametrize(
    "pattern",
    [
        "/[/",
        "/abc/u",
        r"/\Aabc\z/",
        "/a/b/",
        "/(?P<name>a)/",
        "/a++/",
        r"/\a/",
        r"/\u0041/",
        r"/\U00000041/",
        r"/\N{EM DASH}/",
        r"/\s/",
        r"/\S/",
        r"/\v/",
        r"/\x41/",
        r"/\0/",
        r"/\1/",
        "/a{65536}/",
        "/a{0,65536}/",
        "/a{65536,}/",
        "/a{99999999999999999999999999}/",
        "/a{,3}/",
        "/a{ 2 }/",
    ],
)
def test_unusable_patterns_remain_exact_source_and_warning(pattern):
    result = convert(pattern)
    assert "responseValidation" not in result["survey"]["fields"][0]
    assert result["issues"][0]["details"] == {"rule": "preg", "sourceValue": pattern}


def test_numeric_pattern_preserves_input_text_and_numeric_bounds():
    result = convert(
        "/^[0-9]{4}/",
        native="N",
        attributes={
            "minimum_answer": "10",
            "maximum_answer": "20",
            "num_value_int_only": "1",
            "maximum_chars": "4",
        },
    )
    field = result["survey"]["fields"][0]
    assert field["type"] == "number"
    assert field["responseValueType"] == "text"
    assert field["responseValidation"] == {
        "min": 10,
        "max": 20,
        "integer": True,
        "maxLength": 4,
        "responseFormatPattern": "^[0-9]{4}",
    }
    assert not result["issues"]


@pytest.mark.parametrize(
    ("pattern", "body"),
    [
        ("/^[0-9]{1}/", "^[0-9]{1}"),
        ("/^[0-9]/", "^[0-9]"),
        ("/^[0-9].*/", "^[0-9].*"),
        ("/^[0-9]{3}.*/", "^[0-9]{3}.*"),
        ("/^[0-9]{4}/", "^[0-9]{4}"),
    ],
)
def test_every_numeric_pattern_shape_in_cached_c3_sample(pattern, body):
    field = convert(pattern, native="N")["survey"]["fields"][0]
    assert field["responseValueType"] == "text"
    assert field["responseValidation"]["responseFormatPattern"] == body


def test_numeric_default_keeps_its_leading_zeroes():
    question = {
        "qid": "1",
        "title": "N",
        "type": "N",
        "preg": "/^[0-9]{4}/",
        "defaultvalue": "0012",
    }
    result = build_survey_structure({"survey": {"sid": "test"}, "questions": [question]})
    assert result["survey"]["fields"][0]["defaultValue"] == "0012"


def test_unportable_numeric_pattern_retains_old_numeric_response_and_warning():
    result = convert(r"/\A[0-9]{4}\z/", native="N")
    assert result["survey"]["fields"][0]["type"] == "number"
    assert "responseValueType" not in result["survey"]["fields"][0]
    assert result["issues"][0]["details"]["rule"] == "preg"


def test_numeric_question_without_pattern_still_uses_number_responses():
    field = convert("", native="N")["survey"]["fields"][0]
    assert field["type"] == "number"
    assert "responseValueType" not in field


def test_ranking_combines_two_maxima_and_keeps_every_option():
    result = build_survey_structure(
        {
            "survey": {"sid": "test"},
            "questions": [
                {
                    "qid": "1",
                    "title": "R",
                    "type": "R",
                    "question": "Rank",
                    "attributes": {"max_subquestions": "11", "max_answers": "9"},
                    "answeroptions": {str(n): {"answer": str(n)} for n in range(12)},
                }
            ],
        }
    )
    assert not result["issues"]
    assert result["survey"]["fields"][0]["responseValidation"]["maxSelections"] == 9
    assert len(result["survey"]["fields"][0]["options"]) == 12


def test_multiple_choice_other_comment_is_required_without_requiring_all_comments():
    result = build_survey_structure(
        {
            "survey": {"sid": "test"},
            "questions": [
                {
                    "qid": "1",
                    "title": "P",
                    "type": "P",
                    "question": "Choose",
                    "mandatory": "Y",
                    "other": "Y",
                    "attributes": {"other_comment_mandatory": "1"},
                },
                {"qid": "2", "parent_qid": "1", "title": "A", "question": "A", "type": "T"},
            ],
        }
    )
    assert not result["issues"]
    other = result["survey"]["fields"][0]["other"]
    assert other["commentRequired"] is True
    assert "textRequired" not in other
