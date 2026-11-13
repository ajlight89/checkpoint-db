"""Store workflows.

These functions hold the application's rules. They never ask questions or
print, so the command-line menu and the tests call them the same way. Every
value reaches SQLite through a ``?`` placeholder.
"""

import sqlite3
from datetime import date, datetime

from checkpoint import db
from checkpoint.money import member_discount

# One line of a sale or trade-in: (product_id, condition, quantity).
Line = tuple[int, str, int]


class StoreError(Exception):
    """A request the store refuses. The message can be shown to the user."""


def _now() -> str:
    """Return the current local time as 'YYYY-MM-DD HH:MM:SS'."""
    return datetime.now().isoformat(sep=" ", timespec="seconds")


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


# ----- Sales -----


def _is_active_member(conn: sqlite3.Connection, customer_id: int, on_date: str) -> bool:
    """Return whether a loyalty member is active on ``on_date`` (BR-17).

    Raises StoreError if the customer is not a loyalty member.
    """
    sql = "SELECT join_date, expiry_date FROM loyalty_member WHERE customer_id = ?"
    row = conn.execute(sql, (customer_id,)).fetchone()
    if row is None:
        raise StoreError(f"Customer {customer_id} is not a loyalty member.")
    join_date, expiry_date = row
    return join_date <= on_date < expiry_date


def record_sale(
    conn: sqlite3.Connection,
    lines: list[Line],
    payment_method: str,
    member_id: int | None = None,
    when: str | None = None,
) -> int:
    """Record a sale and its lines in one transaction and return the sale_id.

    Each line is charged the stock record's current selling price (BR-19).
    An active member gets 10% off every line (BR-21); an expired member's
    sale is still linked to the member but gets no discount. If any line
    fails, such as one selling more than is on hand, nothing is recorded.
    """
    if not lines:
        raise StoreError("A sale needs at least one line.")  # BR-18
    when = when or _now()
    price_sql = """
        SELECT sell_price_cents FROM stock_item
        WHERE product_id = ? AND condition = ?
    """
    try:
        with db.transaction(conn):
            discounted = member_id is not None and _is_active_member(
                conn, member_id, when[:10]
            )
            cursor = conn.execute(
                "INSERT INTO sale (sale_datetime, member_id, payment_method) "
                "VALUES (?, ?, ?)",
                (when, member_id, payment_method),
            )
            sale_id = cursor.lastrowid
            for product_id, condition, quantity in lines:
                row = conn.execute(price_sql, (product_id, condition)).fetchone()
                if row is None:
                    raise StoreError(
                        f"No stock record for product {product_id} ({condition})."
                    )
                price = row[0]
                discount = member_discount(quantity * price) if discounted else 0
                conn.execute(
                    "INSERT INTO sale_line VALUES (?, ?, ?, ?, ?, ?)",
                    (sale_id, product_id, condition, quantity, price, discount),
                )
    except sqlite3.IntegrityError as err:
        raise StoreError(f"Sale not recorded: {err}.") from err
    return sale_id
