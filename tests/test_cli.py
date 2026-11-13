"""Tests for the command-line menus, with scripted answers in place of typing."""

import sqlite3

import pytest

from checkpoint import cli


def run(
    monkeypatch: pytest.MonkeyPatch, conn: sqlite3.Connection, *answers: str
) -> None:
    """Run the menus with ``answers`` typed in order, one per prompt."""
    replies = iter(answers)
    monkeypatch.setattr("builtins.input", lambda prompt: next(replies))
    cli.main(conn)


def words(out: str) -> list[list[str]]:
    """Split printed output into lines of words, so spacing does not matter."""
    return [line.split() for line in out.splitlines()]


def count(conn: sqlite3.Connection, table: str) -> int:
    """Return the number of rows in ``table`` (a fixed name, never user input)."""
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


# ----- Helpers and clerk lookups -----


def test_show_lines_up_columns(capsys: pytest.CaptureFixture[str]) -> None:
    rows = [("Cable", 1299, None), ("Console", 49999, 20000)]
    cli.show(("Item", "Price", "Trade"), rows, money=(1, 2))
    assert capsys.readouterr().out.splitlines() == [
        "Item       Price    Trade",
        "-------  -------  -------",
        "Cable     $12.99",
        "Console  $499.99  $200.00",
    ]


def test_ask_int_repeats_until_positive(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    replies = iter(["", "0", "-2", "two", "3"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(replies))
    assert cli.ask_int("Quantity") == 3
    assert capsys.readouterr().out.count("greater than zero") == 4


def test_stock_list_shows_prices(
    demo: sqlite3.Connection,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    run(monkeypatch, demo, "1", "1", "b", "q")
    out = capsys.readouterr().out
    row = "9 PlayStation 5 PlayStation 5 used_complete 2 $349.99 $200.00"
    assert row.split() in words(out)
    assert out.endswith("Goodbye.\n")


def test_unknown_phone_and_choice(
    demo: sqlite3.Connection,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    run(monkeypatch, demo, "1", "9", "3", "5095559999", "b", "q")
    out = capsys.readouterr().out
    assert "Unknown choice." in out
    assert "No customer has that phone number." in out


# ----- Clerk recording -----


def test_sale_prints_member_total(
    demo: sqlite3.Connection,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Two HDMI cables (2 x $12.99) for active member 1: 10% off is $2.60.
    run(monkeypatch, demo, "1", "6", "15", "1", "2", "", "1", "2", "b", "q")
    assert ["13", "2", "$25.98", "$2.60", "$23.38"] in words(capsys.readouterr().out)
    assert count(demo, "sale") == 13


def test_oversell_prints_error_and_returns_to_menu(
    demo: sqlite3.Connection,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Only 1 Xbox Series X is on hand after the sample sales.
    run(monkeypatch, demo, "1", "6", "11", "1", "2", "", "", "1", "b", "q")
    out = capsys.readouterr().out
    assert "Sale not recorded: CHECK constraint failed" in out
    assert out.count("Clerk menu") == 2
    assert count(demo, "sale") == 12


def test_trade_in_prints_payout(
    demo: sqlite3.Connection,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    run(monkeypatch, demo, "1", "7", "4", "8", "3", "2", "", "b", "q")
    # Two loose copies of Super Mario 64 at $18.00 each.
    assert ["9", "2", "$36.00"] in words(capsys.readouterr().out)


def test_add_customer_then_enroll(
    demo: sqlite3.Connection,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    answers = ("1", "4", "Owen", "Park", "5095550123", "5", "13", "", "b", "q")
    run(monkeypatch, demo, *answers)
    out = capsys.readouterr().out
    assert "Added customer 13." in out
    assert "Enrolled customer 13 for one year." in out
