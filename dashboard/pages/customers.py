"""
TechStore Analytics — Customers Page
======================================
Customer analysis: top spenders, growth, geographic distribution.
Includes repeat customer metrics and country breakdown.
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
    """Render the Customers analysis page."""
    st.markdown("## 👥 Análisis de Clientes")
    st.markdown(
        "Conoce a tus clientes: gasto, crecimiento y distribución geográfica."
    )
    st.divider()

    customers = loader.get_customers()
    top_customers = loader.get_top_customers()
    orders = loader.get_orders()

    # ------------------------------------------------------------------
    # Apply date range filter to orders
    # ------------------------------------------------------------------
    if not orders.empty and "order_date" in orders.columns:
        orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce")
        if filters and filters.get("date_range"):
            dr = filters["date_range"]
            orders = orders[
                (orders["order_date"] >= pd.to_datetime(dr[0]))
                & (orders["order_date"] <= pd.to_datetime(dr[1]))
            ]

    # ------------------------------------------------------------------
    # Quick metrics
    # ------------------------------------------------------------------
    total_customers = len(customers)

    # Repeat customers (customers with > 1 order)
    repeat_count = 0
    repeat_pct = 0.0
    if not orders.empty and "customer_id" in orders.columns:
        valid_orders = orders[~orders["status"].isin(["cancelled"])] if "status" in orders.columns else orders
        order_counts = valid_orders.groupby("customer_id").size()
        repeat_count = int((order_counts > 1).sum())
        repeat_pct = (repeat_count / total_customers * 100) if total_customers > 0 else 0.0

    # Average spend per customer
    avg_spend = 0.0
    if not top_customers.empty and "total_spent" in top_customers.columns:
        avg_spend = float(top_customers["total_spent"].mean())

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de Clientes", f"{total_customers:,}")
    col2.metric("Clientes Recurrentes", f"{repeat_count:,}")
    col3.metric("Tasa de Recurrencia", f"{repeat_pct:.1f}%")
    col4.metric("Gasto Promedio", f"${avg_spend:,.2f}")

    st.divider()

    # ------------------------------------------------------------------
    # Customer Growth Chart
    # ------------------------------------------------------------------
    if not customers.empty and "created_at" in customers.columns:
        customers_copy = customers.copy()
        customers_copy["created_at"] = pd.to_datetime(customers_copy["created_at"], errors="coerce")
        customers_copy["month"] = customers_copy["created_at"].dt.to_period("M").astype(str)

        growth = (
            customers_copy.groupby("month")
            .size()
            .reset_index(name="new_customers")
        )
        growth["cumulative"] = growth["new_customers"].cumsum()

        if not growth.empty:
            col1, col2 = st.columns(2)

            with col1:
                fig_growth = create_line_chart(
                    growth,
                    x="month",
                    y="cumulative",
                    title="📈 Crecimiento Acumulado de Clientes",
                    line_color="#10b981",
                )
                fig_growth.update_layout(yaxis_tickformat=",")
                st.plotly_chart(fig_growth, use_container_width=True)

            with col2:
                fig_new = create_bar_chart(
                    growth,
                    x="month",
                    y="new_customers",
                    title="🆕 Nuevos Clientes por Mes",
                )
                st.plotly_chart(fig_new, use_container_width=True)

    # ------------------------------------------------------------------
    # Customers by Country
    # ------------------------------------------------------------------
    if not customers.empty and "country" in customers.columns:
        country_counts = (
            customers["country"]
            .value_counts()
            .reset_index()
        )
        country_counts.columns = ["country", "count"]

        col1, col2 = st.columns(2)

        with col1:
            fig_country = create_pie_chart(
                country_counts,
                values="count",
                names="country",
                title="🌍 Clientes por País",
            )
            st.plotly_chart(fig_country, use_container_width=True)

        with col2:
            fig_country_bar = create_bar_chart(
                country_counts.head(10),
                x="country",
                y="count",
                title="🌍 Top 10 Países por Clientes",
            )
            st.plotly_chart(fig_country_bar, use_container_width=True)

    # ------------------------------------------------------------------
    # Customers by City (top 15)
    # ------------------------------------------------------------------
    if not customers.empty and "city" in customers.columns:
        city_counts = (
            customers["city"]
            .value_counts()
            .head(15)
            .reset_index()
        )
        city_counts.columns = ["city", "count"]

        fig_city = create_bar_chart(
            city_counts,
            x="city",
            y="count",
            title="🏙️ Top 15 Ciudades por Clientes",
        )
        st.plotly_chart(fig_city, use_container_width=True)

    # ------------------------------------------------------------------
    # Top Customers Table
    # ------------------------------------------------------------------
    if not top_customers.empty:
        create_table(top_customers.head(20), title="🏆 Top 20 Clientes por Gasto")
