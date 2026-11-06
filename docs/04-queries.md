# Queries

This document presents the report queries in SQL, relational algebra, and, for some of them, tuple relational calculus. The functions in `src/checkpoint/queries.py` run the SQL with each value bound to a `?` placeholder. Each result shown here comes from the sample data in `src/checkpoint/sql/demo.sql`, after the triggers have adjusted the stock counts, and `tests/test_queries.py` checks the same rows.

## Notation

The relational algebra follows Elmasri and Navathe, Chapter 8: σ (select), π (project), ⋈ (join, with its condition written as a subscript), ⟕ (left outer join), ℑ (aggregate function, with the grouping attributes on its left), and ← (assign a result to a name). Relation names are written in capitals. Relations are sets, so the algebra has no sort order; the SQL's `ORDER BY` only arranges the rows for display. The tuple relational calculus uses the same chapter's form, { t.attribute, … | condition }, where `R(t)` means tuple t belongs to relation R and ∃ means "there exists".

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

## Q2: Purchases per Member in a Period

**Question:** How many purchases did each loyalty member make in a given period, including members who made none?

**Concepts:** left outer join, COUNT, and GROUP BY. An inner join keeps only members with a matching sale, so members with no purchases would disappear. A left join keeps every member and fills the sale columns with NULL when no sale matches. `COUNT(s.sale_id)` counts only non-NULL values, so those members get 0; `COUNT(*)` would count the NULL-filled row and report 1.

The period test belongs in the join's `ON` clause. In `WHERE`, it would run after the join, the NULL `sale_datetime` of a member with no sales would fail it, and that member's row would be removed: the left join would act like an inner join. The period runs from the start date up to but not including the end date, so consecutive periods never count a sale twice.

**SQL** (function `purchases_per_member(conn, start, end)`):

```sql
SELECT m.customer_id, c.first_name, c.last_name, COUNT(s.sale_id)
FROM loyalty_member AS m
JOIN customer AS c ON c.customer_id = m.customer_id
LEFT JOIN sale AS s
    ON s.member_id = m.customer_id
    AND s.sale_datetime >= ?
    AND s.sale_datetime < ?
GROUP BY m.customer_id, c.first_name, c.last_name
ORDER BY m.customer_id;
```

**Relational algebra** (November 2026):

```text
PERIOD_SALES ← σ sale_datetime ≥ '2026-11-01' AND sale_datetime < '2026-12-01' (SALE)
MEMBERS      ← LOYALTY_MEMBER ⋈ LOYALTY_MEMBER.customer_id = CUSTOMER.customer_id CUSTOMER
MEMBER_SALES ← MEMBERS ⟕ MEMBERS.customer_id = PERIOD_SALES.member_id PERIOD_SALES
RESULT       ← customer_id, first_name, last_name ℑ COUNT sale_id (MEMBER_SALES)
```

The selection is applied to SALE before the outer join, which matches placing the period test in the `ON` clause. Basic tuple relational calculus has no aggregate functions, so this query has no calculus form.

**Result** (November 2026):

| customer_id | first_name | last_name | purchases |
| ----------: | ---------- | --------- | --------: |
|           1 | Maya       | Chen      |         1 |
|           2 | Jordan     | Reyes     |         1 |
|           3 | Priya      | Patel     |         0 |
|           5 | Sofia      | Rossi     |         0 |
|           7 | Hannah     | Kim       |         0 |
|           9 | Grace      | Okafor    |         1 |

Members 5 and 9 have expired memberships but are still listed, because the query counts purchases by every member on record.

## Q3: Platforms with at Least N Game Units Sold in a Period

**Question:** Which platforms sold at least a given number of game units in a given period?

**Concepts:** GROUP BY with HAVING, and SUM. `WHERE` filters rows before they are grouped, so it selects the sale lines in the period. `HAVING` filters groups after the aggregate is computed, so it compares each platform's total with the minimum. An aggregate cannot appear in `WHERE`, because no groups exist yet when `WHERE` runs. The total is `SUM(sl.quantity)`, not `COUNT(*)`: one sale line can carry several units. Joining to `game` leaves out console sales, even though consoles also belong to a platform.

**SQL** (function `platforms_with_game_sales(conn, start, end, min_units)`):

```sql
SELECT pl.platform_name, SUM(sl.quantity) AS units
FROM sale_line AS sl
JOIN sale AS s ON s.sale_id = sl.sale_id
JOIN game AS g ON g.product_id = sl.product_id
JOIN platform AS pl ON pl.platform_id = g.platform_id
WHERE s.sale_datetime >= ? AND s.sale_datetime < ?
GROUP BY pl.platform_id, pl.platform_name
HAVING SUM(sl.quantity) >= ?
ORDER BY units DESC, pl.platform_name;
```

**Relational algebra** (November 2026, at least 2 units):

```text
PERIOD_SALES  ← σ sale_datetime ≥ '2026-11-01' AND sale_datetime < '2026-12-01' (SALE)
PERIOD_LINES  ← SALE_LINE ⋈ SALE_LINE.sale_id = PERIOD_SALES.sale_id PERIOD_SALES
GAME_LINES    ← PERIOD_LINES ⋈ PERIOD_LINES.product_id = GAME.product_id GAME
WITH_PLATFORM ← GAME_LINES ⋈ GAME_LINES.platform_id = PLATFORM.platform_id PLATFORM
UNITS(platform_id, platform_name, units)
              ← platform_id, platform_name ℑ SUM quantity (WITH_PLATFORM)
RESULT        ← π platform_name, units (σ units ≥ 2 (UNITS))
```

The selection on SALE corresponds to `WHERE`, and the selection on UNITS, applied after the aggregate function, corresponds to `HAVING`. Listing attribute names on the left of ← renames the attributes of the result. The query has no calculus form, for the same reason as Q2.

**Result** (November 2026, at least 2 units):

| platform_name   | units |
| --------------- | ----: |
| Nintendo 64     |     2 |
| Nintendo Switch |     2 |

Super Nintendo and Xbox Series X|S each sold 1 game in November and fall below the minimum. Nintendo 64's 2 units come from a single sale line with a quantity of 2.

## Q4: Used Games Priced Above Their Condition's Average

**Question:** Which used games are priced above the average price of used games in the same condition?

**Concepts:** correlated subquery and AVG. The subquery refers to `s.condition`, a column of the outer query, so it is evaluated for each outer row and returns the average for that row's condition. An uncorrelated subquery would return one value for every row. The subquery joins to `game`, so the averages include only games; used consoles cost far more and would raise the averages. The comparison is a strict `>`, so a price equal to the average is not above it.

In the sample data, each platform has at most one used stock record per condition, so an average per platform and condition would equal each record's own price and no row would qualify. The query therefore compares each record with all used games in the same condition.

**SQL** (function `used_games_above_average(conn)`):

```sql
SELECT p.name, pl.platform_name, s.condition, s.sell_price_cents
FROM stock_item AS s
JOIN game AS g ON g.product_id = s.product_id
JOIN product AS p ON p.product_id = s.product_id
JOIN platform AS pl ON pl.platform_id = g.platform_id
WHERE s.condition <> 'new'
    AND s.sell_price_cents > (
        SELECT AVG(s2.sell_price_cents)
        FROM stock_item AS s2
        JOIN game AS g2 ON g2.product_id = s2.product_id
        WHERE s2.condition = s.condition
    )
ORDER BY s.condition, s.sell_price_cents DESC, p.name;
```

**Relational algebra:**

```text
USED_GAMES ← σ condition ≠ 'new' (STOCK_ITEM ⋈ STOCK_ITEM.product_id = GAME.product_id GAME)
AVERAGES(avg_condition, avg_price)
           ← condition ℑ AVERAGE sell_price_cents (USED_GAMES)
ABOVE      ← σ sell_price_cents > avg_price
               (USED_GAMES ⋈ USED_GAMES.condition = AVERAGES.avg_condition AVERAGES)
NAMED      ← ABOVE ⋈ ABOVE.product_id = PRODUCT.product_id PRODUCT
RESULT     ← π name, platform_name, condition, sell_price_cents
               (NAMED ⋈ NAMED.platform_id = PLATFORM.platform_id PLATFORM)
```

Relational algebra has no subqueries. The equivalent computes every condition's average once with the aggregate function, joins each used game to the average for its condition, and selects the games priced above it. The query has no calculus form, for the same reason as Q2.

**Result:**

| name                                    | platform_name   | condition     | sell_price_cents |
| --------------------------------------- | --------------- | ------------- | ---------------: |
| Super Mario World                       | Super Nintendo  | used_complete |             6999 |
| Elden Ring                              | PlayStation 5   | used_complete |             3999 |
| The Legend of Zelda: Breath of the Wild | Nintendo Switch | used_complete |             3999 |
| Super Mario 64                          | Nintendo 64     | used_loose    |             3999 |

The averages are 3659 cents for the five used_complete records and 3499 cents for the three used_loose records. Mario Kart 8 Deluxe in used_loose condition costs exactly 3499 cents, so it is not listed.
