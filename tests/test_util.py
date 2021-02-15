import pytest

from app_confetti import util


class TestStrToLiteral:

    @pytest.mark.parametrize("value", [{"a", "b"}, {"a": "b"}, [1, 2, 3], True, None, 5, 6.0, "value"])
    def test_non_string_literals_passed_through(self, value):
        assert util.str_to_literal(value) == value

    @pytest.mark.parametrize("value, expected", [
        ("{'a', 'b'}", {"a", "b"}),
        ("{'a': 'b'}", {"a": "b"}),
        ("[1, 2, 3]", [1, 2, 3]),
        ("True", True),
        ("None", None),
        ("5", 5),
        ("6.0", 6.0),
    ])
    def test_strings_return_literals(self, value, expected):
        assert util.str_to_literal(value) == expected
