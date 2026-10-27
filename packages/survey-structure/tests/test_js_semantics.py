import pytest

from survey_structure import _js


def test_keys_put_array_indices_first():
    assert _js.keys({"b": 1, "2": 1, "a": 1, "1": 1, "01": 1}) == ["1", "2", "b", "a", "01"]


def test_length_counts_utf16_code_units():
    assert _js.length("a") == 1
    assert _js.length("😀") == 2


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [(1, 1.0, True), (True, 1, False), ("1", 1, False), (None, None, True), (0, False, False)],
)
def test_strict_equal(left, right, expected):
    assert _js.strict_equal(left, right) is expected


@pytest.mark.parametrize(
    ("value", "expected"), [(1.0, "1"), (1.5, "1.5"), (True, "true"), (None, "null")]
)
def test_to_string(value, expected):
    assert _js.to_string(value) == expected
