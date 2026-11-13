"""Tests for the store workflows, run against the sample data."""

import sqlite3

import pytest

from checkpoint import services
from checkpoint.services import StoreError


def count(conn: sqlite3.Connection, table: str) -> int:
    """Return the number of rows in ``table`` (a fixed name, never user input)."""
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def qty(conn: sqlite3.Connection, product_id: int, condition: str) -> int:
    """Return the quantity on hand for one stock record."""
    sql = "SELECT qty_on_hand FROM stock_item WHERE product_id = ? AND condition = ?"
    return conn.execute(sql, (product_id, condition)).fetchone()[0]


# ----- Customers -----


def test_find_customer_shows_member_dates(demo: sqlite3.Connection) -> None:
    row = services.find_customer(demo, "5095550111")
    assert row == (1, "Maya", "Chen", "5095550111", "2023-02-10", "2027-02-10")


def test_find_customer_walk_in_has_no_dates(demo: sqlite3.Connection) -> None:
    row = services.find_customer(demo, "5095550114")
    assert row == (4, "Liam", "Walsh", "5095550114", None, None)


def test_find_customer_unknown_phone(demo: sqlite3.Connection) -> None:
    assert services.find_customer(demo, "5095559999") is None


def test_add_customer_returns_new_id(demo: sqlite3.Connection) -> None:
    assert services.add_customer(demo, "Owen", "Park", "5095550123") == 13
    row = services.find_customer(demo, "5095550123")
    assert row == (13, "Owen", "Park", "5095550123", None, None)


def test_add_customer_refuses_duplicate_phone(demo: sqlite3.Connection) -> None:
    with pytest.raises(StoreError, match="UNIQUE"):
        services.add_customer(demo, "Owen", "Park", "5095550111")
    assert count(demo, "customer") == 12


def test_add_member_lasts_one_year(demo: sqlite3.Connection) -> None:
    services.add_member(demo, 4, "2026-11-13", "liam.walsh@example.com")
    row = demo.execute(
        "SELECT join_date, expiry_date, email FROM loyalty_member WHERE customer_id = 4"
    ).fetchone()
    assert row == ("2026-11-13", "2027-11-13", "liam.walsh@example.com")


def test_add_member_refuses_existing_member(demo: sqlite3.Connection) -> None:
    with pytest.raises(StoreError, match="UNIQUE"):
        services.add_member(demo, 1, "2026-11-13")
    assert count(demo, "loyalty_member") == 6


def test_placeholders_stop_sql_injection(demo: sqlite3.Connection) -> None:
    # Pasted into the SQL text, this phone would make the WHERE clause true
    # for every row. Bound to a placeholder, it is only an unknown phone.
    assert services.find_customer(demo, "' OR '1'='1") is None
    # A name written to end the statement and drop the table is stored as text.
    name = "Robert'); DROP TABLE customer; --"
    customer_id = services.add_customer(demo, name, "Tables", "5095550124")
    stored = demo.execute(
        "SELECT first_name FROM customer WHERE customer_id = ?", (customer_id,)
    ).fetchone()
    assert stored == (name,)
    assert count(demo, "customer") == 13


# ----- Sales -----


def test_record_sale_for_walk_in(demo: sqlite3.Connection) -> None:
    # HDMI cable, new: 10 at the start, 4 sold in the sample sales, so 6 on hand.
    # A used line is charged its selling price, not its trade-in value.
    sale_id = services.record_sale(
        demo, [(15, "new", 2), (5, "used_loose", 1)], "cash", when="2026-11-13 12:00:00"
    )
    assert sale_id == 13
    lines = demo.execute(
        "SELECT * FROM sale_line WHERE sale_id = 13 ORDER BY product_id"
    ).fetchall()
    assert lines == [(13, 5, "used_loose", 1, 3499, 0), (13, 15, "new", 2, 1299, 0)]
    assert qty(demo, 15, "new") == 4


def test_record_sale_gives_active_member_discount(demo: sqlite3.Connection) -> None:
    sale_id = services.record_sale(
        demo,
        [(2, "new", 1), (13, "new", 1)],
        "card",
        member_id=1,
        when="2026-11-13 12:00:00",
    )
    discounts = demo.execute(
        "SELECT discount_amount_cents FROM sale_line WHERE sale_id = ? "
        "ORDER BY product_id",
        (sale_id,),
    ).fetchall()
    assert discounts == [(600,), (700,)]
    total = demo.execute(
        "SELECT total_cents FROM sale_total WHERE sale_id = ?", (sale_id,)
    ).fetchone()
    assert total == (5999 + 6999 - 600 - 700,)


def test_record_sale_discount_follows_membership_dates(
    demo: sqlite3.Connection,
) -> None:
    # BR-17: active from the join date up to, but not including, the expiry date.
    # Member 7 joined on 2026-10-05; member 9 expired on 2026-03-03.
    sales = [
        (7, "2026-10-04 18:00:00"),
        (7, "2026-10-05 09:00:00"),
        (9, "2026-03-02 23:59:59"),
        (9, "2026-03-03 00:00:00"),
    ]
    for member_id, when in sales:
        services.record_sale(demo, [(15, "new", 1)], "cash", member_id, when)
    rows = demo.execute(
        "SELECT s.member_id, l.discount_amount_cents "
        "FROM sale AS s JOIN sale_line AS l ON l.sale_id = s.sale_id "
        "WHERE s.sale_id > 12 ORDER BY s.sale_id"
    ).fetchall()
    assert rows == [(7, 0), (7, 130), (9, 130), (9, 0)]


def test_record_sale_refuses_non_member(demo: sqlite3.Connection) -> None:
    with pytest.raises(StoreError, match="not a loyalty member"):
        services.record_sale(demo, [(15, "new", 1)], "cash", member_id=4)
    assert count(demo, "sale") == 12


def test_record_sale_needs_a_line(demo: sqlite3.Connection) -> None:
    with pytest.raises(StoreError, match="at least one line"):
        services.record_sale(demo, [], "cash")
    assert count(demo, "sale") == 12


def test_record_sale_refuses_unknown_stock_record(demo: sqlite3.Connection) -> None:
    with pytest.raises(StoreError, match="No stock record"):
        services.record_sale(demo, [(15, "new", 1), (3, "used_loose", 1)], "cash")
    assert count(demo, "sale") == 12
    assert qty(demo, 15, "new") == 6


def test_oversell_cancels_the_whole_sale(demo: sqlite3.Connection) -> None:
    # The used PlayStation 5 has 2 on hand. The first line is valid, but the
    # second breaks CHECK (qty_on_hand >= 0), so neither line is kept.
    with pytest.raises(StoreError, match="qty_on_hand"):
        services.record_sale(demo, [(15, "new", 1), (9, "used_complete", 5)], "card")
    assert count(demo, "sale") == 12
    assert count(demo, "sale_line") == 22
    assert qty(demo, 15, "new") == 6
    assert qty(demo, 9, "used_complete") == 2
