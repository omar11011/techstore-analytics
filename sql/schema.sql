-- =============================================================================
-- TechStore Analytics - Database Schema
-- =============================================================================
-- Complete DDL script for the TechStore Analytics project.
-- Creates all tables with proper constraints, relationships, and comments.
-- Table ordering respects foreign key dependencies (parent tables first).
-- =============================================================================

-- =============================================================================
-- 1. CUSTOMERS
-- =============================================================================
-- Stores customer profile information including contact details and address.
-- Each customer can place multiple orders (1:N relationship with orders).
-- =============================================================================

CREATE TABLE IF NOT EXISTS customers (
    customer_id     SERIAL          PRIMARY KEY,
    first_name      VARCHAR(100)    NOT NULL,
    last_name       VARCHAR(100)    NOT NULL,
    email           VARCHAR(255)    NOT NULL UNIQUE,
    phone           VARCHAR(30),
    address_line1   VARCHAR(255),
    address_line2   VARCHAR(255),
    city            VARCHAR(100),
    state           VARCHAR(100),
    postal_code     VARCHAR(20),
    country         VARCHAR(100)    DEFAULT 'Mexico',
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_customers_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

COMMENT ON TABLE customers IS 'Customer profiles with contact information and addresses. Supports 1:N relationship with orders.';


-- =============================================================================
-- 2. CATEGORIES
-- =============================================================================
-- Product classification hierarchy. Each category groups related products
-- (e.g., Laptops, Smartphones, Accessories).
-- =============================================================================

CREATE TABLE IF NOT EXISTS categories (
    category_id     SERIAL          PRIMARY KEY,
    name            VARCHAR(100)    NOT NULL UNIQUE,
    description     TEXT,
    parent_id       INTEGER         REFERENCES categories(category_id) ON DELETE SET NULL,
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_categories_not_self_parent CHECK (parent_id IS NULL OR parent_id <> category_id)
);

COMMENT ON TABLE categories IS 'Product category hierarchy. Supports nested subcategories via self-referencing parent_id.';


-- =============================================================================
-- 3. SUPPLIERS
-- =============================================================================
-- Vendor/supplier information for procurement and cost tracking.
-- Links to products to track supply chain relationships.
-- =============================================================================

CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id     SERIAL          PRIMARY KEY,
    company_name    VARCHAR(200)    NOT NULL,
    contact_name    VARCHAR(150),
    email           VARCHAR(255)    NOT NULL UNIQUE,
    phone           VARCHAR(30),
    address_line1   VARCHAR(255),
    address_line2   VARCHAR(255),
    city            VARCHAR(100),
    state           VARCHAR(100),
    postal_code     VARCHAR(20),
    country         VARCHAR(100)    DEFAULT 'Mexico',
    is_active       BOOLEAN         DEFAULT TRUE,
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_suppliers_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

COMMENT ON TABLE suppliers IS 'Supplier/vendor profiles for procurement tracking. Active flag enables soft-deletion.';


-- =============================================================================
-- 4. PRODUCTS
-- =============================================================================
-- Product catalog with pricing, cost, and categorization.
-- Each product belongs to one category and can be supplied by one supplier.
-- Links to inventory and order_items for stock and sales tracking.
-- =============================================================================

CREATE TABLE IF NOT EXISTS products (
    product_id      SERIAL          PRIMARY KEY,
    sku             VARCHAR(50)     NOT NULL UNIQUE,
    name            VARCHAR(255)    NOT NULL,
    description     TEXT,
    category_id     INTEGER         NOT NULL REFERENCES categories(category_id) ON DELETE RESTRICT,
    supplier_id     INTEGER         REFERENCES suppliers(supplier_id) ON DELETE SET NULL,
    unit_price      NUMERIC(12, 2)  NOT NULL,
    cost_price      NUMERIC(12, 2)  NOT NULL,
    weight_kg       NUMERIC(8, 3),
    dimensions      VARCHAR(50),    -- Format: 'LxWxH' in cm
    is_active       BOOLEAN         DEFAULT TRUE,
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_products_price_positive CHECK (unit_price > 0),
    CONSTRAINT chk_products_cost_positive  CHECK (cost_price >= 0),
    CONSTRAINT chk_products_margin         CHECK (unit_price > cost_price)
);

COMMENT ON TABLE products IS 'Product catalog with pricing and cost data. SKU is unique. Constraints ensure positive pricing and profitable margins.';


-- =============================================================================
-- 5. STORES
-- =============================================================================
-- Physical retail store locations. Each store maintains its own inventory
-- and processes its own orders.
-- =============================================================================

CREATE TABLE IF NOT EXISTS stores (
    store_id        SERIAL          PRIMARY KEY,
    name            VARCHAR(200)    NOT NULL,
    address_line1   VARCHAR(255)    NOT NULL,
    address_line2   VARCHAR(255),
    city            VARCHAR(100)    NOT NULL,
    state           VARCHAR(100),
    postal_code     VARCHAR(20),
    country         VARCHAR(100)    DEFAULT 'Mexico',
    phone           VARCHAR(30),
    email           VARCHAR(255),
    is_active       BOOLEAN         DEFAULT TRUE,
    opening_date    DATE,
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE stores IS 'Physical retail store locations. Active flag supports temporary closures.';


-- =============================================================================
-- 6. INVENTORY
-- =============================================================================
-- Tracks stock levels per product per store. This is the intersection
-- table between products and stores (M:N relationship).
-- Unique constraint ensures one inventory record per product-store pair.
-- =============================================================================

CREATE TABLE IF NOT EXISTS inventory (
    inventory_id    SERIAL          PRIMARY KEY,
    product_id      INTEGER         NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    store_id        INTEGER         NOT NULL REFERENCES stores(store_id) ON DELETE CASCADE,
    stock_quantity  INTEGER         NOT NULL DEFAULT 0,
    reorder_level   INTEGER         NOT NULL DEFAULT 10,
    last_restocked  TIMESTAMP,

    CONSTRAINT uq_inventory_product_store UNIQUE (product_id, store_id),
    CONSTRAINT chk_inventory_stock_nonneg  CHECK (stock_quantity >= 0),
    CONSTRAINT chk_inventory_reorder_pos   CHECK (reorder_level > 0)
);

COMMENT ON TABLE inventory IS 'Stock levels per product per store. Reorder_level triggers restocking alerts. Unique constraint prevents duplicate product-store entries.';


-- =============================================================================
-- 7. ORDERS
-- =============================================================================
-- Customer order headers with status tracking. Each order belongs to one
-- customer and is processed at one store. Status workflow:
-- pending -> confirmed -> processing -> shipped -> delivered | cancelled
-- =============================================================================

CREATE TABLE IF NOT EXISTS orders (
    order_id        SERIAL          PRIMARY KEY,
    customer_id     INTEGER         NOT NULL REFERENCES customers(customer_id) ON DELETE RESTRICT,
    store_id        INTEGER         NOT NULL REFERENCES stores(store_id) ON DELETE RESTRICT,
    order_date      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status          VARCHAR(20)     NOT NULL DEFAULT 'pending',
    total_amount    NUMERIC(12, 2)  NOT NULL DEFAULT 0,
    notes           TEXT,
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_orders_status CHECK (
        status IN ('pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled')
    ),
    CONSTRAINT chk_orders_total_nonneg CHECK (total_amount >= 0)
);

COMMENT ON TABLE orders IS 'Order headers with status workflow: pending -> confirmed -> processing -> shipped -> delivered | cancelled.';


-- =============================================================================
-- 8. ORDER_ITEMS
-- =============================================================================
-- Line items within each order. Each item references a specific product
-- and records the unit price at the time of purchase (price snapshot).
-- This prevents price changes from altering historical order totals.
-- =============================================================================

CREATE TABLE IF NOT EXISTS order_items (
    order_item_id   SERIAL          PRIMARY KEY,
    order_id        INTEGER         NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id      INTEGER         NOT NULL REFERENCES products(product_id) ON DELETE RESTRICT,
    quantity        INTEGER         NOT NULL,
    unit_price      NUMERIC(12, 2)  NOT NULL,   -- Price at time of purchase (snapshot)
    discount_pct    NUMERIC(5, 2)   DEFAULT 0,  -- Percentage discount (0-100)
    line_total      NUMERIC(12, 2)  GENERATED ALWAYS AS (
        quantity * unit_price * (1 - COALESCE(discount_pct, 0) / 100)
    ) STORED,

    CONSTRAINT chk_order_items_qty_positive   CHECK (quantity > 0),
    CONSTRAINT chk_order_items_price_positive CHECK (unit_price > 0),
    CONSTRAINT chk_order_items_discount_range CHECK (discount_pct >= 0 AND discount_pct <= 100)
);

COMMENT ON TABLE order_items IS 'Order line items with price snapshots. line_total is computed: qty * unit_price * (1 - discount%).';


-- =============================================================================
-- 9. PAYMENTS
-- =============================================================================
-- Payment records linked to orders. Supports multiple payment methods
-- and tracks payment status independently from order status.
-- =============================================================================

CREATE TABLE IF NOT EXISTS payments (
    payment_id      SERIAL          PRIMARY KEY,
    order_id        INTEGER         NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    payment_method  VARCHAR(30)     NOT NULL,
    amount          NUMERIC(12, 2)  NOT NULL,
    status          VARCHAR(20)     NOT NULL DEFAULT 'pending',
    transaction_id  VARCHAR(100),               -- External payment gateway reference
    payment_date    TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_payments_method CHECK (
        payment_method IN ('credit_card', 'debit_card', 'cash', 'bank_transfer', 'paypal', 'stripe', 'other')
    ),
    CONSTRAINT chk_payments_status CHECK (
        status IN ('pending', 'completed', 'failed', 'refunded')
    ),
    CONSTRAINT chk_payments_amount_positive CHECK (amount > 0)
);

COMMENT ON TABLE payments IS 'Payment records with multi-method support. Transaction_id links to external payment gateways.';


-- =============================================================================
-- 10. SHIPMENTS
-- =============================================================================
-- Shipment tracking for delivered orders. Each shipment is linked to one
-- order and tracks carrier, tracking number, and delivery timestamps.
-- =============================================================================

CREATE TABLE IF NOT EXISTS shipments (
    shipment_id     SERIAL          PRIMARY KEY,
    order_id        INTEGER         NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    carrier         VARCHAR(100)    NOT NULL,
    tracking_number VARCHAR(100)    NOT NULL UNIQUE,
    shipping_method VARCHAR(50)     DEFAULT 'standard',
    shipped_at      TIMESTAMP,
    estimated_delivery TIMESTAMP,
    delivered_at    TIMESTAMP,
    shipping_cost   NUMERIC(10, 2)  DEFAULT 0,
    status          VARCHAR(20)     NOT NULL DEFAULT 'pending',
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_shipments_status CHECK (
        status IN ('pending', 'picked_up', 'in_transit', 'out_for_delivery', 'delivered', 'returned')
    ),
    CONSTRAINT chk_shipments_cost_nonneg CHECK (shipping_cost >= 0)
);

COMMENT ON TABLE shipments IS 'Shipment tracking with carrier details and delivery timestamps. Status tracks fulfillment progress.';


-- =============================================================================
-- END OF SCHEMA
-- =============================================================================
-- Total: 10 tables
-- Relationships:
--   customers  1──N  orders
--   stores     1──N  orders
--   stores     1──N  inventory
--   products   1──N  inventory
--   products   1──N  order_items
--   orders     1──N  order_items
--   orders     1──N  payments
--   orders     1──1  shipments
--   categories 1──N  products (self-referencing for hierarchy)
--   suppliers  1──N  products
-- =============================================================================
