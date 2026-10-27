"""Tests for the views in views.sql."""

import sqlite3
from datetime import date, timedelta

import pytest

VIEWS = {
    "member_status",
    "sale_total",
    "trade_in_total",
    "clerk_stock",
    "manager_low_stock",
    "analyst_sale_lines",
}

# Each case: days from today to the join date and to the expiry date, and
# whether the member is active today (BR-17).
MEMBERSHIPS = [
    pytest.param(-730, -365, 0, id="expired"),
    pytest.param(-365, 0, 0, id="expires today"),
    pytest.param(0, 365, 1, id="joined today"),
    pytest.param(1, 366, 0, id="not started"),
]


def test_all_views_exist(conn: sqlite3.Connection) -> None:
    rows = conn.execute("SELECT name FROM sqlite_schema WHERE type = 'view'")
    assert {name for (name,) in rows} == VIEWS


@pytest.mark.parametrize(("join_days", "expiry_days", "expected"), MEMBERSHIPS)
def test_member_status_is_active(
    base: sqlite3.Connection, join_days: int, expiry_days: int, expected: int
) -> None:
    today = date.today()
    join_date = (today + timedelta(days=join_days)).isoformat()
    expiry_date = (today + timedelta(days=expiry_days)).isoformat()
    base.execute(
        "INSERT INTO loyalty_member VALUES (1, ?, ?, NULL)", (join_date, expiry_date)
    )
    assert base.execute("SELECT is_active FROM member_status").fetchone()[0] == expected


def test_sale_total_adds_up_the_lines(base: sqlite3.Connection) -> None:
    base.execute("INSERT INTO sale_line VALUES (1, 1, 'new', 1, 1999, 200)")
    base.execute("INSERT INTO sale_line VALUES (1, 1, 'used_loose', 2, 999, 0)")
    row = base.execute(
        "SELECT item_count, subtotal_cents, discount_cents, total_cents FROM sale_total"
    ).fetchone()
    assert row == (3, 3997, 200, 3797)


def test_trade_in_total_adds_up_the_lines(base: sqlite3.Connection) -> None:
    base.execute("INSERT INTO trade_in_line VALUES (1, 1, 'used_loose', 2, 400)")
    row = base.execute("SELECT item_count, payout_cents FROM trade_in_total").fetchone()
    assert row == (2, 800)


def test_clerk_stock_shows_platforms(base: sqlite3.Connection) -> None:
    base.execute(
        "INSERT INTO product VALUES (2, 'Controller', 'Sony', 2013, 'accessory')"
    )
    base.execute("INSERT INTO accessory VALUES (2, 'controller')")
    base.execute("INSERT INTO stock_item VALUES (2, 'new', 5, 5999, NULL, 2)")
    rows = base.execute(
        "SELECT name, platform_name, condition FROM clerk_stock ORDER BY name, condition"
    ).fetchall()
    assert rows == [
        ("Bloodborne", "PlayStation 4", "new"),
        ("Bloodborne", "PlayStation 4", "used_loose"),
        ("Controller", None, "new"),
    ]


def test_manager_low_stock_lists_items_at_threshold(base: sqlite3.Connection) -> None:
    low = "SELECT condition, qty_on_hand FROM manager_low_stock"
    assert base.execute(low).fetchall() == []
    base.execute("INSERT INTO sale_line VALUES (1, 1, 'used_loose', 2, 999, 0)")
    assert base.execute(low).fetchall() == [("used_loose", 1)]


def test_analyst_sale_lines_has_no_customer_details(base: sqlite3.Connection) -> None:
    base.execute("INSERT INTO sale_line VALUES (1, 1, 'new', 1, 1999, 0)")
    cursor = base.execute("SELECT * FROM analyst_sale_lines")
    columns = {column[0] for column in cursor.description}
    assert cursor.fetchall()
    assert not columns & {"customer_id", "first_name", "last_name", "phone", "email"}
