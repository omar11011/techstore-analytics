"""
TechStore Analytics — Executive Summary Page
==============================================
High-level KPIs, monthly trends, category mix, top products & customers.
This is the main landing page of the dashboard.
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
from dashboard.components.kpi_cards import render_kpi_row
from dashboard.data_loader import DataLoader


def _apply_filters_to_orders(orders: pd.DataFrame, filters: dict | None) -> pd.DataFrame:
    """Apply sidebar filters to the orders DataFrame."""
    if not filters or orders.empty:
        return orders

    filtered = orders.copy()

    if "order_date" in filtered.columns:
        filtered["order_date"] = pd.to_datetime(filtered["order_date"], errors="coerce")
        if filters.get("date_range"):
            dr = filters["date_range"]
            filtered = filtered[
                (filtered["order_date"] >= pd.to_datetime(dr[0]))
                & (filtered["order_date"] <= pd.to_datetime(dr[1]))
            ]

    if filters.get("store") and "store_id" in filtered.columns:
        # Store filter is by name; need store_id mapping
        pass  # Handled at page level with store DataFrames

    return filtered


def render(loader: DataLoader, filters: dict | None = None) -> None:
    """Render the Executive Summary page."""
    st.markdown("## 📊 Resumen Ejecutivo")
    st.markdown(
        "Vista general del rendimiento de TechStore con indicadores clave, "
        "tendencias de ventas y análisis de categorías."
    )
    st.divider()

    # ------------------------------------------------------------------
    # KPI Row
    # ------------------------------------------------------------------
    summary = loader.get_dashboard_summary()
    kpi_metrics = [
        {"label": "Ventas Totales", "value": summary.get("total_sales", 0), "prefix": "$", "is_percentage": False},
        {"label": "Órdenes", "value": summary.get("num_orders", 0), "prefix": "", "is_percentage": False},
        {"label": "Clientes", "value": summary.get("num_customers", 0), "prefix": "", "is_percentage": False},
        {"label": "Productos", "value": summary.get("num_products", 0), "prefix": "", "is_percentage": False},
        {"label": "Ticket Promedio", "value": summary.get("avg_ticket", 0), "prefix": "$", "is_percentage": False},
        {"label": "Margen Bruto", "value": summary.get("gross_margin", 0), "prefix": "", "is_percentage": True},
    ]
    render_kpi_row(kpi_metrics)
    st.divider()

    # ------------------------------------------------------------------
    # Monthly Sales Trend + Average Ticket
    # ------------------------------------------------------------------
    monthly = loader.get_monthly_sales()
    if not monthly.empty:
        monthly = monthly.copy()
        monthly["period"] = monthly.apply(
            lambda r: f"{int(r['year'])}-{int(r['month']):02d}", axis=1
        )

        col1, col2 = st.columns([3, 2])
        with col1:
            fig_line = create_line_chart(
                monthly,
                x="period",
                y="total_sales",
                title="📈 Tendencia de Ventas Mensuales",
            )
            fig_line.update_layout(yaxis_tickprefix="$", yaxis_tickformat=",")
            st.plotly_chart(fig_line, use_container_width=True)

        with col2:
            fig_ticket = create_bar_chart(
                monthly,
                x="period",
                y="avg_ticket",
                title="🎫 Ticket Promedio Mensual",
            )
            fig_ticket.update_layout(yaxis_tickprefix="$", yaxis_tickformat=",")
            st.plotly_chart(fig_ticket, use_container_width=True)

    # ------------------------------------------------------------------
    # Category Sales Pie & Top 5 Products Bar
    # ------------------------------------------------------------------
    cat_sales = loader.get_category_sales()
    top_products = loader.get_top_products()

    col3, col4 = st.columns(2)

    with col3:
        if not cat_sales.empty:
            fig_pie = create_pie_chart(
                cat_sales,
                values="total_sales",
                names="category_name",
                title="🏷️ Ventas por Categoría",
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    with col4:
        if not top_products.empty:
            top5 = top_products.head(5)
            fig_bar = create_bar_chart(
                top5,
                x="product_name",
                y="revenue",
                title="🏆 Top 5 Productos por Ingresos",
            )
            fig_bar.update_layout(yaxis_tickprefix="$", yaxis_tickformat=",")
            st.plotly_chart(fig_bar, use_container_width=True)

    # ------------------------------------------------------------------
    # Top Customers Table
    # ------------------------------------------------------------------
    top_customers = loader.get_top_customers()
    if not top_customers.empty:
        create_table(top_customers.head(10), title="👥 Top 10 Clientes por Gasto")
