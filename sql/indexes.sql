-- =============================================================================
-- TechStore Analytics - Performance Indexes
-- =============================================================================
-- Creates indexes to optimize common query patterns in the TechStore
-- Analytics database. Each index targets specific access paths identified
-- in the application workload.
--
-- Strategy:
--   - B-tree indexes (default) for equality and range lookups
--   - Composite indexes where multi-column access patterns exist
--   - IF NOT EXISTS to ensure idempotent execution
-- =============================================================================


-- =============================================================================
-- ORDERS TABLE INDEXES
-- =============================================================================
-- The orders table is the most heavily queried table. Indexes target:
--   - Date range filtering (reports, dashboards)
--   - Customer order history lookups
--   - Store-level order aggregation
--   - Status-based filtering (active order tracking)
-- =============================================================================

-- Supports date-range queries: monthly reports, daily summaries, trend analysis
CREATE INDEX IF NOT EXISTS idx_orders_order_date
    ON orders (order_date);

COMMENT ON INDEX idx_orders_order_date IS 'Optimizes date-range queries for sales reports, trend analysis, and monthly aggregations.';


-- Supports customer order history: "my orders" pages, customer analysis
CREATE INDEX IF NOT EXISTS idx_orders_customer_id
    ON orders (customer_id);

COMMENT ON INDEX idx_orders_customer_id IS 'Optimizes customer order history lookups and customer spending aggregations.';


-- Supports store-level reporting: store performance dashboards, regional analysis
CREATE INDEX IF NOT EXISTS idx_orders_store_id
    ON orders (store_id);

COMMENT ON INDEX idx_orders_store_id IS 'Optimizes store-level order aggregation and performance reporting.';


-- Supports status filtering: active order tracking, pending order queues
CREATE INDEX IF NOT EXISTS idx_orders_status
    ON orders (status);

COMMENT ON INDEX idx_orders_status IS 'Optimizes filtering by order status for workflow queues (pending, shipped, etc.).';


-- =============================================================================
-- CUSTOMERS TABLE INDEXES
-- =============================================================================
-- The email unique constraint already creates an implicit index, but we
-- create an explicit one for documentation and to support case-insensitive
-- lookups if needed.
-- =============================================================================

-- Supports login lookups, duplicate detection, and customer search by email
CREATE INDEX IF NOT EXISTS idx_customers_email
    ON customers (email);

COMMENT ON INDEX idx_customers_email IS 'Optimizes email-based customer lookups (login, search, duplicate detection). Note: UNIQUE constraint also creates an index.';


-- =============================================================================
-- PRODUCTS TABLE INDEXES
-- =============================================================================
-- Indexes for product lookup patterns:
--   - SKU-based lookups (barcode scanning, API integrations)
--   - Category-based product listing and filtering
-- =============================================================================

-- Supports SKU lookups: barcode scanning, API product resolution, inventory sync
CREATE INDEX IF NOT EXISTS idx_products_sku
    ON products (sku);

COMMENT ON INDEX idx_products_sku IS 'Optimizes SKU-based product lookups for barcode scanning, API resolution, and inventory sync. Note: UNIQUE constraint also creates an index.';


-- Supports category filtering: product listing pages, category browsing
CREATE INDEX IF NOT EXISTS idx_products_category_id
    ON products (category_id);

COMMENT ON INDEX idx_products_category_id IS 'Optimizes category-based product filtering for catalog browsing and category sales reports.';


-- =============================================================================
-- INVENTORY TABLE INDEXES
-- =============================================================================
-- Inventory is frequently queried by product and by store. The unique
-- constraint on (product_id, store_id) already creates a composite index,
-- but individual indexes support single-column access patterns.
-- =============================================================================

-- Supports product inventory lookups: "find all stores carrying product X"
CREATE INDEX IF NOT EXISTS idx_inventory_product_id
    ON inventory (product_id);

COMMENT ON INDEX idx_inventory_product_id IS 'Optimizes queries finding all store inventories for a given product.';


-- Supports store inventory lookups: "show all products in store X"
CREATE INDEX IF NOT EXISTS idx_inventory_store_id
    ON inventory (store_id);

COMMENT ON INDEX idx_inventory_store_id IS 'Optimizes queries listing all products in a given store for inventory dashboards.';


-- =============================================================================
-- ORDER_ITEMS TABLE INDEXES
-- =============================================================================
-- Order items are always accessed via either the parent order or the
-- product. These indexes support both access patterns efficiently.
-- =============================================================================

-- Supports order detail queries: "show all items in order X"
CREATE INDEX IF NOT EXISTS idx_order_items_order_id
    ON order_items (order_id);

COMMENT ON INDEX idx_order_items_order_id IS 'Optimizes retrieval of line items for a given order (order detail pages, receipts).';


-- Supports product sales queries: "how many times was product X sold?"
CREATE INDEX IF NOT EXISTS idx_order_items_product_id
    ON order_items (product_id);

COMMENT ON INDEX idx_order_items_product_id IS 'Optimizes product sales aggregation: total units sold, revenue by product, best-sellers.';


-- =============================================================================
-- SHIPMENTS TABLE INDEXES
-- =============================================================================
-- Shipments are frequently looked up by tracking number for customer
-- service and delivery tracking interfaces.
-- =============================================================================

-- Supports tracking number lookups: delivery tracking, customer service queries
CREATE INDEX IF NOT EXISTS idx_shipments_tracking_number
    ON shipments (tracking_number);

COMMENT ON INDEX idx_shipments_tracking_number IS 'Optimizes tracking number searches for delivery tracking and customer service. Note: UNIQUE constraint also creates an index.';


-- =============================================================================
-- PAYMENTS TABLE INDEXES
-- =============================================================================
-- Payment method analysis and reconciliation queries benefit from an
-- index on payment_method.
-- =============================================================================

-- Supports payment method analytics: method distribution, reconciliation reports
CREATE INDEX IF NOT EXISTS idx_payments_payment_method
    ON payments (payment_method);

COMMENT ON INDEX idx_payments_payment_method IS 'Optimizes payment method analytics: distribution reports, reconciliation, and method preferences.';


-- =============================================================================
-- ADDITIONAL COMPOSITE INDEXES (RECOMMENDED)
-- =============================================================================
-- These composite indexes target multi-column access patterns observed in
-- the views and showcase queries. They significantly improve performance
-- for complex analytical workloads.
-- =============================================================================

-- Supports monthly sales reporting: filters by date range + non-cancelled status
CREATE INDEX IF NOT EXISTS idx_orders_date_status
    ON orders (order_date, status);

COMMENT ON INDEX idx_orders_date_status IS 'Composite index optimizing date-range queries that also filter by status (monthly reports excluding cancelled orders).';


-- Supports inventory alert queries: finds products needing restock
CREATE INDEX IF NOT EXISTS idx_inventory_stock_quantity
    ON inventory (stock_quantity)
    WHERE stock_quantity <= reorder_level;

COMMENT ON INDEX idx_inventory_stock_quantity IS 'Partial index for low-stock alerts. Only indexes rows where stock is at or below reorder level, saving space and improving alert query speed.';


-- Supports order item revenue calculations with product join
CREATE INDEX IF NOT EXISTS idx_order_items_product_order
    ON order_items (product_id, order_id);

COMMENT ON INDEX idx_order_items_product_order IS 'Composite index for product sales queries that also need order context (date, status).';


-- =============================================================================
-- END OF INDEXES
-- =============================================================================
-- Total: 15 indexes
--   - 13 standard indexes (covering all requested access patterns)
--   - 1 composite index (date + status for reporting)
--   - 1 partial index (low-stock alert optimization)
-- =============================================================================
