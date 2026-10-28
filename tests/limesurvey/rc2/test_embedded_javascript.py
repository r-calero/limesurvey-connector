"""Executable rich text is diagnosed and retained, never evaluated."""

import pytest

from limesurvey_connector.limesurvey.normalization import build_survey_structure
from limesurvey_connector.limesurvey.normalization.text_sanitizer import (
    contains_embedded_javascript,
)


@pytest.mark.parametrize(
    "html",
    [
        "&lt;script&gt;window.run()&lt;/script&gt;",
        '&lt;button onclick="window.run()"&gt;Example&lt;/button&gt;',
        "<!-- <script>window.run()</script> -->",
        '<script type="application/json">{"example": "{value}"}</script>',
        '<script type="application/ld+json">{"name":"Example"}</script>',
        "<script>  \n </script>",
        '<p data-onclick="documentation">Example {text}</p>',
    ],
)
def test_nonexecutable_markup_is_not_misreported(html):
    assert not contains_embedded_javascript(html)


@pytest.mark.parametrize(
    "html",
    [
        "<script>window.run()</script>",
        '<SCRIPT type="text/javascript">window.run()</SCRIPT>',
        '<script src="https://example.invalid/code.js"></script>',
        '<script type="module">window.run()</script>',
        '<button onclick="window.run()">Run</button>',
        '<input oninput="if (this.value > 7) this.value = 7">',
        '<a href="javascript:window.run()">Run</a>',
    ],
)
def test_executable_markup_is_detected_without_running_it(html):
    assert contains_embedded_javascript(html)


def test_question_with_comment_filter_and_exclusive_option_keeps_one_explicit_diagnostic():
    html = """<p>Frecuencia</p><script>
    function setInputFilter(input, value) { return value >= 1 && value <= 7; }
    document.getElementById('SQ015').onclick = function () {
      document.getElementById('SQ001').disabled = this.checked;
    };
    </script><script>window.initialSelection = 'SQ015';</script>"""
    result = build_survey_structure(
        {
            "survey": {"sid": "synthetic"},
            "questions": [
                {
                    "qid": "parent",
                    "title": "S3P33",
                    "type": "P",
                    "question": html,
                    "result": {"question": html},
                },
                {
                    "qid": "child1",
                    "parent_qid": "parent",
                    "title": "SQ001",
                    "question": "Una opción",
                },
                {"qid": "child15", "parent_qid": "parent", "title": "SQ015", "question": "Ninguna"},
            ],
        }
    )
    field = result["survey"]["fields"][0]
    assert field["label"] == "Frecuencia"
    assert field["source"]["originDetails"][0]["unconvertedAttributes"]["question"] == html
    assert (
        len(result["issues"]) == 1
    )  # Neither duplicate source copies nor JS braces create extra issues.
    issue = result["issues"][0]
    assert issue["code"] == "SOURCE_SCRIPT_NOT_EXECUTED"
    assert issue["questionCode"] == "S3P33"
    assert issue["details"] == {
        "rule": "embedded_javascript",
        "sourceExpression": html,
        "scope": "field",
    }
    assert "no se reproducen" in issue["message"]
    assert (
        result["sourceMetrics"]["conditionsDetected"] == 0
    )  # JS was not parsed as a relevance condition.


def test_event_handler_in_question_help_is_preserved():
    html = '<button onclick="window.run()">Ayuda</button>'
    result = build_survey_structure(
        {
            "survey": {"sid": "synthetic"},
            "questions": [
                {"qid": "q1", "title": "Q1", "type": "S", "question": "Question", "help": html},
            ],
        }
    )
    field = result["survey"]["fields"][0]
    assert field["help"] == "Ayuda"
    assert field["source"]["originDetails"][0]["unconvertedAttributes"] == {"help": html}
    assert result["issues"][0]["details"]["sourceExpression"] == html
