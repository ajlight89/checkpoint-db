"""Database connections and transactions."""

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path


def connect(path: str | Path = ":memory:") -> sqlite3.Connection:
    """Open a connection with foreign key enforcement turned on.

    The connection runs in SQLite's autocommit mode: each statement is its
    own transaction unless it runs inside ``transaction()``.
    """
    conn = sqlite3.connect(path, autocommit=True)
    conn.execute("PRAGMA foreign_keys = ON")
    if conn.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
        conn.close()
        raise RuntimeError("This SQLite build cannot enforce foreign keys.")
    return conn


@contextmanager
def transaction(conn: sqlite3.Connection) -> Generator[sqlite3.Connection]:
    """Run a block as one transaction: commit if it succeeds, roll back if not."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
    except BaseException:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise
    conn.execute("COMMIT")
