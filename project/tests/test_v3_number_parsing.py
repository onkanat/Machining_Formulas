"""Tests for the shared user-number parser used by both calculation panels."""

from __future__ import annotations

import pytest

from machining_formulas.gui.v3_gui import parse_user_number


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("100", 100.0),
        (" 12.5 ", 12.5),
        ("12,5", 12.5),
        ("1.234,5", 1234.5),
        ("1 234,5", 1234.5),
        ("-3,25", -3.25),
        (7, 7.0),
    ],
)
def test_parse_user_number_accepts_common_formats(raw, expected):
    assert parse_user_number(raw, "Değer") == pytest.approx(expected)


@pytest.mark.parametrize("raw", ["", "  ", "abc", "1,2,3", None])
def test_parse_user_number_rejects_invalid_input(raw):
    with pytest.raises(ValueError, match="geçerli bir sayı"):
        parse_user_number(raw, "Density")
