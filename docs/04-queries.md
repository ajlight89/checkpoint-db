# Queries

This document presents the report queries in SQL, relational algebra, and, for some of them, tuple relational calculus. The functions in `src/checkpoint/queries.py` run the SQL with each value bound to a `?` placeholder. Each result shown here comes from the sample data in `src/checkpoint/sql/demo.sql`, after the triggers have adjusted the stock counts, and `tests/test_queries.py` checks the same rows.

## Notation

The relational algebra follows Elmasri and Navathe, Chapter 8: σ (select), π (project), ⋈ (join, with its condition written as a subscript), and ← (assign a result to a name). Relation names are written in capitals. Relations are sets, so the algebra has no sort order; the SQL's `ORDER BY` only arranges the rows for display. The tuple relational calculus uses the same chapter's form, { t.attribute, … | condition }, where `R(t)` means tuple t belongs to relation R and ∃ means "there exists".

## Q1: In-Stock Games for a Platform

**Question:** Which games are in stock for a given platform, in which conditions, and at what price?

**Concepts:** selection, projection, and joins across three relations. Joining `stock_item` to `game` keeps only games, because consoles and accessories have no `game` row; the console for the same platform is therefore left out. Stock records with no units on hand are left out.

**SQL** (function `in_stock_games(conn, platform_id)`):

```sql
SELECT p.name, s.condition, s.qty_on_hand, s.sell_price_cents
FROM stock_item AS s
JOIN game AS g ON g.product_id = s.product_id
JOIN product AS p ON p.product_id = s.product_id
WHERE g.platform_id = ? AND s.qty_on_hand > 0
ORDER BY p.name, s.condition;
```

**Relational algebra** (platform 2):

```text
PLATFORM_GAMES ← σ platform_id = 2 (GAME)
IN_STOCK       ← σ qty_on_hand > 0 (STOCK_ITEM)
GAME_STOCK     ← IN_STOCK ⋈ IN_STOCK.product_id = PLATFORM_GAMES.product_id PLATFORM_GAMES
RESULT         ← π name, condition, qty_on_hand, sell_price_cents
                   (GAME_STOCK ⋈ GAME_STOCK.product_id = PRODUCT.product_id PRODUCT)
```

Applying both selections before the joins gives the same result as joining first and selecting afterward, and the joins then work on fewer tuples.

**Tuple relational calculus** (platform 2):

```text
{ p.name, s.condition, s.qty_on_hand, s.sell_price_cents |
    STOCK_ITEM(s) AND PRODUCT(p)
    AND p.product_id = s.product_id
    AND s.qty_on_hand > 0
    AND (∃g)(GAME(g) AND g.product_id = s.product_id AND g.platform_id = 2) }
```

The tuple variables s and p are free because the result takes attributes from them. The variable g is bound by ∃: the result needs no attribute of `game`, only the fact that a matching `game` tuple exists.

**Result** (platform 2, PlayStation 5):

| name       | condition     | qty_on_hand | sell_price_cents |
| ---------- | ------------- | ----------: | ---------------: |
| Astro Bot  | new           |           3 |             5999 |
| Elden Ring | new           |           4 |             5999 |
| Elden Ring | used_complete |           4 |             3999 |

Astro Bot started with 4 new copies and sold 1. Elden Ring started with 5 new copies and sold 1, and with 3 used copies and received 1 in a trade-in.
