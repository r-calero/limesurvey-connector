"""Intentional changes to LimeSurvey handling (conformance/intentional-changes.json)."""

import pytest

from limesurvey_connector.limesurvey.naming import (
    underscore_column,
    underscore_record,
    with_limesurvey_names,
)
from limesurvey_connector.limesurvey.normalization import build_survey_structure
from limesurvey_connector.limesurvey.responses import system_columns_in, translate_csv
from limesurvey_connector.remote import decode_response_export
from survey_data_dictionary import build_survey_dictionary


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        ("Q1[SQ001]", "Q1_SQ001"),
        ("Q11[SQ001comment]", "Q11_SQ001comment"),
        ("Q3[1]", "Q3_1"),
        ("Q2[SQ001][1]", "Q2_SQ001_0"),
        ("Q2[SQ001][2]", "Q2_SQ001_1"),
        ("Q7[SQ001_SQ002]", "Q7_SQ001_SQ002"),
        ("Q1_SQ001", "Q1_SQ001"),
        ("Clasifica [Fidel][Política]", "Clasifica [Fidel][Política]"),
        ("Doble escala [Proteínas][Escala 1]", "Doble escala [Proteínas][Escala 1]"),
    ],
)
def test_bracketed_code_headings_become_underscore_names(header, expected):
    assert underscore_column(header) == expected


def test_underscore_record_never_overwrites_an_existing_key():
    assert underscore_record({"Q1[A]": "x", "Q1_A": "y"}) == {"Q1[A]": "x", "Q1_A": "y"}


def test_option_comments_use_limesurvey_names():
    field = {
        "id": "q",
        "code": "Q11",
        "type": "multiple-choice-with-comments",
        "label": "L",
        "groupId": "g",
        "source": {"platform": "limesurvey", "questionId": "7"},
        "options": [{"code": "SQ001", "label": "A"}],
    }
    survey = {
        "surveyStructureVersion": "2.1.0",
        "id": "5",
        "source": {"platform": "limesurvey"},
        "groups": [{"id": "g", "order": 0}],
        "fields": [field],
    }
    renamed = with_limesurvey_names(build_survey_dictionary(survey))
    comment = next(entry for entry in renamed["fields"] if entry["responseKey"].endswith("comment"))
    assert comment["responseKey"] == "Q11_SQ001comment"
    assert "Q11_SQ001_comment" in comment["aliases"]
    assert "5XgX7SQ001comment" in comment["aliases"]


def _other_survey(type_, **other):
    field = {
        "id": "q",
        "code": "Q12",
        "type": type_,
        "label": "L",
        "groupId": "g",
        "source": {"platform": "limesurvey", "questionId": "7"},
        "options": [{"code": "A1", "label": "A"}],
        "other": {"code": "-oth-", "label": "Otro", "textResponseKey": "Q12other", **other},
    }
    return {
        "surveyStructureVersion": "2.1.0",
        "id": "5",
        "source": {"platform": "limesurvey"},
        "groups": [{"id": "g", "order": 0}],
        "fields": [field],
    }


def test_other_text_uses_limesurvey_name():
    # limesurvey-rc2-api 2.1.0 writes Qother; LimeSurvey exports Q_other.
    renamed = with_limesurvey_names(build_survey_dictionary(_other_survey("single-choice")))
    other = renamed["fields"][1]
    assert other["responseKey"] == "Q12_other"
    assert other["aliases"][-2:] == ["5XgX7other", "Q12other"]


def test_other_comment_uses_limesurvey_name():
    survey = _other_survey("multiple-choice-with-comments", commentResponseKey="Q12_othercomment")
    renamed = with_limesurvey_names(build_survey_dictionary(survey))
    keys = {entry["responseKey"]: entry for entry in renamed["fields"]}
    assert {"Q12_other", "Q12_othercomment"} <= set(keys)
    assert keys["Q12_othercomment"]["parentCode"] == "Q12_other"
    assert "5XgX7othercomment" in keys["Q12_othercomment"]["aliases"]


def test_vv_export_trailing_tab_and_not_shown_placeholder():
    dictionary = with_limesurvey_names(build_survey_dictionary(_other_survey("single-choice")))
    vv = "L\tL [Otro]\t\nQ12\tQ12_other\t\n{question_not_shown}\t{question_not_shown}\n"
    result = translate_csv(dictionary, vv, format="vv", delimiter="\t")
    assert result["canonical"]["headers"] == ["Q12", "Q12_other"]
    assert result["translated"]["issues"] == []
    cell = result["translated"]["responses"][0]["fields"][0]
    assert cell["sourceValue"] == "{question_not_shown}"
    assert (cell["displayValue"], cell["missing"]) == (None, True)


def _question(type_, **extra):
    return {
        "qid": "100",
        "gid": "1",
        "parent_qid": "0",
        "title": "Q",
        "type": type_,
        "question": "Q",
        **extra,
    }


def _rows(*codes):
    return [
        {
            "qid": str(200 + index),
            "gid": "1",
            "parent_qid": "100",
            "title": code,
            "type": "T",
            "question": code,
            "question_order": str(index),
            "scale_id": "0",
        }
        for index, code in enumerate(codes)
    ]


def _normalize(question, children, language="es"):
    return build_survey_structure(
        {
            "survey": {"sid": "1", "language": language},
            "groups": [{"gid": "1", "group_name": "G", "group_order": "0"}],
            "questions": [question, *children],
        }
    )


def test_array_increase_same_decrease():
    result = _normalize(_question("E"), _rows("R1", "R2"))
    field = result["survey"]["fields"][0]
    assert field["matrix"]["mode"] == "single"
    assert [(column["code"], column["label"]) for column in field["matrix"]["columns"]] == [
        ("I", "Aumenta"),
        ("S", "Igual"),
        ("D", "Disminuye"),
    ]
    assert result["issues"] == []


def test_dual_scale_split_by_scale_id_when_codes_differ():
    options = {
        "A1": {"answer": "Low", "scale_id": "0", "order": "1"},
        "B1": {"answer": "Rarely", "scale_id": "1", "order": "1"},
    }
    field = _normalize(_question("1", answeroptions=options), _rows("R1"))["survey"]["fields"][0]
    assert [
        [option["code"] for option in column["options"]] for column in field["matrix"]["columns"]
    ] == [["A1"], ["B1"]]


@pytest.mark.parametrize(("language", "expected"), [("es-MX", "Escala"), ("en", "Scale")])
def test_dual_scale_default_headers_follow_survey_language(language, expected):
    multiscale = {"0": {"A1": {"answer": "Low"}}, "1": {"A1": {"answer": "Rarely"}}}
    question = _question("1", answeroptions_multiscale=multiscale)
    field = _normalize(question, _rows("R1"), language)["survey"]["fields"][0]
    assert [column["label"] for column in field["matrix"]["columns"]] == [
        f"{expected} 1",
        f"{expected} 2",
    ]


def test_dual_scale_read_from_question_level_multiscale():
    multiscale = {"0": {"A1": {"answer": "Low"}}, "1": {"A1": {"answer": "Rarely"}}}
    field = _normalize(_question("1", answeroptions_multiscale=multiscale), _rows("R1"))["survey"][
        "fields"
    ][0]
    assert [column["options"][0]["label"] for column in field["matrix"]["columns"]] == [
        "Low",
        "Rarely",
    ]


def test_dual_scale_with_one_scale_lost_by_limesurvey_is_reported():
    options = {"A1": {"answer": "Low", "scale_id": "0", "order": "1"}}
    result = _normalize(_question("1", answeroptions=options), _rows("R1"))
    assert result["survey"]["fields"] == []
    assert "import the .lss file" in result["issues"][0]["message"]


def test_timing_columns_are_recognized():
    found = system_columns_in(
        ["interviewtime", "groupTime3", "Q3Time", "OtherTime", "submitdate"], {"Q3"}
    )
    assert [column["code"] for column in found] == [
        "submitdate",
        "interviewtime",
        "groupTime3",
        "Q3Time",
    ]
    assert found[2]["labels"]["es"] == "Tiempo en el grupo 3 (segundos)"


def test_wrapped_json_export_is_unwrapped():
    content = b'{"responses": [{"7": {"id": "7", "Q1[SQ001]": "Y"}}, {"9": {"id": "9", "Q1[SQ001]": "N"}}]}'
    dataset = decode_response_export(content, 5, "json", None, 1000)
    assert dataset["responseIds"] == ["7", "9"]
    assert dataset["responses"][0] == {"id": "7", "Q1_SQ001": "Y"}
