"""Tests for connections and transactions."""

import sqlite3

import pytest

from checkpoint import db

# Two small tables used only by these tests: a parent and a child that refers to it.
TEST_TABLES = """
    CREATE TABLE parent (
        parent_id   INTEGER PRIMARY KEY,
        name        TEXT    NOT NULL UNIQUE
    ) STRICT;
    CREATE TABLE child (
        child_id    INTEGER PRIMARY KEY,
        parent_id   INTEGER NOT NULL REFERENCES parent (parent_id)
    ) STRICT;
"""


@pytest.fixture
def tables(conn: sqlite3.Connection) -> sqlite3.Connection:
    """The ``conn`` database with the two test tables created."""
    conn.executescript(TEST_TABLES)
    return conn


def test_foreign_keys_are_on(conn: sqlite3.Connection) -> None:
    assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1


def test_foreign_key_violation_is_rejected(tables: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
        tables.execute("INSERT INTO child VALUES (1, 99)")


def test_transaction_commits_on_success(tables: sqlite3.Connection) -> None:
    with db.transaction(tables):
        tables.execute("INSERT INTO parent VALUES (1, 'Sega')")
    assert tables.execute("SELECT count(*) FROM parent").fetchone()[0] == 1


def test_transaction_rolls_back_on_error(tables: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError), db.transaction(tables):
        tables.execute("INSERT INTO parent VALUES (1, 'Sega')")
        tables.execute("INSERT INTO parent VALUES (2, 'Sega')")
    assert tables.execute("SELECT count(*) FROM parent").fetchone()[0] == 0
    assert not tables.in_transaction
