"""Smoke tests: confirm the package imports and the environment is correct."""

import sqlite3

import checkpoint


def test_package_has_version() -> None:
    assert checkpoint.__version__ == "0.1.0"


def test_sqlite_supports_strict_tables() -> None:
    # STRICT tables need SQLite 3.37.0 or later, the oldest version supported.
    assert sqlite3.sqlite_version_info >= (3, 37, 0)
