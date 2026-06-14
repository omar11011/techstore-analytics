"""
TechStore Analytics — Sales Page
==================================
Detailed sales analysis with charts and tables.
Includes monthly trends, category breakdown, store performance, and product rankings.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.components.charts import (
    create_bar_chart,
    create_line_chart,
    create_pie_chart,
    create_table,
)
from dashboard.data_loader import DataLoader


def render(loader: DataLoader, filters: dict | None = None) -> None:
    """Render the Sales analysis page."""
    st.markdown("## 💰 Análisis de Ventas")
    st.markdown(
        "Explora las ventas por período, categoría, sucursal y producto."
    )
    st.divider()

    # ------------------------------------------------------------------
    # Load data
    # ------------------------------------------------------------------
    orders = loader.get_orders()
    monthly = loader.get_monthly_sales()
    cat_sales = loader.get_category_sales()
    store_perf = loader.get_store_performance()
    top_products = loader.get_top_products()

    # ------------------------------------------------------------------
    # Apply date range filter
    # ------------------------------------------------------------------
    if not orders.empty and "order_date" in orders.columns:
        orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce", utc=True)
        orders = orders.dropna(subset=["order_date"])
        if filters and filters.get("date_range"):
            dr = filters["date_range"]
            start = pd.to_datetime(dr[0], utc=True)
            end = pd.to_datetime(dr[1], utc=True)
            orders = orders[
                (orders["order_date"] >= start)
                & (orders["order_date"] <= end)
            ]

    # ------------------------------------------------------------------
    # Quick sales metrics
    # ------------------------------------------------------------------
    valid_orders = orders[~orders["status"].isin(["cancelled"])] if not orders.empty and "status" in orders.columns else orders
    total_filtered_sales = float(valid_orders["total_amount"].sum()) if not valid_orders.empty and "total_amount" in valid_orders.columns else 0.0
    total_filtered_orders = len(valid_orders)
    avg_ticket_filtered = total_filtered_sales / total_filtered_orders if total_filtered_orders > 0 else 0.0

    col1, col2, col3 = st.columns(3)
    col1.metric("Ventas Filtradas", f"${total_filtered_sales:,.2f}")
    col2.metric("Órdenes Filtradas", f"{total_filtered_orders:,}")
    col3.metric("Ticket Promedio", f"${avg_ticket_filtered:,.2f}")

    st.divider()

    # ------------------------------------------------------------------
    # Monthly Sales Trend
    # ------------------------------------------------------------------
    if not monthly.empty:
        monthly = monthly.copy()
        monthly["period"] = monthly.apply(
            lambda r: f"{int(r['year'])}-{int(r['month']):02d}", axis=1
        )

        fig_line = create_line_chart(
            monthly,
            x="period",
            y="total_sales",
            title="📈 Evolución Mensual de Ventas",
        )
        fig_line.update_layout(yaxis_tickprefix="$", yaxis_tickformat=",")
        st.plotly_chart(fig_line, use_container_width=True)

    # ------------------------------------------------------------------
    # Sales by Category & Store
    # ------------------------------------------------------------------
    col1, col2 = st.columns(2)

    with col1:
        if not cat_sales.empty:
            # Apply category filter if set
            display_cat = cat_sales.copy()
            if filters and filters.get("category"):
                display_cat = cat_sales[cat_sales["category_name"] == filters["category"]]

            fig_cat = create_bar_chart(
                display_cat,
                x="category_name",
                y="total_sales",
                title="🏷️ Ventas por Categoría",
            )
            fig_cat.update_layout(yaxis_tickprefix="$", yaxis_tickformat=",")
            st.plotly_chart(fig_cat, use_container_width=True)

    with col2:
        if not store_perf.empty:
            # Apply store filter if set
            display_store = store_perf.copy()
            if filters and filters.get("store"):
                display_store = store_perf[store_perf["store_name"] == filters["store"]]

            fig_store = create_bar_chart(
                display_store,
                x="store_name",
                y="total_sales",
                title="🏪 Ventas por Sucursal",
            )
            fig_store.update_layout(yaxis_tickprefix="$", yaxis_tickformat=",")
            st.plotly_chart(fig_store, use_container_width=True)

    # ------------------------------------------------------------------
    # Category Distribution Pie Chart
    # ------------------------------------------------------------------
    if not cat_sales.empty:
        fig_pie = create_pie_chart(
            cat_sales,
            values="total_sales",
            names="category_name",
            title="🏷️ Distribución de Ventas por Categoría",
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # ------------------------------------------------------------------
    # Product Ranking Table
    # ------------------------------------------------------------------
    if not top_products.empty:
        # Apply category filter to products if set
        display_products = top_products.copy()
        if filters and filters.get("category") and "category_name" in display_products.columns:
            display_products = display_products[display_products["category_name"] == filters["category"]]

        create_table(display_products, title="📋 Ranking de Productos por Ingresos")

    # ------------------------------------------------------------------
    # Order Status Summary
    # ------------------------------------------------------------------
    if not orders.empty and "status" in orders.columns:
        st.markdown("#### 📊 Resumen por Estado de Orden")
        status_counts = orders["status"].value_counts().reset_index()
        status_counts.columns = ["Estado", "Cantidad"]
        status_counts["Porcentaje"] = (status_counts["Cantidad"] / status_counts["Cantidad"].sum() * 100).round(1)

        # Translate status labels
        status_labels = {
            "delivered": "Entregado",
            "shipped": "Enviado",
            "processing": "Procesando",
            "confirmed": "Confirmado",
            "pending": "Pendiente",
            "cancelled": "Cancelado",
        }
        status_counts["Estado"] = status_counts["Estado"].map(status_labels).fillna(status_counts["Estado"])

        create_table(status_counts, title=None)
