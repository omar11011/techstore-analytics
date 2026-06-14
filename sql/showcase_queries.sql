-- =============================================================================
-- TechStore Analytics - Showcase Queries
-- =============================================================================
-- 20 advanced SQL queries demonstrating analytical capabilities.
-- Each query includes a header comment block explaining:
--   - Purpose and business value
--   - SQL features demonstrated
--   - Expected output columns
-- =============================================================================


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║ QUERY 1: Top 10 productos más vendidos                                    ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝
-- Purpose:  Identify the 10 best-selling products by total quantity sold.
--           Critical for inventory planning, demand forecasting, and
--           identifying star products.
-- Features: JOIN, GROUP BY, ORDER BY, LIMIT, aggregate functions (SUM, COUNT)
-- Output:   rank, product_name, category_name, units_sold, total_revenue

SELECT
    RANK() OVER (ORDER BY SUM(oi.quantity) DESC)  AS rank,
    p.name                                          AS product_name,
    cat.name                                        AS category_name,
    SUM(oi.quantity)                                AS units_sold,
    SUM(oi.line_total)::NUMERIC(14, 2)              AS total_revenue
FROM order_items oi
INNER JOIN products p     ON oi.product_id  = p.product_id
INNER JOIN categories cat ON p.category_id  = cat.category_id
INNER JOIN orders o       ON oi.order_id    = o.order_id
WHERE o.status NOT IN ('cancelled')
GROUP BY
    p.product_id,
    p.name,
    cat.name
ORDER BY
    units_sold DESC
LIMIT 10;


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║ QUERY 2: Clientes con mayor gasto acumulado                               ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝
-- Purpose:  Rank customers by cumulative spending. Supports VIP identification,
--           loyalty program tiers, and targeted marketing campaigns.
-- Features: JOIN, GROUP BY, window function (RANK), aggregate functions,
--           COALESCE, date arithmetic
-- Output:   rank, customer_id, full_name, total_spent, num_orders, avg_ticket, first_order_date

SELECT
    RANK() OVER (ORDER BY SUM(o.total_amount) DESC)  AS rank,
    c.customer_id,
    (c.first_name || ' ' || c.last_name)              AS full_name,
    SUM(o.total_amount)::NUMERIC(14, 2)                AS total_spent,
    COUNT(o.order_id)                                  AS num_orders,
    ROUND((SUM(o.total_amount) / COUNT(o.order_id))::NUMERIC, 2) AS avg_ticket,
    MIN(o.order_date)::DATE                            AS first_order_date
FROM customers c
INNER JOIN orders o ON c.customer_id = o.customer_id
WHERE o.status NOT IN ('cancelled')
GROUP BY
    c.customer_id,
    c.first_name,
    c.last_name
ORDER BY
    total_spent DESC
LIMIT 20;


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║ QUERY 3: Ventas mensuales (revenue by month)                              ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝
-- Purpose:  Show monthly revenue trend for financial reporting and forecasting.
--           Identifies seasonal patterns and growth trajectories.
-- Features: EXTRACT, TO_CHAR, GROUP BY with date truncation, aggregate functions,
--           ORDER BY multi-column
-- Output:   year, month, month_name, total_sales, num_orders, avg_ticket, num_customers

SELECT
    EXTRACT(YEAR FROM o.order_date)::INTEGER           AS year,
    EXTRACT(MONTH FROM o.order_date)::INTEGER          AS month,
    TO_CHAR(o.order_date, 'Month')                     AS month_name,
    SUM(o.total_amount)::NUMERIC(14, 2)                AS total_sales,
    COUNT(DISTINCT o.order_id)                         AS num_orders,
    ROUND((SUM(o.total_amount) / NULLIF(COUNT(DISTINCT o.order_id), 0))::NUMERIC, 2) AS avg_ticket,
    COUNT(DISTINCT o.customer_id)                      AS num_customers
FROM orders o
WHERE o.status NOT IN ('cancelled')
GROUP BY
    EXTRACT(YEAR FROM o.order_date),
    EXTRACT(MONTH FROM o.order_date),
    TO_CHAR(o.order_date, 'Month')
ORDER BY
    year DESC,
    month DESC;


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║ QUERY 4: Ventas por categoría                                            ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝
-- Purpose:  Analyze revenue distribution across product categories.
--           Supports assortment planning and category management decisions.
-- Features: Multiple JOINs, GROUP BY, ROUND, aggregate functions,
--           percentage calculation with subquery
-- Output:   category_name, total_sales, num_products, num_units_sold, pct_of_total_sales

SELECT
    cat.name                                            AS category_name,
    SUM(oi.line_total)::NUMERIC(14, 2)                  AS total_sales,
    COUNT(DISTINCT p.product_id)                        AS num_products,
    SUM(oi.quantity)                                    AS num_units_sold,
    ROUND(
        (SUM(oi.line_total) / (
            SELECT SUM(oi2.line_total)
            FROM order_items oi2
            INNER JOIN orders o2 ON oi2.order_id = o2.order_id
            WHERE o2.status NOT IN ('cancelled')
        ) * 100)::NUMERIC, 2
    )                                                   AS pct_of_total_sales
FROM categories cat
INNER JOIN products p     ON cat.category_id = p.category_id
INNER JOIN order_items oi ON p.product_id    = oi.product_id
INNER JOIN orders o       ON oi.order_id     = o.order_id
WHERE o.status NOT IN ('cancelled')
GROUP BY
    cat.category_id,
    cat.name
ORDER BY
    total_sales DESC;


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║ QUERY 5: Ventas por proveedor                                            ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝
-- Purpose:  Evaluate supplier contribution to total revenue. Supports
--           supplier negotiation, procurement strategy, and dependency analysis.
-- Features: LEFT JOIN (to include suppliers with no sales), COALESCE,
--           subquery for percentage, GROUP BY
-- Output:   supplier_name, num_products_supplied, total_sales, num_units_sold, pct_of_total

SELECT
    s.company_name                                      AS supplier_name,
    COUNT(DISTINCT p.product_id)                        AS num_products_supplied,
    COALESCE(SUM(oi.line_total), 0)::NUMERIC(14, 2)    AS total_sales,
    COALESCE(SUM(oi.quantity), 0)                       AS num_units_sold,
    ROUND(
        COALESCE(SUM(oi.line_total), 0) / NULLIF(
            (SELECT SUM(oi2.line_total)
             FROM order_items oi2
             INNER JOIN orders o2 ON oi2.order_id = o2.order_id
             WHERE o2.status NOT IN ('cancelled')),
            0
        ) * 100::NUMERIC, 2
    )                                                   AS pct_of_total
FROM suppliers s
LEFT JOIN products p     ON s.supplier_id = p.supplier_id
LEFT JOIN order_items oi ON p.product_id  = oi.product_id
LEFT JOIN orders o       ON oi.order_id   = o.order_id
    AND o.status NOT IN ('cancelled')
WHERE s.is_active = TRUE
GROUP BY
    s.supplier_id,
    s.company_name
ORDER BY
    total_sales DESC;


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║ QUERY 6: Ticket promedio                                                 ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝
-- Purpose:  Calculate the overall average order value (ticket) and break it
--           down by store and payment method. Key metric for sales strategy.
-- Features: CTE (WITH clause), multiple aggregate levels, UNION ALL,
--           GROUPING SETS alternative, CASE for labeling
-- Output:   dimension, dimension_value, avg_ticket, num_orders, min_ticket, max_ticket

WITH order_totals AS (
    SELECT
        o.order_id,
        o.total_amount,
        o.store_id,
        st.name          AS store_name,
        pay.payment_method
    FROM orders o
    LEFT JOIN stores st  ON o.store_id = st.store_id
    LEFT JOIN LATERAL (
        SELECT payment_method
        FROM payments p
        WHERE p.order_id = o.order_id
          AND p.status = 'completed'
        LIMIT 1
    ) pay ON TRUE
    WHERE o.status NOT IN ('cancelled')
)
SELECT
    dimension,
    dimension_value,
    ROUND(AVG(total_amount)::NUMERIC, 2)   AS avg_ticket,
    COUNT(order_id)                         AS num_orders,
    ROUND(MIN(total_amount)::NUMERIC, 2)    AS min_ticket,
    ROUND(MAX(total_amount)::NUMERIC, 2)    AS max_ticket
FROM (
    SELECT 'Overall' AS dimension, 'All' AS dimension_value, order_id, total_amount FROM order_totals
    UNION ALL
    SELECT 'Store', store_name, order_id, total_amount FROM order_totals
    UNION ALL
    SELECT 'Payment Method', COALESCE(payment_method, 'unknown'), order_id, total_amount FROM order_totals
) combined
GROUP BY
    dimension,
    dimension_value
ORDER BY
    dimension,
    avg_ticket DESC;


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║ QUERY 7: Productos sin ventas (LEFT JOIN + IS NULL)                       ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝
-- Purpose:  Identify products that have never been sold. Critical for
--           dead inventory detection, catalog cleanup, and markdown decisions.
-- Features: LEFT JOIN + IS NULL pattern, COALESCE, subquery for last activity
-- Output:   product_id, product_name, sku, category_name, unit_price, days_since_creation

SELECT
    p.product_id,
    p.name                                              AS product_name,
    p.sku,
    cat.name                                            AS category_name,
    p.unit_price,
    (CURRENT_DATE - p.created_at::DATE)                 AS days_since_creation
FROM products p
INNER JOIN categories cat ON p.category_id = cat.category_id
LEFT JOIN order_items oi  ON p.product_id  = oi.product_id
LEFT JOIN orders o        ON oi.order_id   = o.order_id
    AND o.status NOT IN ('cancelled')
WHERE oi.order_item_id IS NULL
    AND p.is_active = TRUE
ORDER BY
    days_since_creation DESC;


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║ QUERY 8: Productos con bajo stock (inventory < 10)                        ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝
-- Purpose:  Find products with low inventory across all stores.
--           Essential for automated restock alerts and purchase order generation.
-- Features: JOIN, CASE expression, arithmetic comparison, COALESCE
-- Output:   product_name, sku, store_name, stock_quantity, reorder_level, deficit, urgency

SELECT
    p.name                                              AS product_name,
    p.sku,
    s.name                                              AS store_name,
    i.stock_quantity,
    i.reorder_level,
    (i.reorder_level - i.stock_quantity)                AS deficit,
    CASE
        WHEN i.stock_quantity = 0          THEN 'CRITICAL - Out of stock'
        WHEN i.stock_quantity <= 5         THEN 'URGENT - Very low'
        WHEN i.stock_quantity <= i.reorder_level THEN 'WARNING - Below reorder level'
        ELSE 'OK'
    END                                                 AS urgency
FROM inventory i
INNER JOIN products p ON i.product_id = p.product_id
INNER JOIN stores s   ON i.store_id   = s.store_id
WHERE i.stock_quantity < 10
    AND p.is_active = TRUE
ORDER BY
    i.stock_quantity ASC,
    p.name;


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║ QUERY 9: Inventario por tienda                                           ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝
-- Purpose:  Provide a complete inventory overview per store with stock value.
--           Supports inventory valuation, transfer planning, and audit.
-- Features: Multiple JOINs, aggregate functions, CASE for stock health,
--           GROUP BY with ROLLUP-like totals
-- Output:   store_name, city, total_products, total_units, inventory_value, low_stock_count, out_of_stock_count

SELECT
    s.name                                              AS store_name,
    s.city,
    COUNT(DISTINCT i.product_id)                        AS total_products,
    SUM(i.stock_quantity)                               AS total_units,
    SUM(i.stock_quantity * p.unit_price)::NUMERIC(14, 2) AS inventory_value,
    SUM(CASE WHEN i.stock_quantity > 0 AND i.stock_quantity <= i.reorder_level THEN 1 ELSE 0 END)
                                                        AS low_stock_count,
    SUM(CASE WHEN i.stock_quantity = 0 THEN 1 ELSE 0 END)
                                                        AS out_of_stock_count
FROM stores s
INNER JOIN inventory i ON s.store_id    = i.store_id
INNER JOIN products p  ON i.product_id  = p.product_id
WHERE s.is_active = TRUE
    AND p.is_active = TRUE
GROUP BY
    s.store_id,
    s.name,
    s.city
ORDER BY
    inventory_value DESC;


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║ QUERY 10: Ranking de tiendas por ventas                                   ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝
-- Purpose:  Rank stores by total sales with key performance indicators.
--           Supports regional performance comparison and resource allocation.
-- Features: Window functions (RANK, LAG), aggregate functions, COALESCE,
--           date filtering, multiple CTEs
-- Output:   rank, store_name, city, country, total_sales, num_orders, num_customers, avg_ticket, prev_month_sales, sales_change_pct

WITH current_period AS (
    SELECT
        o.store_id,
        SUM(o.total_amount)                             AS total_sales,
        COUNT(o.order_id)                               AS num_orders,
        COUNT(DISTINCT o.customer_id)                   AS num_customers
    FROM orders o
    WHERE o.status NOT IN ('cancelled')
    GROUP BY o.store_id
),
monthly_store_sales AS (
    SELECT
        o.store_id,
        EXTRACT(YEAR FROM o.order_date)::INTEGER        AS yr,
        EXTRACT(MONTH FROM o.order_date)::INTEGER       AS mo,
        SUM(o.total_amount)                             AS monthly_sales
    FROM orders o
    WHERE o.status NOT IN ('cancelled')
    GROUP BY o.store_id, yr, mo
)
SELECT
    RANK() OVER (ORDER BY cp.total_sales DESC)          AS rank,
    s.name                                              AS store_name,
    s.city,
    s.country,
    cp.total_sales::NUMERIC(14, 2),
    cp.num_orders,
    cp.num_customers,
    ROUND((cp.total_sales / NULLIF(cp.num_orders, 0))::NUMERIC, 2) AS avg_ticket,
    LAG(ms.monthly_sales) OVER (
        PARTITION BY ms.store_id ORDER BY ms.yr, ms.mo
    )::NUMERIC(14, 2)                                   AS prev_month_sales,
    CASE
        WHEN LAG(ms.monthly_sales) OVER (
            PARTITION BY ms.store_id ORDER BY ms.yr, ms.mo
        ) > 0
        THEN ROUND(((ms.monthly_sales - LAG(ms.monthly_sales) OVER (
            PARTITION BY ms.store_id ORDER BY ms.yr, ms.mo
        )) / LAG(ms.monthly_sales) OVER (
            PARTITION BY ms.store_id ORDER BY ms.yr, ms.mo
        ) * 100)::NUMERIC, 2)
        ELSE NULL
    END                                                 AS sales_change_pct
FROM current_period cp
INNER JOIN stores s ON cp.store_id = s.store_id
INNER JOIN monthly_store_sales ms ON cp.store_id = ms.store_id
ORDER BY
    rank;


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║ QUERY 11: Margen bruto por producto (revenue - cost)                      ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝
-- Purpose:  Calculate gross profit and margin percentage per product.
--           Identifies the most and least profitable products for pricing
--           and assortment decisions.
-- Features: Arithmetic operations, CASE for margin tier classification,
--           aggregate functions, ROUND, NULLIF
-- Output:   product_name, category_name, total_revenue, total_cost, gross_profit, profit_margin_pct, margin_tier

SELECT
    p.name                                              AS product_name,
    cat.name                                            AS category_name,
    SUM(oi.line_total)::NUMERIC(14, 2)                  AS total_revenue,
    SUM(p.cost_price * oi.quantity)::NUMERIC(14, 2)     AS total_cost,
    (SUM(oi.line_total) - SUM(p.cost_price * oi.quantity))::NUMERIC(14, 2) AS gross_profit,
    ROUND(
        ((SUM(oi.line_total) - SUM(p.cost_price * oi.quantity)) /
         NULLIF(SUM(oi.line_total), 0) * 100)::NUMERIC, 2
    )                                                   AS profit_margin_pct,
    CASE
        WHEN (SUM(oi.line_total) - SUM(p.cost_price * oi.quantity)) /
             NULLIF(SUM(oi.line_total), 0) * 100 >= 40  THEN 'High Margin'
        WHEN (SUM(oi.line_total) - SUM(p.cost_price * oi.quantity)) /
             NULLIF(SUM(oi.line_total), 0) * 100 >= 20  THEN 'Medium Margin'
        ELSE 'Low Margin'
    END                                                 AS margin_tier
FROM products p
INNER JOIN categories cat ON p.category_id = cat.category_id
INNER JOIN order_items oi ON p.product_id  = oi.product_id
INNER JOIN orders o       ON oi.order_id   = o.order_id
WHERE o.status NOT IN ('cancelled')
GROUP BY
    p.product_id,
    p.name,
    cat.name
ORDER BY
    gross_profit DESC;


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║ QUERY 12: Margen bruto por categoría                                      ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝
-- Purpose:  Aggregate profit metrics at the category level for strategic
--           category management. Identifies which categories drive the most
--           absolute and relative profit.
-- Features: CTE for product-level aggregation, outer query for category rollup,
--           RANK window function, CASE for margin tier
-- Output:   category_name, total_revenue, total_cost, gross_profit, profit_margin_pct, margin_tier, num_products, rank

WITH product_profits AS (
    SELECT
        cat.category_id,
        cat.name                                        AS category_name,
        p.product_id,
        SUM(oi.line_total)                              AS revenue,
        SUM(p.cost_price * oi.quantity)                 AS cost
    FROM products p
    INNER JOIN categories cat ON p.category_id = cat.category_id
    INNER JOIN order_items oi ON p.product_id  = oi.product_id
    INNER JOIN orders o       ON oi.order_id   = o.order_id
    WHERE o.status NOT IN ('cancelled')
    GROUP BY cat.category_id, cat.name, p.product_id
)
SELECT
    category_name,
    SUM(revenue)::NUMERIC(14, 2)                        AS total_revenue,
    SUM(cost)::NUMERIC(14, 2)                           AS total_cost,
    (SUM(revenue) - SUM(cost))::NUMERIC(14, 2)          AS gross_profit,
    ROUND(
        ((SUM(revenue) - SUM(cost)) / NULLIF(SUM(revenue), 0) * 100)::NUMERIC, 2
    )                                                   AS profit_margin_pct,
    CASE
        WHEN (SUM(revenue) - SUM(cost)) / NULLIF(SUM(revenue), 0) * 100 >= 40
            THEN 'High Margin'
        WHEN (SUM(revenue) - SUM(cost)) / NULLIF(SUM(revenue), 0) * 100 >= 20
            THEN 'Medium Margin'
        ELSE 'Low Margin'
    END                                                 AS margin_tier,
    COUNT(product_id)                                   AS num_products,
    RANK() OVER (ORDER BY (SUM(revenue) - SUM(cost)) DESC) AS rank
FROM product_profits
GROUP BY
    category_id,
    category_name
ORDER BY
    gross_profit DESC;


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║ QUERY 13: Clientes recurrentes (more than 1 order)                        ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝
-- Purpose:  Identify and analyze repeat customers. Measures customer loyalty
--           and retention. Compares spending between repeat and one-time buyers.
-- Features: HAVING clause, CTE, CASE, aggregate functions,
--           subquery for comparison metrics
-- Output:   customer_id, full_name, num_orders, total_spent, avg_days_between_orders, customer_segment

WITH repeat_customers AS (
    SELECT
        c.customer_id,
        c.first_name || ' ' || c.last_name              AS full_name,
        COUNT(o.order_id)                               AS num_orders,
        SUM(o.total_amount)                             AS total_spent,
        AVG(
            EXTRACT(EPOCH FROM (
                o.order_date - LAG(o.order_date) OVER (
                    PARTITION BY o.customer_id ORDER BY o.order_date
                )
            )) / 86400
        )                                               AS avg_days_between_orders
    FROM customers c
    INNER JOIN orders o ON c.customer_id = o.customer_id
    WHERE o.status NOT IN ('cancelled')
    GROUP BY
        c.customer_id,
        c.first_name,
        c.last_name
    HAVING COUNT(o.order_id) > 1
)
SELECT
    rc.customer_id,
    rc.full_name,
    rc.num_orders,
    rc.total_spent::NUMERIC(14, 2),
    ROUND(rc.avg_days_between_orders::NUMERIC, 1)       AS avg_days_between_orders,
    CASE
        WHEN rc.num_orders >= 10  THEN 'Platinum'
        WHEN rc.num_orders >= 5   THEN 'Gold'
        WHEN rc.num_orders >= 3   THEN 'Silver'
        ELSE 'Bronze'
    END                                                 AS customer_segment,
    ROUND(
        (rc.total_spent / NULLIF(rc.num_orders, 0))::NUMERIC, 2
    )                                                   AS avg_ticket
FROM repeat_customers rc
ORDER BY
    rc.total_spent DESC;


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║ QUERY 14: Crecimiento mensual de ventas (LAG window function)             ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝
-- Purpose:  Calculate month-over-month sales growth rate. Essential for
--           tracking business momentum and identifying acceleration or slowdown.
-- Features: LAG window function, CTE, arithmetic with window results,
--           ROUND, NULLIF, ORDER BY
-- Output:   year, month, total_sales, prev_month_sales, absolute_change, growth_rate_pct, trend

WITH monthly_sales AS (
    SELECT
        EXTRACT(YEAR FROM o.order_date)::INTEGER        AS yr,
        EXTRACT(MONTH FROM o.order_date)::INTEGER       AS mo,
        SUM(o.total_amount)                             AS total_sales,
        COUNT(DISTINCT o.order_id)                      AS num_orders
    FROM orders o
    WHERE o.status NOT IN ('cancelled')
    GROUP BY yr, mo
)
SELECT
    yr                                                  AS year,
    mo                                                  AS month,
    total_sales::NUMERIC(14, 2),
    LAG(total_sales) OVER (ORDER BY yr, mo)::NUMERIC(14, 2)    AS prev_month_sales,
    (total_sales - LAG(total_sales) OVER (ORDER BY yr, mo))::NUMERIC(14, 2) AS absolute_change,
    ROUND(
        ((total_sales - LAG(total_sales) OVER (ORDER BY yr, mo)) /
         NULLIF(LAG(total_sales) OVER (ORDER BY yr, mo), 0) * 100)::NUMERIC, 2
    )                                                   AS growth_rate_pct,
    CASE
        WHEN total_sales > LAG(total_sales) OVER (ORDER BY yr, mo) THEN '↑ Growth'
        WHEN total_sales < LAG(total_sales) OVER (ORDER BY yr, mo) THEN '↓ Decline'
        ELSE '→ Flat'
    END                                                 AS trend
FROM monthly_sales
ORDER BY
    yr DESC, mo DESC;


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║ QUERY 15: Porcentaje de participación por categoría                        ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝
-- Purpose:  Calculate each category's share of total sales as a percentage.
--           Reveals concentration risk and category dependency.
-- Features: Window function (SUM() OVER), CTE, ROUND, cumulative percentage,
--           RANK, CASE for concentration level
-- Output:   category_name, total_sales, pct_of_total, cumulative_pct, rank, concentration_level

WITH category_totals AS (
    SELECT
        cat.name                                        AS category_name,
        SUM(oi.line_total)                              AS total_sales
    FROM categories cat
    INNER JOIN products p     ON cat.category_id = p.category_id
    INNER JOIN order_items oi ON p.product_id    = oi.product_id
    INNER JOIN orders o       ON oi.order_id     = o.order_id
    WHERE o.status NOT IN ('cancelled')
    GROUP BY cat.category_id, cat.name
),
total_revenue AS (
    SELECT SUM(total_sales) AS grand_total FROM category_totals
)
SELECT
    ct.category_name,
    ct.total_sales::NUMERIC(14, 2),
    ROUND((ct.total_sales / tr.grand_total * 100)::NUMERIC, 2) AS pct_of_total,
    ROUND(
        (SUM(ct.total_sales) OVER (ORDER BY ct.total_sales DESC) / tr.grand_total * 100)::NUMERIC, 2
    )                                                   AS cumulative_pct,
    RANK() OVER (ORDER BY ct.total_sales DESC)          AS rank,
    CASE
        WHEN (SUM(ct.total_sales) OVER (ORDER BY ct.total_sales DESC) / tr.grand_total * 100) <= 50
            AND RANK() OVER (ORDER BY ct.total_sales DESC) = 1
        THEN 'Dominant'
        WHEN ct.total_sales / tr.grand_total * 100 >= 15 THEN 'Major'
        WHEN ct.total_sales / tr.grand_total * 100 >= 5  THEN 'Medium'
        ELSE 'Niche'
    END                                                 AS concentration_level
FROM category_totals ct
CROSS JOIN total_revenue tr
ORDER BY
    ct.total_sales DESC;


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║ QUERY 16: Productos con caída de ventas (compare current vs previous month ║
-- ║          using LAG)                                                       ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝
-- Purpose:  Detect products whose sales have dropped compared to the previous
--           month. Early warning for demand shifts, competitive threats, or
--           seasonal decline. Enables proactive merchandising response.
-- Features: Multiple CTEs, LAG window function with PARTITION BY,
--           CASE for severity classification, NULLIF, ROUND
-- Output:   product_name, category_name, current_month, current_sales, prev_month_sales, sales_change, change_pct, severity

WITH monthly_product_sales AS (
    SELECT
        p.product_id,
        p.name                                            AS product_name,
        cat.name                                          AS category_name,
        EXTRACT(YEAR FROM o.order_date)::INTEGER          AS yr,
        EXTRACT(MONTH FROM o.order_date)::INTEGER         AS mo,
        SUM(oi.line_total)                                AS monthly_sales,
        SUM(oi.quantity)                                  AS monthly_units
    FROM products p
    INNER JOIN categories cat ON p.category_id = cat.category_id
    INNER JOIN order_items oi ON p.product_id  = oi.product_id
    INNER JOIN orders o       ON oi.order_id   = o.order_id
    WHERE o.status NOT IN ('cancelled')
    GROUP BY p.product_id, p.name, cat.name, yr, mo
),
with_prev_month AS (
    SELECT
        product_id,
        product_name,
        category_name,
        yr,
        mo,
        monthly_sales,
        LAG(monthly_sales) OVER (
            PARTITION BY product_id ORDER BY yr, mo
        )                                                 AS prev_month_sales,
        monthly_units,
        LAG(monthly_units) OVER (
            PARTITION BY product_id ORDER BY yr, mo
        )                                                 AS prev_month_units
    FROM monthly_product_sales
)
SELECT
    product_name,
    category_name,
    TO_CHAR(DATE (yr || '-' || mo || '-01'), 'YYYY-MM')  AS current_month,
    monthly_sales::NUMERIC(14, 2)                         AS current_sales,
    prev_month_sales::NUMERIC(14, 2),
    (monthly_sales - prev_month_sales)::NUMERIC(14, 2)    AS sales_change,
    ROUND(
        ((monthly_sales - prev_month_sales) / NULLIF(prev_month_sales, 0) * 100)::NUMERIC, 2
    )                                                     AS change_pct,
    CASE
        WHEN prev_month_sales > 0 AND (monthly_sales - prev_month_sales) / prev_month_sales * 100 <= -50
            THEN 'CRITICAL - Severe drop'
        WHEN prev_month_sales > 0 AND (monthly_sales - prev_month_sales) / prev_month_sales * 100 <= -25
            THEN 'WARNING - Significant drop'
        WHEN prev_month_sales > 0 AND (monthly_sales - prev_month_sales) / prev_month_sales * 100 < 0
            THEN 'MILD - Slight decline'
        ELSE 'No decline'
    END                                                   AS severity
FROM with_prev_month
WHERE prev_month_sales IS NOT NULL
    AND monthly_sales < prev_month_sales
ORDER BY
    change_pct ASC;


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║ QUERY 17: Órdenes pendientes de envío (LEFT JOIN shipments)               ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝
-- Purpose:  Find confirmed/processing orders that have not yet been shipped.
--           Critical for fulfillment pipeline monitoring and SLA tracking.
-- Features: LEFT JOIN + IS NULL pattern, IN clause, EXTRACT for time elapsed,
--           CASE for SLA status, date arithmetic
-- Output:   order_id, customer_name, order_date, total_amount, days_waiting, order_status, sla_status

SELECT
    o.order_id,
    c.first_name || ' ' || c.last_name                  AS customer_name,
    o.order_date,
    o.total_amount::NUMERIC(14, 2),
    EXTRACT(DAY FROM (CURRENT_TIMESTAMP - o.order_date))::INTEGER AS days_waiting,
    o.status                                            AS order_status,
    CASE
        WHEN o.status IN ('confirmed', 'processing')
            AND EXTRACT(DAY FROM (CURRENT_TIMESTAMP - o.order_date)) >= 5
            THEN 'BREACHED'
        WHEN o.status IN ('confirmed', 'processing')
            AND EXTRACT(DAY FROM (CURRENT_TIMESTAMP - o.order_date)) >= 3
            THEN 'AT RISK'
        ELSE 'WITHIN SLA'
    END                                                 AS sla_status
FROM orders o
INNER JOIN customers c ON o.customer_id = c.customer_id
LEFT JOIN shipments s  ON o.order_id    = s.order_id
WHERE s.shipment_id IS NULL
    AND o.status IN ('confirmed', 'processing')
ORDER BY
    days_waiting DESC;


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║ QUERY 18: Métodos de pago más usados                                      ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝
-- Purpose:  Analyze payment method distribution and performance. Identifies
--           preferred payment channels, failure rates, and average transaction
--           sizes per method. Supports payment gateway optimization.
-- Features: GROUP BY, aggregate functions, CASE, window function (RANK),
--           ROUND, NULLIF, subquery for total percentage
-- Output:   payment_method, num_payments, total_amount, avg_amount, pct_of_total, failed_count, failure_rate_pct, rank

SELECT
    p.payment_method,
    COUNT(p.payment_id)                                 AS num_payments,
    SUM(p.amount)::NUMERIC(14, 2)                       AS total_amount,
    ROUND(AVG(p.amount)::NUMERIC, 2)                    AS avg_amount,
    ROUND(
        (SUM(CASE WHEN p.status = 'completed' THEN p.amount ELSE 0 END) /
         NULLIF(
            (SELECT SUM(p2.amount) FROM payments p2 WHERE p2.status = 'completed'),
            0
         ) * 100)::NUMERIC, 2
    )                                                   AS pct_of_total,
    SUM(CASE WHEN p.status = 'failed' THEN 1 ELSE 0 END) AS failed_count,
    ROUND(
        (SUM(CASE WHEN p.status = 'failed' THEN 1 ELSE 0 END)::NUMERIC /
         NULLIF(COUNT(p.payment_id), 0) * 100)::NUMERIC, 2
    )                                                   AS failure_rate_pct,
    RANK() OVER (ORDER BY SUM(p.amount) DESC)           AS rank
FROM payments p
GROUP BY p.payment_method
ORDER BY
    total_amount DESC;


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║ QUERY 19: Promedio de días de entrega (EXTRACT epoch difference)          ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝
-- Purpose:  Calculate average delivery time from order placement to delivery.
--           Breaks down by carrier, shipping method, and store for logistics
--           optimization and carrier performance evaluation.
-- Features: EXTRACT(EPOCH), date arithmetic, CTE, multiple GROUP BY levels,
--           CASE for performance rating, window function (RANK)
-- Output:   carrier, shipping_method, avg_delivery_days, min_days, max_days, num_deliveries, performance_rating, rank

WITH delivery_times AS (
    SELECT
        s.carrier,
        s.shipping_method,
        o.store_id,
        EXTRACT(EPOCH FROM (s.delivered_at - o.order_date)) / 86400 AS delivery_days
    FROM shipments s
    INNER JOIN orders o ON s.order_id = o.order_id
    WHERE s.status = 'delivered'
        AND s.delivered_at IS NOT NULL
        AND o.order_date IS NOT NULL
)
SELECT
    dt.carrier,
    dt.shipping_method,
    ROUND(AVG(dt.delivery_days)::NUMERIC, 1)            AS avg_delivery_days,
    ROUND(MIN(dt.delivery_days)::NUMERIC, 1)            AS min_days,
    ROUND(MAX(dt.delivery_days)::NUMERIC, 1)            AS max_days,
    COUNT(*)                                            AS num_deliveries,
    CASE
        WHEN AVG(dt.delivery_days) <= 2  THEN 'Excellent'
        WHEN AVG(dt.delivery_days) <= 5  THEN 'Good'
        WHEN AVG(dt.delivery_days) <= 7  THEN 'Acceptable'
        ELSE 'Poor'
    END                                                 AS performance_rating,
    RANK() OVER (ORDER BY AVG(dt.delivery_days) ASC)    AS rank
FROM delivery_times dt
GROUP BY
    dt.carrier,
    dt.shipping_method
ORDER BY
    avg_delivery_days ASC;


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║ QUERY 20: Cohorte simple de clientes por mes de primera compra             ║
-- ║           (CTE + GROUP BY)                                                ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝
-- Purpose:  Build a customer cohort analysis grouped by the month of their
--           first purchase. For each cohort, track how many customers placed
--           orders in subsequent months (retention). This is a fundamental
--           SaaS/e-commerce analytics technique for measuring customer lifetime
--           and retention health.
-- Features: Multiple CTEs, window function (MIN OVER), date truncation,
--           EXTRACT, GROUP BY with multi-level aggregation, CASE for cohort size,
--           EXTRACT epoch for month difference calculation
-- Output:   cohort_month, cohort_size, activity_month, months_since_first, active_customers, retention_pct, cohort_tier

WITH first_purchases AS (
    -- Step 1: Find each customer's first order date
    SELECT
        o.customer_id,
        MIN(o.order_date)                               AS first_order_date
    FROM orders o
    WHERE o.status NOT IN ('cancelled')
    GROUP BY o.customer_id
),
cohort_months AS (
    -- Step 2: Define cohort by first purchase month
    SELECT
        customer_id,
        first_order_date,
        DATE_TRUNC('month', first_order_date)::DATE     AS cohort_month
    FROM first_purchases
),
customer_activity AS (
    -- Step 3: Track all order months per customer
    SELECT
        o.customer_id,
        DATE_TRUNC('month', o.order_date)::DATE         AS activity_month
    FROM orders o
    WHERE o.status NOT IN ('cancelled')
    GROUP BY o.customer_id, activity_month
),
cohort_activity AS (
    -- Step 4: Join cohorts with activity, compute month offset
    SELECT
        cm.cohort_month,
        ca.activity_month,
        cm.customer_id,
        EXTRACT(YEAR FROM ca.activity_month)::INTEGER * 12 +
            EXTRACT(MONTH FROM ca.activity_month)::INTEGER
        -
        (EXTRACT(YEAR FROM cm.cohort_month)::INTEGER * 12 +
            EXTRACT(MONTH FROM cm.cohort_month)::INTEGER)
                                                        AS months_since_first
    FROM cohort_months cm
    INNER JOIN customer_activity ca ON cm.customer_id = ca.customer_id
),
cohort_sizes AS (
    -- Step 5: Count customers in each cohort
    SELECT
        cohort_month,
        COUNT(DISTINCT customer_id)                     AS cohort_size
    FROM cohort_months
    GROUP BY cohort_month
)
-- Step 6: Final aggregation with retention calculation
SELECT
    cs.cohort_month::TEXT                                AS cohort_month,
    cs.cohort_size,
    ca.activity_month::TEXT                              AS activity_month,
    ca.months_since_first,
    COUNT(DISTINCT ca.customer_id)                      AS active_customers,
    ROUND(
        (COUNT(DISTINCT ca.customer_id)::NUMERIC / NULLIF(cs.cohort_size, 0) * 100)::NUMERIC, 1
    )                                                   AS retention_pct,
    CASE
        WHEN cs.cohort_size >= 100 THEN 'Large'
        WHEN cs.cohort_size >= 50  THEN 'Medium'
        WHEN cs.cohort_size >= 20  THEN 'Small'
        ELSE 'Micro'
    END                                                 AS cohort_tier
FROM cohort_activity ca
INNER JOIN cohort_sizes cs ON ca.cohort_month = cs.cohort_month
GROUP BY
    cs.cohort_month,
    cs.cohort_size,
    ca.activity_month,
    ca.months_since_first
ORDER BY
    cs.cohort_month DESC,
    ca.months_since_first ASC;


-- =============================================================================
-- END OF SHOWCASE QUERIES
-- =============================================================================
-- Total: 20 advanced queries
--
-- SQL Features Demonstrated:
--   ✓ CTEs (WITH clause)              - Queries 6, 10, 12, 14, 16, 20
--   ✓ Window Functions (LAG, RANK)    - Queries 1, 2, 10, 12, 14, 15, 16, 19
--   ✓ LEFT JOIN + IS NULL             - Queries 5, 7, 17
--   ✓ CASE expressions                - Queries 6, 8, 9, 11, 12, 13, 14, 16, 17, 19, 20
--   ✓ Subqueries                      - Queries 4, 5, 6, 18
--   ✓ Aggregate Functions (SUM, COUNT, AVG, MIN, MAX)  - All queries
--   ✓ HAVING clause                   - Query 13
--   ✓ EXTRACT / date functions        - Queries 3, 7, 10, 14, 16, 17, 19, 20
--   ✓ LATERAL JOIN                    - Query 6
--   ✓ CROSS JOIN                      - Query 15
--   ✓ COALESCE / NULLIF               - Multiple queries
--   ✓ Percentage calculations         - Queries 4, 5, 11, 12, 14, 15, 18, 20
--   ✓ Cumulative SUM (window)         - Query 15
--   ✓ Partial / conditional COUNT     - Queries 9, 18
--   ✓ Date arithmetic / EPOCH         - Queries 7, 13, 17, 19
--   ✓ ROLLUP-like totals              - Query 9
--   ✓ UNION ALL                       - Query 6
-- =============================================================================
