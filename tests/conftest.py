"""Shared pytest fixtures."""

import sqlite3
from collections.abc import Iterator

import pytest

from checkpoint import db


@pytest.fixture
def conn() -> Iterator[sqlite3.Connection]:
    """A new, empty in-memory database."""
    connection = db.connect()
    yield connection
    connection.close()
