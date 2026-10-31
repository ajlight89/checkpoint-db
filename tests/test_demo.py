"""Tests for the sample data in demo.sql."""

import sqlite3

import pytest

from checkpoint import db

ROW_COUNTS = {
    "platform": 6,
    "product": 16,
    "game": 8,
    "game_genre": 11,
    "console": 4,
    "accessory": 4,
    "stock_item": 24,
    "customer": 12,
    "loyalty_member": 6,
    "sale": 12,
    "sale_line": 22,
    "trade_in": 8,
    "trade_in_line": 12,
}

# Each case: a stock record and its quantity after the trade-ins and sales.
STOCK_AFTER = [
    pytest.param(1, "new", 3, id="no activity"),
    pytest.param(1, "used_complete", 5, id="4 + 2 traded - 1 sold"),
    pytest.param(2, "used_complete", 4, id="3 + 1 traded"),
    pytest.param(15, "new", 6, id="10 - 4 sold"),
    pytest.param(16, "new", 1, id="4 - 3 sold"),
]


@pytest.fixture
def demo(conn: sqlite3.Connection) -> sqlite3.Connection:
    """The ``conn`` database with the sample rows loaded."""
    db.load_demo(conn)
    return conn


def test_new_database_starts_empty(conn: sqlite3.Connection) -> None:
    for table in ROW_COUNTS:
        assert conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == 0


def test_row_counts(demo: sqlite3.Connection) -> None:
    counts = {
        table: demo.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        for table in ROW_COUNTS
    }
    assert counts == ROW_COUNTS


def test_every_product_has_exactly_one_subclass_row(demo: sqlite3.Connection) -> None:
    # BR-01: each product appears once across game, console, and accessory.
    rows = demo.execute("""
        SELECT p.product_id
        FROM product AS p
        LEFT JOIN (SELECT product_id FROM game
                   UNION ALL SELECT product_id FROM console
                   UNION ALL SELECT product_id FROM accessory) AS sub
            ON sub.product_id = p.product_id
        GROUP BY p.product_id
        HAVING count(sub.product_id) <> 1
    """).fetchall()
    assert rows == []


def test_only_games_before_1994_have_no_rating(demo: sqlite3.Connection) -> None:
    # BR-05
    rows = demo.execute("""
        SELECT p.release_year < 1994, g.esrb_rating IS NULL, count(*)
        FROM game AS g
        JOIN product AS p ON p.product_id = g.product_id
        GROUP BY 1, 2
    """).fetchall()
    assert sorted(rows) == [(0, 0, 7), (1, 1, 1)]


def test_every_sale_and_trade_in_has_a_line(demo: sqlite3.Connection) -> None:
    # BR-18 and BR-24
    empty_sales = demo.execute(
        "SELECT sale_id FROM sale WHERE sale_id NOT IN (SELECT sale_id FROM sale_line)"
    ).fetchall()
    empty_trade_ins = demo.execute(
        "SELECT trade_in_id FROM trade_in"
        " WHERE trade_in_id NOT IN (SELECT trade_in_id FROM trade_in_line)"
    ).fetchall()
    assert empty_sales == []
    assert empty_trade_ins == []


def test_every_customer_is_a_member_or_a_seller(demo: sqlite3.Connection) -> None:
    # BR-13: customers are recorded only when they join or sell to the store.
    rows = demo.execute("""
        SELECT customer_id FROM customer
        WHERE customer_id NOT IN (SELECT customer_id FROM loyalty_member)
          AND customer_id NOT IN (SELECT customer_id FROM trade_in)
    """).fetchall()
    assert rows == []


def test_memberships_last_whole_years(demo: sqlite3.Connection) -> None:
    # BR-16: one year, moved forward one year at each renewal.
    rows = demo.execute("""
        SELECT customer_id FROM loyalty_member
        WHERE expiry_date <> date(join_date,
              '+' || (CAST(substr(expiry_date, 1, 4) AS INTEGER)
                      - CAST(substr(join_date, 1, 4) AS INTEGER)) || ' years')
    """).fetchall()
    assert rows == []


@pytest.mark.parametrize(("product_id", "condition", "expected"), STOCK_AFTER)
def test_triggers_adjusted_the_stock(
    demo: sqlite3.Connection, product_id: int, condition: str, expected: int
) -> None:
    qty = demo.execute(
        "SELECT qty_on_hand FROM stock_item WHERE product_id = ? AND condition = ?",
        (product_id, condition),
    ).fetchone()[0]
    assert qty == expected


def test_low_stock_rows(demo: sqlite3.Connection) -> None:
    rows = demo.execute("SELECT product_id, condition FROM manager_low_stock")
    assert set(rows) == {
        (6, "new"),
        (7, "used_complete"),
        (11, "new"),
        (12, "used_complete"),
        (16, "new"),
    }


def test_discounts_follow_membership_on_the_sale_date(demo: sqlite3.Connection) -> None:
    # BR-21: 10% off each line, rounded half up, only for members active that day.
    rows = demo.execute("""
        SELECT l.quantity * l.unit_price_cents,
               l.discount_amount_cents,
               coalesce(date(s.sale_datetime) >= m.join_date
                        AND date(s.sale_datetime) < m.expiry_date, 0)
        FROM sale_line AS l
        JOIN sale AS s ON s.sale_id = l.sale_id
        LEFT JOIN loyalty_member AS m ON m.customer_id = s.member_id
    """).fetchall()
    for line_cents, discount, active in rows:
        expected = (line_cents * 10 + 50) // 100 if active else 0
        assert discount == expected
    assert any(active for _, _, active in rows)
    assert not all(active for _, _, active in rows)
