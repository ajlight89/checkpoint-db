-- Checkpoint-DB views.
-- BR-nn refers to a business rule in docs/01-requirements.md.

-- Derived values: computed when read, never stored.

-- BR-17: a member is active from join_date up to, but not including, expiry_date.
CREATE VIEW member_status AS
SELECT c.customer_id,
       c.first_name,
       c.last_name,
       c.phone,
       m.email,
       m.join_date,
       m.expiry_date,
       date('now', 'localtime') >= m.join_date
           AND date('now', 'localtime') < m.expiry_date AS is_active
FROM loyalty_member AS m
JOIN customer AS c ON c.customer_id = m.customer_id;

-- A sale's totals, from its lines (BR-18, BR-21).
CREATE VIEW sale_total AS
SELECT s.sale_id,
       s.sale_datetime,
       s.member_id,
       s.payment_method,
       sum(l.quantity) AS item_count,
       sum(l.quantity * l.unit_price_cents) AS subtotal_cents,
       sum(l.discount_amount_cents) AS discount_cents,
       sum(l.quantity * l.unit_price_cents - l.discount_amount_cents) AS total_cents
FROM sale AS s
JOIN sale_line AS l ON l.sale_id = s.sale_id
GROUP BY s.sale_id, s.sale_datetime, s.member_id, s.payment_method;

-- A trade-in's cash payout, from its lines (BR-24, BR-26).
CREATE VIEW trade_in_total AS
SELECT t.trade_in_id,
       t.trade_datetime,
       t.customer_id,
       sum(l.quantity) AS item_count,
       sum(l.quantity * l.unit_value_cents) AS payout_cents
FROM trade_in AS t
JOIN trade_in_line AS l ON l.trade_in_id = t.trade_in_id
GROUP BY t.trade_in_id, t.trade_datetime, t.customer_id;

-- Role views (BR-27).

-- Clerks: every stock record with its product and platform.
-- Accessories have no platform, so platform_name is NULL for them.
CREATE VIEW clerk_stock AS
SELECT p.product_id,
       p.name,
       p.product_type,
       pl.platform_name,
       s.condition,
       s.qty_on_hand,
       s.sell_price_cents,
       s.trade_value_cents
FROM stock_item AS s
JOIN product AS p ON p.product_id = s.product_id
LEFT JOIN game AS g ON g.product_id = p.product_id
LEFT JOIN console AS c ON c.product_id = p.product_id
LEFT JOIN platform AS pl ON pl.platform_id = coalesce(g.platform_id, c.platform_id);

-- Managers: stock records at or below their reorder threshold (BR-10).
CREATE VIEW manager_low_stock AS
SELECT p.product_id,
       p.name,
       s.condition,
       s.qty_on_hand,
       s.reorder_threshold
FROM stock_item AS s
JOIN product AS p ON p.product_id = s.product_id
WHERE s.qty_on_hand <= s.reorder_threshold;

-- Analysts: sale lines with no customer names or contact details.
CREATE VIEW analyst_sale_lines AS
SELECT s.sale_id,
       s.sale_datetime,
       s.member_id IS NOT NULL AS member_sale,
       s.payment_method,
       p.product_id,
       p.name,
       p.product_type,
       l.condition,
       l.quantity,
       l.unit_price_cents,
       l.discount_amount_cents,
       l.quantity * l.unit_price_cents - l.discount_amount_cents AS line_total_cents
FROM sale_line AS l
JOIN sale AS s ON s.sale_id = l.sale_id
JOIN product AS p ON p.product_id = l.product_id;
