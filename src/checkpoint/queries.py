"""Report queries over the store's data.

Each function runs one query with its values bound to ``?`` placeholders
and returns the result rows as tuples.
"""

import sqlite3


def in_stock_games(conn: sqlite3.Connection, platform_id: int) -> list[tuple]:
    """Return the games in stock for one platform, with condition and price.

    Each row is (name, condition, qty_on_hand, sell_price_cents), sorted by
    name and then condition. Stock records with no units on hand are left out.
    """
    sql = """
        SELECT p.name, s.condition, s.qty_on_hand, s.sell_price_cents
        FROM stock_item AS s
        JOIN game AS g ON g.product_id = s.product_id
        JOIN product AS p ON p.product_id = s.product_id
        WHERE g.platform_id = ? AND s.qty_on_hand > 0
        ORDER BY p.name, s.condition
    """
    return conn.execute(sql, (platform_id,)).fetchall()
