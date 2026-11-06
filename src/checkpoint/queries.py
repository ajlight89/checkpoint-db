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


def purchases_per_member(conn: sqlite3.Connection, start: str, end: str) -> list[tuple]:
    """Return how many purchases each loyalty member made in a period.

    The period runs from ``start`` up to but not including ``end``, both
    written as 'YYYY-MM-DD'. Each row is (customer_id, first_name, last_name,
    purchases), sorted by customer_id. Members with no purchases in the
    period are included with a count of 0.
    """
    # The period test sits in the ON clause. In WHERE, it would remove the
    # rows the LEFT JOIN keeps for members with no sales.
    sql = """
        SELECT m.customer_id, c.first_name, c.last_name, COUNT(s.sale_id)
        FROM loyalty_member AS m
        JOIN customer AS c ON c.customer_id = m.customer_id
        LEFT JOIN sale AS s
            ON s.member_id = m.customer_id
            AND s.sale_datetime >= ?
            AND s.sale_datetime < ?
        GROUP BY m.customer_id, c.first_name, c.last_name
        ORDER BY m.customer_id
    """
    return conn.execute(sql, (start, end)).fetchall()


def platforms_with_game_sales(
    conn: sqlite3.Connection, start: str, end: str, min_units: int
) -> list[tuple]:
    """Return the platforms that sold at least ``min_units`` games in a period.

    The period runs from ``start`` up to but not including ``end``, both
    written as 'YYYY-MM-DD'. Each row is (platform_name, units), sorted by
    units from most to fewest and then by name. Only game units count.
    """
    # WHERE picks the sale lines before grouping; HAVING picks the groups after.
    sql = """
        SELECT pl.platform_name, SUM(sl.quantity) AS units
        FROM sale_line AS sl
        JOIN sale AS s ON s.sale_id = sl.sale_id
        JOIN game AS g ON g.product_id = sl.product_id
        JOIN platform AS pl ON pl.platform_id = g.platform_id
        WHERE s.sale_datetime >= ? AND s.sale_datetime < ?
        GROUP BY pl.platform_id, pl.platform_name
        HAVING SUM(sl.quantity) >= ?
        ORDER BY units DESC, pl.platform_name
    """
    return conn.execute(sql, (start, end, min_units)).fetchall()
