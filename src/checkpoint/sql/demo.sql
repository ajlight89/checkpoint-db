-- Checkpoint-DB sample data: a small store with a few weeks of activity.
-- BR-nn refers to a business rule in docs/01-requirements.md.
-- Run after schema.sql, triggers.sql, and views.sql. Prices and values are in cents.

-- Catalog

INSERT INTO platform (platform_id, platform_name, manufacturer, release_year) VALUES
    (1, 'PlayStation 4', 'Sony', 2013),
    (2, 'PlayStation 5', 'Sony', 2020),
    (3, 'Nintendo Switch', 'Nintendo', 2017),
    (4, 'Xbox Series X|S', 'Microsoft', 2020),
    (5, 'Super Nintendo', 'Nintendo', 1991),
    (6, 'Nintendo 64', 'Nintendo', 1996);

-- Each product has exactly one row in game, console, or accessory (BR-01).
INSERT INTO product (product_id, name, brand, release_year, product_type) VALUES
    (1, 'Bloodborne', 'Sony', 2015, 'game'),
    (2, 'Elden Ring', 'Bandai Namco', 2022, 'game'),
    (3, 'Astro Bot', 'Sony', 2024, 'game'),
    (4, 'The Legend of Zelda: Breath of the Wild', 'Nintendo', 2017, 'game'),
    (5, 'Mario Kart 8 Deluxe', 'Nintendo', 2017, 'game'),
    (6, 'Halo Infinite', 'Microsoft', 2021, 'game'),
    (7, 'Super Mario World', 'Nintendo', 1991, 'game'),
    (8, 'Super Mario 64', 'Nintendo', 1996, 'game'),
    (9, 'PlayStation 5', 'Sony', 2020, 'console'),
    (10, 'Nintendo Switch OLED Model', 'Nintendo', 2021, 'console'),
    (11, 'Xbox Series X', 'Microsoft', 2020, 'console'),
    (12, 'Super Nintendo Entertainment System', 'Nintendo', 1991, 'console'),
    (13, 'DualSense Wireless Controller', 'Sony', 2020, 'accessory'),
    (14, 'Pulse 3D Wireless Headset', 'Sony', 2021, 'accessory'),
    (15, 'High Speed HDMI Cable, 6 ft', 'Monoprice', 2019, 'accessory'),
    (16, 'microSDXC Card for Nintendo Switch, 256 GB', 'SanDisk', 2018, 'accessory');

-- Games released before 1994 have no ESRB rating (BR-05).
INSERT INTO game (product_id, esrb_rating, platform_id) VALUES
    (1, 'M', 1),
    (2, 'M', 2),
    (3, 'E10+', 2),
    (4, 'E10+', 3),
    (5, 'E', 3),
    (6, 'T', 4),
    (7, NULL, 5),
    (8, 'E', 6);

INSERT INTO game_genre (product_id, genre) VALUES
    (1, 'Action'),
    (1, 'Role-playing'),
    (2, 'Action'),
    (2, 'Role-playing'),
    (3, 'Platformer'),
    (4, 'Action'),
    (4, 'Adventure'),
    (5, 'Racing'),
    (6, 'Shooter'),
    (7, 'Platformer'),
    (8, 'Platformer');

-- The Super Nintendo has no built-in storage, so storage_gb is NULL (BR-07).
INSERT INTO console (product_id, model_number, storage_gb, platform_id) VALUES
    (9, 'CFI-1015A', 825, 2),
    (10, 'HEG-001', 64, 3),
    (11, '1882', 1000, 4),
    (12, 'SNS-001', NULL, 5);

INSERT INTO accessory (product_id, accessory_type) VALUES
    (13, 'controller'),
    (14, 'headset'),
    (15, 'cable'),
    (16, 'memory_card');

-- Stock

-- Quantities here are the counts before the trade-ins and sales below.
-- The triggers raise and lower them as those lines are inserted (BR-23, BR-26).
-- New stock has no trade-in value (BR-11). Older games are stocked used only.
INSERT INTO stock_item
    (product_id, condition, qty_on_hand, sell_price_cents, trade_value_cents, reorder_threshold)
VALUES
    (1, 'new', 3, 1999, NULL, 2),
    (1, 'used_complete', 4, 1299, 500, 2),
    (2, 'new', 5, 5999, NULL, 2),
    (2, 'used_complete', 3, 3999, 2000, 2),
    (3, 'new', 4, 5999, NULL, 2),
    (4, 'new', 4, 5999, NULL, 2),
    (4, 'used_complete', 2, 3999, 2000, 2),
    (5, 'new', 6, 5999, NULL, 3),
    (5, 'used_loose', 3, 3499, 1500, 2),
    (6, 'new', 2, 3999, NULL, 2),
    (6, 'used_complete', 3, 1999, 800, 1),
    (7, 'used_complete', 1, 6999, 3000, 1),
    (7, 'used_loose', 2, 2999, 1200, 1),
    (8, 'used_loose', 3, 3999, 1800, 1),
    (9, 'new', 3, 49999, NULL, 1),
    (9, 'used_complete', 1, 34999, 20000, 1),
    (10, 'new', 3, 34999, NULL, 1),
    (11, 'new', 2, 49999, NULL, 1),
    (12, 'used_complete', 1, 14999, 6000, 1),
    (13, 'new', 8, 6999, NULL, 4),
    (13, 'used_loose', 2, 3999, 1500, 1),
    (14, 'new', 4, 9999, NULL, 2),
    (15, 'new', 10, 1299, NULL, 5),
    (16, 'new', 4, 2999, NULL, 3);

-- Customers

-- Customers 1, 2, 3, 5, 7, and 9 are loyalty members. The others are
-- walk-in sellers, recorded because each one sold items to the store (BR-13).
INSERT INTO customer (customer_id, first_name, last_name, phone) VALUES
    (1, 'Maya', 'Chen', '5095550111'),
    (2, 'Jordan', 'Reyes', '5095550112'),
    (3, 'Priya', 'Patel', '5095550113'),
    (4, 'Liam', 'Walsh', '5095550114'),
    (5, 'Sofia', 'Rossi', '5095550115'),
    (6, 'Ethan', 'Brooks', '5095550116'),
    (7, 'Hannah', 'Kim', '5095550117'),
    (8, 'Noah', 'Fischer', '5095550118'),
    (9, 'Grace', 'Okafor', '5095550119'),
    (10, 'Lucas', 'Moreau', '5095550120'),
    (11, 'Ava', 'Thompson', '5095550121'),
    (12, 'Daniel', 'Novak', '5095550122');

-- Each membership runs a whole number of years: one year plus any renewals (BR-16).
-- Members 5 and 9 have expired; the rest are active through the end of 2026.
INSERT INTO loyalty_member (customer_id, join_date, expiry_date, email) VALUES
    (1, '2023-02-10', '2027-02-10', 'maya.chen@example.com'),
    (2, '2026-06-01', '2027-06-01', 'jordan.reyes@example.com'),
    (3, '2024-09-15', '2027-09-15', NULL),
    (5, '2024-01-20', '2025-01-20', 'sofia.rossi@example.com'),
    (7, '2026-10-05', '2027-10-05', 'hannah.kim@example.com'),
    (9, '2025-03-03', '2026-03-03', NULL);

-- Trade-ins

-- Each line pays the stock record's trade-in value and accepts only used items (BR-25).
INSERT INTO trade_in (trade_in_id, trade_datetime, customer_id) VALUES
    (1, '2026-10-02 10:05:00', 4),
    (2, '2026-10-09 16:20:00', 6),
    (3, '2026-10-15 12:00:00', 8),
    (4, '2026-10-22 17:45:00', 2),
    (5, '2026-10-30 11:30:00', 10),
    (6, '2026-11-06 14:10:00', 11),
    (7, '2026-11-07 15:35:00', 12),
    (8, '2026-11-12 10:50:00', 5);

INSERT INTO trade_in_line (trade_in_id, product_id, condition, quantity, unit_value_cents) VALUES
    (1, 7, 'used_loose', 1, 1200),
    (1, 8, 'used_loose', 1, 1800),
    (2, 1, 'used_complete', 2, 500),
    (3, 9, 'used_complete', 1, 20000),
    (3, 13, 'used_loose', 1, 1500),
    (4, 5, 'used_loose', 1, 1500),
    (5, 12, 'used_complete', 1, 6000),
    (5, 7, 'used_complete', 1, 3000),
    (6, 6, 'used_complete', 1, 800),
    (7, 4, 'used_complete', 1, 2000),
    (7, 2, 'used_complete', 1, 2000),
    (8, 8, 'used_loose', 1, 1800);

-- Sales

-- Each line charges the stock record's selling price (BR-19). A member who is
-- active on the day of the sale gets 10% off each line, rounded half up to the
-- nearest cent (BR-21). Sales 6 and 12 belong to expired members, so their lines
-- have no discount.
INSERT INTO sale (sale_id, sale_datetime, member_id, payment_method) VALUES
    (1, '2026-10-03 11:15:00', NULL, 'card'),
    (2, '2026-10-04 13:40:00', 1, 'card'),
    (3, '2026-10-07 18:05:00', NULL, 'cash'),
    (4, '2026-10-11 12:25:00', 3, 'card'),
    (5, '2026-10-18 15:50:00', NULL, 'card'),
    (6, '2026-10-24 10:30:00', 5, 'cash'),
    (7, '2026-10-31 19:10:00', 7, 'card'),
    (8, '2026-11-05 13:00:00', NULL, 'cash'),
    (9, '2026-11-08 16:45:00', 2, 'card'),
    (10, '2026-11-09 11:55:00', NULL, 'card'),
    (11, '2026-11-10 14:20:00', 1, 'cash'),
    (12, '2026-11-11 17:30:00', 9, 'card');

INSERT INTO sale_line
    (sale_id, product_id, condition, quantity, unit_price_cents, discount_amount_cents)
VALUES
    (1, 5, 'new', 1, 5999, 0),
    (1, 15, 'new', 1, 1299, 0),
    (2, 2, 'new', 1, 5999, 600),
    (2, 13, 'new', 1, 6999, 700),
    (3, 7, 'used_loose', 1, 2999, 0),
    (4, 9, 'new', 1, 49999, 5000),
    (4, 13, 'new', 1, 6999, 700),
    (4, 15, 'new', 1, 1299, 130),
    (5, 10, 'new', 1, 34999, 0),
    (5, 16, 'new', 2, 2999, 0),
    (6, 1, 'used_complete', 1, 1299, 0),
    (7, 3, 'new', 1, 5999, 600),
    (7, 14, 'new', 1, 9999, 1000),
    (8, 8, 'used_loose', 2, 3999, 0),
    (9, 4, 'new', 1, 5999, 600),
    (9, 5, 'used_loose', 1, 3499, 350),
    (10, 11, 'new', 1, 49999, 0),
    (10, 6, 'new', 1, 3999, 0),
    (11, 12, 'used_complete', 1, 14999, 1500),
    (11, 7, 'used_complete', 1, 6999, 700),
    (12, 16, 'new', 1, 2999, 0),
    (12, 15, 'new', 2, 1299, 0);
