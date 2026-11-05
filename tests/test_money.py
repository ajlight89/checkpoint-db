"""Tests for money.py."""

import pytest

from checkpoint import money

# Each case: an amount in cents, a percentage, and the result rounded half up.
PERCENTS = [
    pytest.param(1999, 10, 200, id="199.9 rounds up"),
    pytest.param(1244, 10, 124, id="124.4 rounds down"),
    pytest.param(1245, 10, 125, id="124.5 rounds up"),
    pytest.param(5000, 10, 500, id="exact"),
    pytest.param(0, 10, 0, id="zero amount"),
    pytest.param(5999, 0, 0, id="zero percent"),
]

# Each case: an amount in cents and how it is shown.
FORMATS = [
    pytest.param(0, "$0.00", id="zero"),
    pytest.param(5, "$0.05", id="cents only"),
    pytest.param(1999, "$19.99", id="dollars and cents"),
    pytest.param(123456, "$1,234.56", id="thousands"),
    pytest.param(-250, "-$2.50", id="negative"),
]


@pytest.mark.parametrize(("cents", "percent", "expected"), PERCENTS)
def test_percent_of(cents: int, percent: int, expected: int) -> None:
    assert money.percent_of(cents, percent) == expected


@pytest.mark.parametrize(("cents", "percent"), [(-1, 10), (100, -1)])
def test_percent_of_rejects_negatives(cents: int, percent: int) -> None:
    with pytest.raises(ValueError):
        money.percent_of(cents, percent)


def test_member_discount_is_ten_percent() -> None:
    assert money.MEMBER_DISCOUNT_PERCENT == 10
    assert money.member_discount(49999) == 5000


@pytest.mark.parametrize(("cents", "expected"), FORMATS)
def test_format_cents(cents: int, expected: str) -> None:
    assert money.format_cents(cents) == expected
