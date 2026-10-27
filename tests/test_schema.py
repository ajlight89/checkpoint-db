"""Tests for the tables, keys, and CHECK constraints in schema.sql."""

import sqlite3

import pytest

TABLES = {
    "platform",
    "product",
    "game",
    "game_genre",
    "console",
    "accessory",
    "stock_item",
    "customer",
    "loyalty_member",
    "sale",
    "sale_line",
    "trade_in",
    "trade_in_line",
}


# Each case: a statement that breaks one rule, starting from the base rows in
# conftest.py, and part of the expected error.
REJECTED = [
    pytest.param(
        "INSERT INTO product VALUES (2, 'Plush toy', 'Nintendo', 2020, 'toy')",
        "CHECK",
        id="BR-01 product type",
    ),
    pytest.param(
        "UPDATE stock_item SET trade_value_cents = 500 WHERE condition = 'new'",
        "CHECK",
        id="BR-11 new with trade value",
    ),
    pytest.param(
        "UPDATE stock_item SET trade_value_cents = NULL WHERE condition = 'used_loose'",
        "CHECK",
        id="BR-11 used without trade value",
    ),
    pytest.param(
        "UPDATE stock_item SET qty_on_hand = -1",
        "CHECK",
        id="BR-12 negative stock",
    ),
    pytest.param(
        "INSERT INTO customer VALUES (2, 'Alan', 'Turing', '5095550101')",
        "UNIQUE",
        id="BR-14 duplicate phone",
    ),
    pytest.param(
        "INSERT INTO loyalty_member VALUES (1, '2026-11-09', '2026-11-09', NULL)",
        "CHECK",
        id="BR-16 expiry not after join",
    ),
    pytest.param(
        "INSERT INTO sale_line VALUES (1, 1, 'new', 1, 1999, 2000)",
        "CHECK",
        id="BR-21 discount over line total",
    ),
    pytest.param(
        "INSERT INTO trade_in_line VALUES (1, 1, 'new', 1, 500)",
        "CHECK",
        id="BR-25 new item traded in",
    ),
    pytest.param(
        "INSERT INTO sale_line VALUES (1, 1, 'used_complete', 1, 1499, 0)",
        "FOREIGN KEY",
        id="missing stock record",
    ),
    pytest.param(
        "UPDATE stock_item SET qty_on_hand = 'two'",
        "cannot store TEXT value in INTEGER column",
        id="STRICT column type",
    ),
]


def test_all_tables_exist(conn: sqlite3.Connection) -> None:
    rows = conn.execute("SELECT name FROM sqlite_schema WHERE type = 'table'")
    assert {name for (name,) in rows} == TABLES


def test_all_tables_are_strict(conn: sqlite3.Connection) -> None:
    rows = conn.execute("SELECT name FROM pragma_table_list WHERE strict = 1")
    assert {name for (name,) in rows} == TABLES


def test_base_rows_are_accepted(base: sqlite3.Connection) -> None:
    assert base.execute("SELECT count(*) FROM stock_item").fetchone()[0] == 2


@pytest.mark.parametrize(("sql", "message"), REJECTED)
def test_rule_breaking_row_is_rejected(
    base: sqlite3.Connection, sql: str, message: str
) -> None:
    with pytest.raises(sqlite3.IntegrityError, match=message):
        base.execute(sql)
