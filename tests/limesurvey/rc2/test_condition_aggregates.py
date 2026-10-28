"""Portable aggregates and boolean branching use synthetic, reusable identifiers."""

import pytest

from limesurvey_connector.limesurvey.normalization.condition_parser import (
    parse_limesurvey_condition,
)
from limesurvey_connector.limesurvey.normalization.condition_references import (
    UnsupportedConditionError,
    build_condition_references,
)
from limesurvey_connector.limesurvey.normalization.condition_tokens import split_arguments


def references(native=":", attributes=None):
    questions = [
        {
            "qid": "10",
            "gid": "5",
            "title": "QUESTION_1",
            "type": native,
            "attributes": attributes or {},
        },
        {"qid": "20", "parent_qid": "10", "title": "ROW_1", "scale_id": "0"},
        {"qid": "21", "parent_qid": "10", "title": "ROW_2", "scale_id": "0"},
        {"qid": "30", "gid": "5", "title": "QUESTION_2", "type": "Q"},
        {"qid": "31", "parent_qid": "30", "title": "ITEM_1"},
    ]
    if native in {":", ";"}:
        questions.extend(
            [
                {"qid": "22", "parent_qid": "10", "title": "COLUMN_1", "scale_id": "1"},
                {"qid": "23", "parent_qid": "10", "title": "COLUMN_2", "scale_id": "1"},
            ]
        )
    return build_condition_references(questions, "100")


def test_numeric_matrix_indexes_cells_instead_of_axis_labels():
    index = references()
    assert index["QUESTION_1_ROW_1_COLUMN_2"] == ("QUESTION_1", "ROW_1_COLUMN_2")
    assert index["100X5X10ROW_1_COLUMN_2"] == ("QUESTION_1", "ROW_1_COLUMN_2")
    assert "QUESTION_1_ROW_1" not in index
    assert "QUESTION_1_COLUMN_2" not in index


def test_dual_scale_indexes_each_response_cell():
    index = references("1")
    for alias in ["QUESTION_1_ROW_1_0", "QUESTION_1_ROW_1#0", "100X5X10ROW_1#0"]:
        assert index[alias] == ("QUESTION_1", "ROW_1_0")
    assert parse_limesurvey_condition('100X5X10ROW_1#0.NAOK == "A"', index)[
        "responseReference"
    ] == {"fieldCode": "QUESTION_1", "responseItemCode": "ROW_1_0"}


@pytest.mark.parametrize(
    ("native", "kind"),
    [
        ("M", "selection-count"),
        ("P", "selection-count"),
        ("Q", "answered-count"),
        ("F", "answered-count"),
    ],
)
def test_count_explicit_cells_of_one_question(native, kind):
    condition = parse_limesurvey_condition(
        "count(QUESTION_1_ROW_1.NAOK, Q10_S21.NAOK) >= 2", references(native)
    )
    assert condition == {
        "type": kind,
        "responseReference": {"fieldCode": "QUESTION_1"},
        "responseItemCodes": ["ROW_1", "ROW_2"],
        "operator": "greater-than-or-equal",
        "value": 2,
    }


def test_count_explicit_matrix_cells_can_include_zero_answers():
    condition = parse_limesurvey_condition(
        "count(QUESTION_1_ROW_1_COLUMN_1.NAOK, QUESTION_1_ROW_2_COLUMN_2.NAOK) == 2", references()
    )
    assert condition["type"] == "answered-count"
    assert condition["responseItemCodes"] == ["ROW_1_COLUMN_1", "ROW_2_COLUMN_2"]


@pytest.mark.parametrize(
    "function", ['countif("Y", {selector})', 'countifop("==", "Y", {selector})']
)
def test_countif_does_not_count_a_comment_whose_text_is_y_as_a_selection(function):
    with pytest.raises(UnsupportedConditionError, match="cannot be counted faithfully"):
        parse_limesurvey_condition(
            function.format(selector="that.QUESTION_1.NAOK") + " > 0", references("P")
        )
    assert (
        parse_limesurvey_condition(
            function.format(selector="that.QUESTION_1.nocomments.NAOK") + " > 0", references("P")
        )["type"]
        == "selection-count"
    )


@pytest.mark.parametrize("function", ["sum", "min", "max"])
@pytest.mark.parametrize(
    "selector", ["that.QUESTION_1.NAOK", "self.NAOK", "that.QUESTION_1.nocomments.NAOK"]
)
def test_numeric_matrix_uses_neutral_aggregation(function, selector):
    assert parse_limesurvey_condition(
        f"{function}({selector}) >= 2.5", references(), "QUESTION_1"
    ) == {
        "type": "numeric-aggregate",
        "aggregation": function,
        "responseReference": {"fieldCode": "QUESTION_1"},
        "operator": "greater-than-or-equal",
        "value": 2.5,
    }


@pytest.mark.parametrize("function", ["sum", "min", "max"])
def test_numeric_aggregate_explicit_cells_keep_the_subset(function):
    condition = parse_limesurvey_condition(
        f"{function}(QUESTION_1_ROW_1_COLUMN_1.NAOK, QUESTION_1_ROW_2_COLUMN_2.NAOK) == -2",
        references(),
    )
    assert condition["aggregation"] == function
    assert condition["responseItemCodes"] == ["ROW_1_COLUMN_1", "ROW_2_COLUMN_2"]


@pytest.mark.parametrize(
    ("native", "attributes"),
    [("Q", {}), (";", {}), ("M", {}), (":", {"multiflexible_checkbox": "1"})],
)
@pytest.mark.parametrize("function", ["sum", "min", "max"])
def test_numeric_aggregates_do_not_coerce_text_or_checkbox_answers(native, attributes, function):
    with pytest.raises(UnsupportedConditionError, match="numeric matrix"):
        parse_limesurvey_condition(
            f"{function}(that.QUESTION_1.NAOK) > 0", references(native, attributes)
        )


@pytest.mark.parametrize("function", ["min", "max"])
@pytest.mark.parametrize("comparison", ["== -2", "== 2", "> 0", "> 2", ">= 2", "< -2", "<= -2"])
def test_extreme_comparisons_have_unambiguous_blank_results(function, comparison):
    assert (
        parse_limesurvey_condition(
            f"{function}(self.NAOK) {comparison}", references(), "QUESTION_1"
        )["aggregation"]
        == function
    )


@pytest.mark.parametrize("function", ["min", "max"])
@pytest.mark.parametrize(
    "comparison", ["== 0", "!= 0", "!= 2", "> -2", ">= 0", ">= -2", "< 0", "< 2", "<= 0", "<= 2"]
)
def test_extreme_comparisons_do_not_guess_empty_value_coercion(function, comparison):
    with pytest.raises(UnsupportedConditionError, match="empty-value semantics"):
        parse_limesurvey_condition(
            f"{function}(self.NAOK) {comparison}", references(), "QUESTION_1"
        )


@pytest.mark.parametrize("function", ["avg", "mean"])
def test_average_is_not_silently_aliased_to_a_nonexistent_source_function(function):
    with pytest.raises(UnsupportedConditionError, match="not built-in"):
        parse_limesurvey_condition(f"{function}(self.NAOK) > 0", references(), "QUESTION_1")


# Invalid arguments share the same parser across aggregates; keep each failure once.
@pytest.mark.parametrize(
    ("function", "inputs"),
    [
        ("sum", value)
        for value in [
            "",
            "self",
            "self.comments.NAOK",
            "self.sq_ROW_1.NAOK",
            "self.NAOK, 1",
            "QUESTION_1_ROW_1_COLUMN_1",
            "QUESTION_1_ROW_1_COLUMN_1.NAOK, QUESTION_2_ITEM_1.NAOK",
            "QUESTION_1_ROW_1_COLUMN_1.NAOK, QUESTION_1_ROW_1_COLUMN_1.NAOK",
            "QUESTION_1_ROW_1_COLUMN_1.NAOK + 1",
            "sum(self.NAOK)",
        ]
    ]
    + [("min", ""), ("max", "")],
)
def test_all_numeric_aggregates_reject_unsupported_inputs(function, inputs):
    with pytest.raises(UnsupportedConditionError):
        parse_limesurvey_condition(f"{function}({inputs}) > 0", references(), "QUESTION_1")


@pytest.mark.parametrize(
    ("function", "value"),
    [("sum", value) for value in ["NaN", "Infinity", "1e999", "1_0", "0x10", '"2"', "1 + 2"]]
    + [("min", "NaN"), ("max", "NaN")],
)
def test_numeric_aggregate_threshold_is_a_real_finite_numeric_literal(function, value):
    with pytest.raises(UnsupportedConditionError, match="finite numeric literal"):
        parse_limesurvey_condition(f"{function}(self.NAOK) > {value}", references(), "QUESTION_1")


@pytest.mark.parametrize(
    "expression",
    [
        "count(QUESTION_1_ROW_1.NAOK, QUESTION_2_ITEM_1.NAOK) > 0",
        "count(QUESTION_1_ROW_1.NAOK, QUESTION_1_ROW_1.NAOK) > 0",
        "count(QUESTION_1_ROW_1, QUESTION_1_ROW_2) > 0",
        "count(QUESTION_1.NAOK, QUESTION_1_ROW_2.NAOK) > 0",
        "count(QUESTION_1_ROW_1comment.NAOK, QUESTION_1_ROW_2.NAOK) > 0",
        "count(QUESTION_1_ROW_1.NAOK,) > 0",
        "count(QUESTION_1_ROW_1.NAOK) >= 0.5",
        "count(that.QUESTION_1.sq_ROW_1.NAOK) > 0",
        "count(that.QUESTION_1.comments.NAOK) > 0",
        "count(that.QUESTION_1_ROW_1.NAOK) > 0",
        "count(that.QUESTION_1.NAOK.nocomments) > 0",
        "count(that.QUESTION_1.NAOK.code) > 0",
        'countif("y", that.QUESTION_1.nocomments.NAOK) > 0',
        "avg(that.QUESTION_1.NAOK) > 0",
        "mean(that.QUESTION_1.NAOK) > 0",
        "sum(that.QUESTION_1) > 0",
        "sum(that.QUESTION_1.sq_ROW_1.NAOK) > 0",
    ],
)
def test_unsupported_aggregate_inputs_remain_explicit_errors(expression):
    with pytest.raises(UnsupportedConditionError):
        parse_limesurvey_condition(expression, references("P"))


def test_if_boolean_branches_lower_to_existing_logical_nodes():
    condition = parse_limesurvey_condition(
        'if(QUESTION_2_ITEM_1.NAOK == "and, or", count(self.NAOK) > 0, false)',
        references("Q"),
        "QUESTION_1",
    )
    assert condition["type"] == "any"
    positive, negative = condition["conditions"]
    assert positive["type"] == negative["type"] == "all"
    assert positive["conditions"][0]["value"] == "and, or"
    assert positive["conditions"][1]["type"] == "answered-count"
    assert negative["conditions"][0] == {"type": "not", "condition": positive["conditions"][0]}
    assert negative["conditions"][1] == {"type": "constant", "value": False}


def test_arguments_do_not_split_nested_or_quoted_commas():
    assert split_arguments('QUESTION_1 == "x,y", if(true, 1, 0), false') == [
        'QUESTION_1 == "x,y"',
        "if(true, 1, 0)",
        "false",
    ]
    assert (
        parse_limesurvey_condition('if(QUESTION_2_ITEM_1.NAOK == "if(x,y,z)", 1, 0)', references())[
            "type"
        ]
        == "any"
    )


def test_deep_nested_if_is_rejected_before_expanding_its_tree():
    expression = "true"
    for _ in range(100):
        expression = f"if({expression}, true, false)"
    with pytest.raises(UnsupportedConditionError, match="Nested if"):
        parse_limesurvey_condition(expression, references())


def test_independent_if_conditions_are_still_supported():
    assert (
        parse_limesurvey_condition("if(true, 1, 0) and if(false, 0, 1)", references())["type"]
        == "all"
    )


@pytest.mark.parametrize(
    "function", ['countif("1", that.QUESTION_1.NAOK)', 'countifop("==", "1", self.NAOK)']
)
def test_checkbox_matrix_counts_selected_ones_not_nonempty_zero_cells(function):
    condition = parse_limesurvey_condition(
        function + " >= 2", references(":", {"multiflexible_checkbox": "1"}), "QUESTION_1"
    )
    assert condition == {
        "type": "selection-count",
        "responseReference": {"fieldCode": "QUESTION_1"},
        "operator": "greater-than-or-equal",
        "value": 2,
    }


@pytest.mark.parametrize(
    "function", ["count(self.NAOK)", 'countif("Y", self.NAOK)', 'countif("0", self.NAOK)']
)
def test_checkbox_matrix_does_not_translate_other_counts_as_selected(function):
    with pytest.raises(UnsupportedConditionError):
        parse_limesurvey_condition(
            function + " > 0", references(":", {"multiflexible_checkbox": "1"}), "QUESTION_1"
        )


@pytest.mark.parametrize("native", [":", "M", "P", "Q"])
def test_countif_one_is_not_used_for_noncheckbox_fields(native):
    with pytest.raises(UnsupportedConditionError):
        parse_limesurvey_condition('countif("1", self.NAOK) > 0', references(native), "QUESTION_1")


def test_empty_this_resolves_only_a_current_scalar_response():
    index = references("N")
    assert parse_limesurvey_condition("is_empty(this.NAOK)", index, "QUESTION_1") == {
        "type": "not-answered",
        "responseReference": {"fieldCode": "QUESTION_1"},
    }
    assert parse_limesurvey_condition("this.NAOK == null", index, "QUESTION_1")["value"] is None
    for expression in ["is_empty(this.NAOK)", "this.NAOK == null"]:
        with pytest.raises(UnsupportedConditionError, match="current scalar"):
            parse_limesurvey_condition(expression, index)
        with pytest.raises(UnsupportedConditionError, match="specific response cell"):
            parse_limesurvey_condition(expression, references(), "QUESTION_1")


@pytest.mark.parametrize(
    "expression",
    [
        "if(true, 10+1, 20)",
        'if(true, "yes", "no")',
        "if(true, QUESTION_1, 0)",
        "if(true, 1)",
        "if(true,,0)",
    ],
)
def test_if_does_not_claim_general_value_or_arithmetic_support(expression):
    with pytest.raises(UnsupportedConditionError):
        parse_limesurvey_condition(expression, references())
