"""Store workflows.

These functions hold the application's rules. They never ask questions or
print, so the command-line menu and the tests call them the same way. Every
value reaches SQLite through a ``?`` placeholder.
"""

import sqlite3
from datetime import date


class StoreError(Exception):
    """A request the store refuses. The message can be shown to the user."""


# ----- Customers -----


def find_customer(conn: sqlite3.Connection, phone: str) -> tuple | None:
    """Return the customer with this phone number, or None if there is none.

    The row is (customer_id, first_name, last_name, phone, join_date,
    expiry_date). The two dates are None for a walk-in seller.
    """
    sql = """
        SELECT c.customer_id, c.first_name, c.last_name, c.phone,
               m.join_date, m.expiry_date
        FROM customer AS c
        LEFT JOIN loyalty_member AS m ON m.customer_id = c.customer_id
        WHERE c.phone = ?
    """
    return conn.execute(sql, (phone,)).fetchone()


def add_customer(
    conn: sqlite3.Connection, first_name: str, last_name: str, phone: str
) -> int:
    """Add a customer and return the new customer_id."""
    sql = "INSERT INTO customer (first_name, last_name, phone) VALUES (?, ?, ?)"
    try:
        cursor = conn.execute(sql, (first_name, last_name, phone))
    except sqlite3.IntegrityError as err:
        raise StoreError(f"Customer not added: {err}.") from err
    return cursor.lastrowid


def add_member(
    conn: sqlite3.Connection,
    customer_id: int,
    join_date: str | None = None,
    email: str | None = None,
) -> None:
    """Enroll an existing customer in the loyalty program for one year (BR-16).

    ``join_date`` is written as 'YYYY-MM-DD' and defaults to today.
    """
    sql = """
        INSERT INTO loyalty_member (customer_id, join_date, expiry_date, email)
        VALUES (?, ?, date(?, '+1 year'), ?)
    """
    join_date = join_date or date.today().isoformat()
    try:
        conn.execute(sql, (customer_id, join_date, join_date, email))
    except sqlite3.IntegrityError as err:
        raise StoreError(f"Member not added: {err}.") from err
