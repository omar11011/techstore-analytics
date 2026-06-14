"""
TechStore Analytics — SQL Showcase Page
=========================================
Display important SQL queries with syntax highlighting and descriptions.
Features at least 8 advanced queries demonstrating analytical capabilities.
"""

from __future__ import annotations

import streamlit as st

from dashboard.data_loader import DataLoader

# ---------------------------------------------------------------------------
# Query collection — 10 advanced SQL queries
# ---------------------------------------------------------------------------
QUERIES = [
    {
        "title": "1. Top 10 Productos Más Vendidos",
        "description": (
            "Identifica los 10 productos más vendidos por cantidad total. "
            "Fundamental para planificación de inventario, pronóstico de demanda "
            "y detección de productos estrella."
        ),
        "features": "JOIN, GROUP BY, ORDER BY, LIMIT, RANK() OVER, SUM, COUNT",
        "sql": """\
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
    p.product_id, p.name, cat.name
ORDER BY units_sold DESC
LIMIT 10;""",
    },
    {
        "title": "2. Clientes con Mayor Gasto Acumulado",
        "description": (
            "Ranking de clientes por gasto acumulado. Apoya la identificación de VIPs, "
            "niveles de programas de lealtad y campañas de marketing dirigidas."
        ),
        "features": "JOIN, GROUP BY, RANK() OVER, COALESCE, date arithmetic",
        "sql": """\
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
GROUP BY c.customer_id, c.first_name, c.last_name
ORDER BY total_spent DESC
LIMIT 20;""",
    },
    {
        "title": "3. Ventas Mensuales (Revenue by Month)",
        "description": (
            "Muestra la tendencia mensual de ingresos para reportes financieros "
            "y pronósticos. Identifica patrones estacionales y trayectorias de crecimiento."
        ),
        "features": "EXTRACT, TO_CHAR, GROUP BY con date truncation, NULLIF",
        "sql": """\
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
ORDER BY year DESC, month DESC;""",
    },
    {
        "title": "4. Ventas por Categoría con Porcentaje",
        "description": (
            "Analiza la distribución de ingresos por categoría de producto. "
            "Incluye el porcentaje del total para entender la concentración de ventas."
        ),
        "features": "Multiple JOINs, GROUP BY, subquery para porcentaje",
        "sql": """\
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
GROUP BY cat.category_id, cat.name
ORDER BY total_sales DESC;""",
    },
    {
        "title": "5. Productos Sin Ventas (LEFT JOIN + IS NULL)",
        "description": (
            "Identifica productos que nunca se han vendido. Fundamental para "
            "detectar inventario muerto, limpieza de catálogo y decisiones de liquidación."
        ),
        "features": "LEFT JOIN + IS NULL, COALESCE, subquery",
        "sql": """\
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
ORDER BY days_since_creation DESC;""",
    },
    {
        "title": "6. Productos con Bajo Stock (inventory < 10)",
        "description": (
            "Encuentra productos con inventario bajo en todas las sucursales. "
            "Esencial para alertas automáticas de reabastecimiento y generación de órdenes de compra."
        ),
        "features": "JOIN, CASE expression, comparación aritmética",
        "sql": """\
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
ORDER BY i.stock_quantity ASC, p.name;""",
    },
    {
        "title": "7. Margen Bruto por Producto",
        "description": (
            "Calcula la ganancia bruta y el porcentaje de margen por producto. "
            "Identifica los productos más y menos rentables para decisiones de "
            "precios y surtido."
        ),
        "features": "Operaciones aritméticas, CASE para clasificación de margen, NULLIF",
        "sql": """\
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
GROUP BY p.product_id, p.name, cat.name
ORDER BY gross_profit DESC;""",
    },
    {
        "title": "8. Margen Bruto por Categoría (CTE)",
        "description": (
            "Agrega métricas de ganancia a nivel de categoría usando CTE. "
            "Identifica qué categorías generan mayor ganancia absoluta y relativa."
        ),
        "features": "CTE, RANK() OVER, CASE para tier de margen, aggregate rollup",
        "sql": """\
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
GROUP BY category_id, category_name
ORDER BY gross_profit DESC;""",
    },
    {
        "title": "9. Clientes Recurrentes (HAVING + CTE)",
        "description": (
            "Identifica y analiza clientes recurrentes. Mide la lealtad y retención. "
            "Compara el gasto entre compradores recurrentes y de una sola vez."
        ),
        "features": "HAVING clause, CTE, CASE, LAG() OVER, segmentación",
        "sql": """\
WITH repeat_customers AS (
    SELECT
        c.customer_id,
        c.first_name || ' ' || c.last_name              AS full_name,
        COUNT(o.order_id)                               AS num_orders,
        SUM(o.total_amount)                             AS total_spent
    FROM customers c
    INNER JOIN orders o ON c.customer_id = o.customer_id
    WHERE o.status NOT IN ('cancelled')
    GROUP BY c.customer_id, c.first_name, c.last_name
    HAVING COUNT(o.order_id) > 1
)
SELECT
    rc.customer_id,
    rc.full_name,
    rc.num_orders,
    rc.total_spent::NUMERIC(14, 2),
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
ORDER BY rc.total_spent DESC;""",
    },
    {
        "title": "10. Inventario por Tienda con Valoración",
        "description": (
            "Proporciona una visión completa del inventario por sucursal con valor de stock. "
            "Apoya la valoración de inventario, planificación de transferencias y auditoría."
        ),
        "features": "Multiple JOINs, CASE, SUM con expresión, GROUP BY",
        "sql": """\
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
WHERE s.is_active = TRUE AND p.is_active = TRUE
GROUP BY s.store_id, s.name, s.city
ORDER BY inventory_value DESC;""",
    },
]


def render(loader: DataLoader, filters: dict | None = None) -> None:
    """Render the SQL Showcase page."""
    st.markdown("## 🗄️ Escaparate SQL")
    st.markdown(
        "Colección de consultas SQL avanzadas que demuestran las capacidades "
        "analíticas de TechStore. Cada query incluye su propósito, "
        "características SQL utilizadas y el código completo."
    )
    st.divider()

    # ------------------------------------------------------------------
    # Query selector
    # ------------------------------------------------------------------
    query_titles = [q["title"] for q in QUERIES]
    selected_title = st.selectbox(
        "🔍 Selecciona una consulta",
        query_titles,
        index=0,
    )

    selected = next(q for q in QUERIES if q["title"] == selected_title)

    # ------------------------------------------------------------------
    # Query info cards
    # ------------------------------------------------------------------
    st.markdown(f"### {selected['title']}")

    col1, col2 = st.columns([3, 2])
    with col1:
        with st.expander("📝 Propósito", expanded=True):
            st.markdown(selected["description"])

    with col2:
        with st.expander("🔧 Características SQL", expanded=True):
            st.markdown(f"**{selected['features']}**")

    # ------------------------------------------------------------------
    # SQL code with syntax highlighting
    # ------------------------------------------------------------------
    st.markdown("#### 💻 Código SQL")
    st.code(selected["sql"], language="sql")

    # ------------------------------------------------------------------
    # Copy hint
    # ------------------------------------------------------------------
    st.info("💡 Puedes copiar el código haciendo clic en el ícono de copiar en la esquina superior derecha del bloque de código.")

    st.divider()

    # ------------------------------------------------------------------
    # All queries overview
    # ------------------------------------------------------------------
    with st.expander("📚 Ver todas las consultas", expanded=False):
        for q in QUERIES:
            st.markdown(f"#### {q['title']}")
            st.markdown(q["description"])
            st.code(q["sql"], language="sql")
            st.divider()
