-- =============================================================================
-- TechStore Analytics - Analytical Views
-- =============================================================================
-- Creates 6 views for common reporting and analytics queries.
-- These views encapsulate complex joins and aggregations for easy consumption
-- by dashboards, reports, and application code.
-- =============================================================================


-- =============================================================================
-- VIEW 1: monthly_sales_summary
-- =============================================================================
-- Aggregates sales data by year and month for trend analysis and forecasting.
-- Provides total revenue, order count, average ticket size, and unique customers.
-- =============================================================================

CREATE OR REPLACE VIEW monthly_sales_summary AS
SELECT
    EXTRACT(YEAR FROM o.order_date)::INTEGER                        AS year,
    EXTRACT(MONTH FROM o.order_date)::INTEGER                       AS month,
    SUM(o.total_amount)::NUMERIC(14, 2)                             AS total_sales,
    COUNT(DISTINCT o.order_id)                                      AS num_orders,
    ROUND((SUM(o.total_amount) / NULLIF(COUNT(DISTINCT o.order_id), 0))::NUMERIC, 2) AS avg_ticket,
    COUNT(DISTINCT o.customer_id)                                   AS num_customers
FROM orders o
WHERE o.status NOT IN ('cancelled')
GROUP BY
    EXTRACT(YEAR FROM o.order_date),
    EXTRACT(MONTH FROM o.order_date);

COMMENT ON VIEW monthly_sales_summary IS 'Monthly sales aggregation: total revenue, order count, average ticket, and unique customers per month. Excludes cancelled orders.';


-- =============================================================================
-- VIEW 2: top_customers
-- =============================================================================
-- Ranks customers by total spending. Useful for loyalty programs, VIP tiers,
-- and customer segmentation analysis.
-- =============================================================================

CREATE OR REPLACE VIEW top_customers AS
SELECT
    c.customer_id,
    c.first_name,
    c.last_name,
    SUM(o.total_amount)::NUMERIC(14, 2)                             AS total_spent,
    COUNT(o.order_id)                                                AS num_orders,
    ROUND((SUM(o.total_amount) / NULLIF(COUNT(o.order_id), 0))::NUMERIC, 2) AS avg_ticket
FROM customers c
INNER JOIN orders o ON c.customer_id = o.customer_id
WHERE o.status NOT IN ('cancelled')
GROUP BY
    c.customer_id,
    c.first_name,
    c.last_name;

COMMENT ON VIEW top_customers IS 'Customer ranking by total spending. Includes order count and average ticket for segmentation.';


-- =============================================================================
-- VIEW 3: inventory_status
-- =============================================================================
-- Classifies inventory levels as 'out', 'low', or 'ok' based on stock
-- quantity relative to the reorder level. Essential for restocking alerts
-- and supply chain dashboards.
-- =============================================================================

CREATE OR REPLACE VIEW inventory_status AS
SELECT
    i.product_id,
    p.name                                                            AS product_name,
    i.store_id,
    s.name                                                            AS store_name,
    i.stock_quantity,
    i.reorder_level,
    CASE
        WHEN i.stock_quantity = 0                   THEN 'out'
        WHEN i.stock_quantity <= i.reorder_level    THEN 'low'
        ELSE 'ok'
    END                                                               AS status
FROM inventory i
INNER JOIN products p ON i.product_id = p.product_id
INNER JOIN stores s   ON i.store_id   = s.store_id;

COMMENT ON VIEW inventory_status IS 'Inventory classification by stock level: out (0), low (<= reorder_level), or ok. Used for restock alerts.';


-- =============================================================================
-- VIEW 4: category_sales_summary
-- =============================================================================
-- Aggregates sales performance by product category. Shows total revenue,
-- product count, and average selling price per category. Useful for
-- category management and assortment optimization.
-- =============================================================================

CREATE OR REPLACE VIEW category_sales_summary AS
SELECT
    cat.category_id,
    cat.name                                                          AS category_name,
    SUM(oi.line_total)::NUMERIC(14, 2)                               AS total_sales,
    COUNT(DISTINCT p.product_id)                                      AS num_products,
    ROUND(AVG(p.unit_price)::NUMERIC, 2)                              AS avg_price
FROM categories cat
INNER JOIN products p     ON cat.category_id = p.category_id
INNER JOIN order_items oi ON p.product_id    = oi.product_id
INNER JOIN orders o       ON oi.order_id     = o.order_id
WHERE o.status NOT IN ('cancelled')
GROUP BY
    cat.category_id,
    cat.name;

COMMENT ON VIEW category_sales_summary IS 'Category-level sales performance: total revenue, product count, and average price per category.';


-- =============================================================================
-- VIEW 5: product_profitability
-- =============================================================================
-- Calculates gross profit and profit margin per product. Combines revenue
-- from order_items with cost data from the products table. Essential for
-- margin analysis and pricing strategy.
-- =============================================================================

CREATE OR REPLACE VIEW product_profitability AS
SELECT
    p.product_id,
    p.name                                                            AS product_name,
    cat.name                                                          AS category_name,
    SUM(oi.line_total)::NUMERIC(14, 2)                               AS total_revenue,
    SUM(p.cost_price * oi.quantity)::NUMERIC(14, 2)                   AS total_cost,
    (SUM(oi.line_total) - SUM(p.cost_price * oi.quantity))::NUMERIC(14, 2) AS gross_profit,
    CASE
        WHEN SUM(oi.line_total) > 0
        THEN ROUND(((SUM(oi.line_total) - SUM(p.cost_price * oi.quantity)) / SUM(oi.line_total) * 100)::NUMERIC, 2)
        ELSE 0
    END                                                               AS profit_margin,
    SUM(oi.quantity)                                                  AS units_sold
FROM products p
INNER JOIN categories cat  ON p.category_id   = cat.category_id
INNER JOIN order_items oi  ON p.product_id    = oi.product_id
INNER JOIN orders o        ON oi.order_id     = o.order_id
WHERE o.status NOT IN ('cancelled')
GROUP BY
    p.product_id,
    p.name,
    cat.name;

COMMENT ON VIEW product_profitability IS 'Product-level profitability: revenue, cost, gross profit, and margin %. Critical for pricing and margin analysis.';


-- =============================================================================
-- VIEW 6: store_performance
-- =============================================================================
-- Evaluates store-level performance including total sales, order volume,
-- customer reach, and average ticket size. Key view for regional
-- performance benchmarking and store comparisons.
-- =============================================================================

CREATE OR REPLACE VIEW store_performance AS
SELECT
    s.store_id,
    s.name                                                            AS store_name,
    s.city,
    s.country,
    SUM(o.total_amount)::NUMERIC(14, 2)                               AS total_sales,
    COUNT(o.order_id)                                                 AS num_orders,
    COUNT(DISTINCT o.customer_id)                                     AS num_customers,
    ROUND((SUM(o.total_amount) / NULLIF(COUNT(o.order_id), 0))::NUMERIC, 2) AS avg_ticket
FROM stores s
INNER JOIN orders o ON s.store_id = o.store_id
WHERE o.status NOT IN ('cancelled')
GROUP BY
    s.store_id,
    s.name,
    s.city,
    s.country;

COMMENT ON VIEW store_performance IS 'Store-level KPIs: total sales, order count, unique customers, and average ticket. For regional benchmarking.';


-- =============================================================================
-- END OF VIEWS
-- =============================================================================
-- Total: 6 views
--   1. monthly_sales_summary   - Time-series sales trends
--   2. top_customers           - Customer spending rankings
--   3. inventory_status        - Stock level classification
--   4. category_sales_summary  - Category performance metrics
--   5. product_profitability   - Margin and profit analysis
--   6. store_performance       - Store-level KPI dashboard
-- =============================================================================
