"""Shared pytest fixtures."""

import sqlite3
from collections.abc import Iterator

import pytest

from checkpoint import db


@pytest.fixture
def conn() -> Iterator[sqlite3.Connection]:
    """A new in-memory database with the Checkpoint-DB tables."""
    connection = db.connect()
    db.initialize(connection)
    yield connection
    connection.close()
