-- Checkpoint-DB tables.
-- BR-nn refers to a business rule in docs/01-requirements.md.
-- Money columns hold whole cents. Dates are 'YYYY-MM-DD' text and
-- date-times are 'YYYY-MM-DD HH:MM:SS' text.

-- Catalog

CREATE TABLE platform (
    platform_id     INTEGER PRIMARY KEY,
    platform_name   TEXT    NOT NULL UNIQUE,                        -- BR-03
    manufacturer    TEXT    NOT NULL,
    release_year    INTEGER NOT NULL CHECK (release_year >= 1970)
) STRICT;

CREATE TABLE product (
    product_id      INTEGER PRIMARY KEY,
    name            TEXT    NOT NULL,
    brand           TEXT    NOT NULL,
    release_year    INTEGER NOT NULL CHECK (release_year >= 1970),
    product_type    TEXT    NOT NULL                                -- BR-01
        CHECK (product_type IN ('game', 'console', 'accessory'))
) STRICT;

CREATE TABLE game (
    product_id      INTEGER PRIMARY KEY REFERENCES product (product_id),
    esrb_rating     TEXT                                            -- BR-05
        CHECK (esrb_rating IN ('EC', 'E', 'K-A', 'E10+', 'T', 'M', 'AO')),
    platform_id     INTEGER NOT NULL REFERENCES platform (platform_id)  -- BR-04
) STRICT;

CREATE TABLE game_genre (
    product_id      INTEGER NOT NULL REFERENCES game (product_id),  -- BR-06
    genre           TEXT    NOT NULL,
    PRIMARY KEY (product_id, genre)
) STRICT;

CREATE TABLE console (
    product_id      INTEGER PRIMARY KEY REFERENCES product (product_id),
    model_number    TEXT    NOT NULL UNIQUE,                        -- BR-07
    storage_gb      INTEGER CHECK (storage_gb > 0),
    platform_id     INTEGER NOT NULL REFERENCES platform (platform_id)
) STRICT;

CREATE TABLE accessory (
    product_id      INTEGER PRIMARY KEY REFERENCES product (product_id),
    accessory_type  TEXT    NOT NULL                                -- BR-08
        CHECK (accessory_type IN ('controller', 'cable', 'memory_card', 'headset', 'other'))
) STRICT;

-- Stock

CREATE TABLE stock_item (
    product_id          INTEGER NOT NULL REFERENCES product (product_id),
    condition           TEXT    NOT NULL                            -- BR-09
        CHECK (condition IN ('new', 'used_complete', 'used_loose')),
    qty_on_hand         INTEGER NOT NULL CHECK (qty_on_hand >= 0),  -- BR-12
    sell_price_cents    INTEGER NOT NULL CHECK (sell_price_cents > 0),
    trade_value_cents   INTEGER CHECK (trade_value_cents > 0),
    reorder_threshold   INTEGER NOT NULL CHECK (reorder_threshold >= 0),
    PRIMARY KEY (product_id, condition),
    CHECK ((condition = 'new') = (trade_value_cents IS NULL))       -- BR-11
) STRICT;

-- Customers

CREATE TABLE customer (
    customer_id     INTEGER PRIMARY KEY,
    first_name      TEXT    NOT NULL,
    last_name       TEXT    NOT NULL,
    phone           TEXT    NOT NULL UNIQUE                         -- BR-14
        CHECK (length(phone) = 10 AND phone NOT GLOB '*[^0-9]*')
) STRICT;

CREATE TABLE loyalty_member (
    customer_id     INTEGER PRIMARY KEY REFERENCES customer (customer_id),
    join_date       TEXT    NOT NULL CHECK (date(join_date) = join_date),
    expiry_date     TEXT    NOT NULL CHECK (date(expiry_date) = expiry_date),
    email           TEXT,
    CHECK (expiry_date > join_date)                                 -- BR-16
) STRICT;

-- Sales

CREATE TABLE sale (
    sale_id         INTEGER PRIMARY KEY,
    sale_datetime   TEXT    NOT NULL CHECK (datetime(sale_datetime) = sale_datetime),
    member_id       INTEGER REFERENCES loyalty_member (customer_id),    -- BR-20
    payment_method  TEXT    NOT NULL                                -- BR-22
        CHECK (payment_method IN ('cash', 'card'))
) STRICT;

CREATE TABLE sale_line (
    sale_id                 INTEGER NOT NULL REFERENCES sale (sale_id),
    product_id              INTEGER NOT NULL,
    condition               TEXT    NOT NULL,
    quantity                INTEGER NOT NULL CHECK (quantity > 0),
    unit_price_cents        INTEGER NOT NULL CHECK (unit_price_cents > 0),  -- BR-19
    discount_amount_cents   INTEGER NOT NULL CHECK (discount_amount_cents >= 0),
    PRIMARY KEY (sale_id, product_id, condition),
    FOREIGN KEY (product_id, condition) REFERENCES stock_item (product_id, condition),
    CHECK (discount_amount_cents <= quantity * unit_price_cents)    -- BR-21
) STRICT;

-- Trade-ins

CREATE TABLE trade_in (
    trade_in_id     INTEGER PRIMARY KEY,
    trade_datetime  TEXT    NOT NULL CHECK (datetime(trade_datetime) = trade_datetime),
    customer_id     INTEGER NOT NULL REFERENCES customer (customer_id)
) STRICT;

CREATE TABLE trade_in_line (
    trade_in_id         INTEGER NOT NULL REFERENCES trade_in (trade_in_id),
    product_id          INTEGER NOT NULL,
    condition           TEXT    NOT NULL CHECK (condition <> 'new'),    -- BR-25
    quantity            INTEGER NOT NULL CHECK (quantity > 0),
    unit_value_cents    INTEGER NOT NULL CHECK (unit_value_cents > 0),
    PRIMARY KEY (trade_in_id, product_id, condition),
    FOREIGN KEY (product_id, condition) REFERENCES stock_item (product_id, condition)
) STRICT;
