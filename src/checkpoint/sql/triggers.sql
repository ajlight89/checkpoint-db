-- Checkpoint-DB triggers.
-- BR-nn refers to a business rule in docs/01-requirements.md.

-- BR-01: a subclass row must match its product's type. A missing product
-- makes the subquery NULL, so the trigger stays quiet and the foreign key
-- reports the error instead.

CREATE TRIGGER game_matches_product_type
BEFORE INSERT ON game
WHEN (SELECT product_type FROM product WHERE product_id = NEW.product_id) <> 'game'
BEGIN
    SELECT RAISE(ABORT, 'product_type must be game for a game row');
END;

CREATE TRIGGER console_matches_product_type
BEFORE INSERT ON console
WHEN (SELECT product_type FROM product WHERE product_id = NEW.product_id) <> 'console'
BEGIN
    SELECT RAISE(ABORT, 'product_type must be console for a console row');
END;

CREATE TRIGGER accessory_matches_product_type
BEFORE INSERT ON accessory
WHEN (SELECT product_type FROM product WHERE product_id = NEW.product_id) <> 'accessory'
BEGIN
    SELECT RAISE(ABORT, 'product_type must be accessory for an accessory row');
END;

-- BR-23: a sale line lowers the stock it names. Selling more than is on hand
-- breaks CHECK (qty_on_hand >= 0), which cancels the line as well (BR-12).

CREATE TRIGGER sale_line_lowers_stock
AFTER INSERT ON sale_line
BEGIN
    UPDATE stock_item
    SET qty_on_hand = qty_on_hand - NEW.quantity
    WHERE product_id = NEW.product_id AND condition = NEW.condition;
END;

-- BR-26: a trade-in line raises the stock it names.

CREATE TRIGGER trade_in_line_raises_stock
AFTER INSERT ON trade_in_line
BEGIN
    UPDATE stock_item
    SET qty_on_hand = qty_on_hand + NEW.quantity
    WHERE product_id = NEW.product_id AND condition = NEW.condition;
END;
