"""Tests for the store workflows, run against the sample data."""

import sqlite3

import pytest

from checkpoint import services
from checkpoint.services import StoreError


def count(conn: sqlite3.Connection, table: str) -> int:
    """Return the number of rows in ``table`` (a fixed name, never user input)."""
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


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
