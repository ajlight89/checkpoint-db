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


def test_purchases_per_member_includes_members_with_none(
    demo: sqlite3.Connection,
) -> None:
    # November sales by members: sale 9 (member 2), 11 (member 1), 12 (member 9).
    assert queries.purchases_per_member(demo, "2026-11-01", "2026-12-01") == [
        (1, "Maya", "Chen", 1),
        (2, "Jordan", "Reyes", 1),
        (3, "Priya", "Patel", 0),
        (5, "Sofia", "Rossi", 0),
        (7, "Hannah", "Kim", 0),
        (9, "Grace", "Okafor", 1),
    ]


def test_purchases_per_member_counts_every_sale(demo: sqlite3.Connection) -> None:
    # October and November together: member 1 made sales 2 and 11.
    assert queries.purchases_per_member(demo, "2026-10-01", "2026-12-01") == [
        (1, "Maya", "Chen", 2),
        (2, "Jordan", "Reyes", 1),
        (3, "Priya", "Patel", 1),
        (5, "Sofia", "Rossi", 1),
        (7, "Hannah", "Kim", 1),
        (9, "Grace", "Okafor", 1),
    ]


def test_platforms_with_game_sales_in_november(demo: sqlite3.Connection) -> None:
    # November game units: Nintendo 64 2 (one line of 2), Nintendo Switch 2,
    # Super Nintendo 1, Xbox Series X|S 1. Console sales do not count.
    assert queries.platforms_with_game_sales(demo, "2026-11-01", "2026-12-01", 2) == [
        ("Nintendo 64", 2),
        ("Nintendo Switch", 2),
    ]


def test_platforms_with_game_sales_over_both_months(demo: sqlite3.Connection) -> None:
    # PlayStation 4 and Xbox Series X|S sold 1 game each, below the minimum.
    assert queries.platforms_with_game_sales(demo, "2026-10-01", "2026-12-01", 2) == [
        ("Nintendo Switch", 3),
        ("Nintendo 64", 2),
        ("PlayStation 5", 2),
        ("Super Nintendo", 2),
    ]


def test_used_games_above_average(demo: sqlite3.Connection) -> None:
    # Averages over used games only: used_complete 3659 (5 records),
    # used_loose 3499 (3 records). Mario Kart 8 Deluxe used_loose is priced
    # exactly at its average, so it is not above it.
    assert queries.used_games_above_average(demo) == [
        ("Super Mario World", "Super Nintendo", "used_complete", 6999),
        ("Elden Ring", "PlayStation 5", "used_complete", 3999),
        (
            "The Legend of Zelda: Breath of the Wild",
            "Nintendo Switch",
            "used_complete",
            3999,
        ),
        ("Super Mario 64", "Nintendo 64", "used_loose", 3999),
    ]


def test_used_games_above_average_per_condition(demo: sqlite3.Connection) -> None:
    # Raising one used_complete price lifts only the used_complete average.
    # Super Mario 64 stays above the used_loose average of 3499.
    demo.execute(
        "UPDATE stock_item SET sell_price_cents = 69999 "
        "WHERE product_id = 7 AND condition = 'used_complete'"
    )
    assert queries.used_games_above_average(demo) == [
        ("Super Mario World", "Super Nintendo", "used_complete", 69999),
        ("Super Mario 64", "Nintendo 64", "used_loose", 3999),
    ]
