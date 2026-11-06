"""Tests for the report queries, run against the sample data."""

import sqlite3

from checkpoint import queries


def test_in_stock_games_for_one_platform(demo: sqlite3.Connection) -> None:
    # Platform 2 is the PlayStation 5. Quantities include the trigger changes:
    # Astro Bot new 4 - 1 sold, Elden Ring new 5 - 1 sold, used 3 + 1 traded.
    # The PlayStation 5 console is also on platform 2 but is not a game.
    assert queries.in_stock_games(demo, 2) == [
        ("Astro Bot", "new", 3, 5999),
        ("Elden Ring", "new", 4, 5999),
        ("Elden Ring", "used_complete", 4, 3999),
    ]


def test_in_stock_games_leaves_out_sold_out_stock(demo: sqlite3.Connection) -> None:
    demo.execute(
        "UPDATE stock_item SET qty_on_hand = 0 "
        "WHERE product_id = 2 AND condition = 'new'"
    )
    assert queries.in_stock_games(demo, 2) == [
        ("Astro Bot", "new", 3, 5999),
        ("Elden Ring", "used_complete", 4, 3999),
    ]
