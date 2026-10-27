import pytest

from survey_structure import test_pattern as ecmascript_test
from survey_structure import to_python_pattern
from survey_structure.patterns import is_valid_pattern, utf16_units, valid_flags


@pytest.mark.parametrize(
    "pattern",
    [
        "[a-z]+",
        "\\d{3}",
        "(?:ab)+",
        "(?<=a)b",
        "a{,3}",
        "\\B",
        "(?<n>a)\\k<n>",
        "[^]",
        "\\Z",
        "[\\w-.]+",
    ],
)
def test_accepts_patterns_with_an_equivalent(pattern):
    assert is_valid_pattern(pattern)


@pytest.mark.parametrize(
    "pattern", ["(?i)a", "(?P<n>a)", "(?>a)", "a++", "[", "(?#c)", "[z-a]", "{2}", "(?<=a+)b"]
)
def test_rejects_invalid_or_untranslatable_patterns(pattern):
    assert not is_valid_pattern(pattern)


@pytest.mark.parametrize(
    ("pattern", "value", "flags", "expected"),
    [
        ("\\d+", "abc123", "", True),
        ("\\d+", "١٢", "", False),
        ("^a$", "a\n", "", False),
        ("a", "a\n", "", True),
        ("\\s", chr(0xA0), "", True),
        ("a{,3}", "a{,3}", "", True),
        ("\\B", "", "", True),
        ("(a)|b\\1", "b", "", True),
        (".", "😀", "", True),
        ("^.$", "😀", "", False),
        ("^..$", "😀", "", True),
        ("\\Z", "Z", "", True),
        ("^b", "a\nb", "", False),
        ("^b", "a\nb", "m", True),
        ("^b", "a\rb", "m", True),
        ("^b", "a" + chr(0x2028) + "b", "m", True),
        ("a$", "a\r\nb", "m", True),
        ("a.b", "a\nb", "", False),
        ("a.b", "a\nb", "s", True),
        ("^ä$", "Ä", "i", True),
        ("^k$", chr(0x212A), "i", False),
        ("^s$", chr(0x17F), "i", False),
        ("^[a-z]$", "Q", "i", True),
        ("^[^a]$", "A", "i", False),
    ],
)
def test_search_follows_ecmascript(pattern, value, flags, expected):
    assert ecmascript_test(pattern, value, flags) is expected


@pytest.mark.parametrize(
    ("flags", "valid"), [("", True), ("ims", True), ("ii", False), ("x", False), ("uv", False)]
)
def test_flag_syntax_follows_regexp(flags, valid):
    assert valid_flags(flags) is valid


def test_unicode_flags_and_case_insensitive_backreferences_are_rejected():
    assert not is_valid_pattern("a", "u")
    assert not is_valid_pattern("(a)\\1", "i")
    assert is_valid_pattern("(a)\\1", "m")


def test_public_helpers():
    assert to_python_pattern("(?<n>a)\\k<n>").pattern == "(?P<n>a)(?(n)(?P=n))"
    assert ecmascript_test("[\\w-.]+@", "ana.b@x")
    assert utf16_units(chr(0x1F600)) == chr(0xD83D) + chr(0xDE00)
    with pytest.raises(ValueError, match="cannot be matched"):
        to_python_pattern("(?<=a+)b")
