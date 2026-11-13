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
