"""Shared pytest fixtures."""

import sqlite3
from collections.abc import Iterator

import pytest

from checkpoint import db

# A few valid rows that tests build on: one game with new and used stock,
# one customer, one sale, and one trade-in.
BASE_ROWS = """
    INSERT INTO platform VALUES (1, 'PlayStation 4', 'Sony', 2013);
    INSERT INTO product VALUES (1, 'Bloodborne', 'Sony', 2015, 'game');
    INSERT INTO game VALUES (1, 'M', 1);
    INSERT INTO stock_item VALUES (1, 'new', 2, 1999, NULL, 1);
    INSERT INTO stock_item VALUES (1, 'used_loose', 3, 999, 400, 1);
    INSERT INTO customer VALUES (1, 'Ada', 'Lovelace', '5095550101');
    INSERT INTO sale VALUES (1, '2026-11-09 14:30:00', NULL, 'cash');
    INSERT INTO trade_in VALUES (1, '2026-11-09 15:00:00', 1);
"""


@pytest.fixture
def conn() -> Iterator[sqlite3.Connection]:
    """A new in-memory database with the Checkpoint-DB tables."""
    connection = db.connect()
    db.initialize(connection)
    yield connection
    connection.close()


@pytest.fixture
def base(conn: sqlite3.Connection) -> sqlite3.Connection:
    """The ``conn`` database with the base rows inserted."""
    conn.executescript(BASE_ROWS)
    return conn


@pytest.fixture
def demo(conn: sqlite3.Connection) -> sqlite3.Connection:
    """The ``conn`` database with the sample rows loaded."""
    db.load_demo(conn)
    return conn
