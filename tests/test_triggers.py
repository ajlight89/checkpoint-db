"""Tests for the triggers in triggers.sql."""

import sqlite3

import pytest

# Each case: a product type, and a subclass row that does not match it.
MISMATCHED = [
    pytest.param("console", "INSERT INTO game VALUES (2, 'E', 1)", id="game row"),
    pytest.param(
        "accessory",
        "INSERT INTO console VALUES (2, 'CUH-2215B', 500, 1)",
        id="console row",
    ),
    pytest.param(
        "game", "INSERT INTO accessory VALUES (2, 'controller')", id="accessory row"
    ),
]


def qty_on_hand(conn: sqlite3.Connection, condition: str) -> int:
    """The quantity on hand of the base game in one condition."""
    sql = "SELECT qty_on_hand FROM stock_item WHERE product_id = 1 AND condition = ?"
    return conn.execute(sql, (condition,)).fetchone()[0]


def test_matching_subclass_row_is_accepted(base: sqlite3.Connection) -> None:
    base.execute("INSERT INTO product VALUES (2, 'PS4 Slim', 'Sony', 2016, 'console')")
    base.execute("INSERT INTO console VALUES (2, 'CUH-2215B', 500, 1)")
    assert base.execute("SELECT count(*) FROM console").fetchone()[0] == 1


@pytest.mark.parametrize(("product_type", "sql"), MISMATCHED)
def test_mismatched_subclass_row_is_rejected(
    base: sqlite3.Connection, product_type: str, sql: str
) -> None:
    base.execute(
        "INSERT INTO product VALUES (2, 'Test item', 'Sony', 2016, ?)", (product_type,)
    )
    with pytest.raises(sqlite3.IntegrityError, match="product_type must be"):
        base.execute(sql)


def test_sale_line_lowers_stock(base: sqlite3.Connection) -> None:
    base.execute("INSERT INTO sale_line VALUES (1, 1, 'used_loose', 2, 999, 0)")
    assert qty_on_hand(base, "used_loose") == 1


def test_overselling_is_rejected_and_nothing_changes(base: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError, match="qty_on_hand >= 0"):
        base.execute("INSERT INTO sale_line VALUES (1, 1, 'used_loose', 4, 999, 0)")
    assert qty_on_hand(base, "used_loose") == 3
    assert base.execute("SELECT count(*) FROM sale_line").fetchone()[0] == 0


def test_trade_in_line_raises_stock(base: sqlite3.Connection) -> None:
    base.execute("INSERT INTO trade_in_line VALUES (1, 1, 'used_loose', 2, 400)")
    assert qty_on_hand(base, "used_loose") == 5
