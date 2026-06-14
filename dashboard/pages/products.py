"""
TechStore Analytics — Products Page
=====================================
Product analysis: top sellers, margins, category breakdown.
Identifies star products, margin leaders, and products without sales.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.components.charts import (
    create_bar_chart,
    create_pie_chart,
    create_table,
)
from dashboard.data_loader import DataLoader


def render(loader: DataLoader, filters: dict | None = None) -> None:
    """Render the Products analysis page."""
    st.markdown("## 🛍️ Análisis de Productos")
    st.markdown(
        "Explora el rendimiento de productos: ventas, márgenes y categorías."
    )
    st.divider()

    products = loader.get_products()
    top_products = loader.get_top_products()
    cat_sales = loader.get_category_sales()
    order_items = loader.get_order_items()
    orders = loader.get_orders()

    # ------------------------------------------------------------------
    # Category filter (local, overrides sidebar)
    # ------------------------------------------------------------------
    selected_category = None
    if not products.empty and "category_name" in products.columns:
        categories = ["Todas"] + sorted(products["category_name"].dropna().unique().tolist())
        # Pre-select from sidebar filter if set
        default_idx = 0
        if filters and filters.get("category"):
            if filters["category"] in categories:
                default_idx = categories.index(filters["category"])
        selected_category = st.selectbox("🏷️ Filtrar por Categoría", categories, index=default_idx, key="product_cat_filter")

    # ------------------------------------------------------------------
    # Quick metrics
    # ------------------------------------------------------------------
    col1, col2, col3 = st.columns(3)
    total_products = len(products)

    # Products without sales
    products_with_sales = set()
    if not top_products.empty and "product_name" in top_products.columns:
        products_with_sales = set(top_products["product_name"].tolist())

    products_without_sales = 0
    if not products.empty and "name" in products.columns:
        products_without_sales = len(products[~products["name"].isin(products_with_sales)])

    # Average margin
    avg_margin = 0.0
    if not products.empty and "unit_price" in products.columns and "cost_price" in products.columns:
        products_copy = products.copy()
        products_copy["margin_pct"] = ((products_copy["unit_price"] - products_copy["cost_price"]) / products_copy["unit_price"] * 100)
        avg_margin = products_copy["margin_pct"].mean()

    col1.metric("Total Productos", f"{total_products:,}")
    col2.metric("Sin Ventas", f"{products_without_sales:,}")
    col3.metric("Margen Promedio", f"{avg_margin:.1f}%")

    st.divider()

    # ------------------------------------------------------------------
    # Apply category filter
    # ------------------------------------------------------------------
    filtered_top = top_products.copy()
    filtered_products = products.copy()
    if selected_category and selected_category != "Todas":
        if not top_products.empty and "category_name" in top_products.columns:
            filtered_top = top_products[top_products["category_name"] == selected_category]
        if not products.empty and "category_name" in products.columns:
            filtered_products = products[products["category_name"] == selected_category]

    # ------------------------------------------------------------------
    # Top Selling Products
    # ------------------------------------------------------------------
    if not filtered_top.empty:
        col1, col2 = st.columns(2)

        with col1:
            fig_top = create_bar_chart(
                filtered_top.head(15),
                x="product_name",
                y="revenue",
                title="🏆 Top Productos por Ingresos",
            )
            fig_top.update_layout(yaxis_tickprefix="$", yaxis_tickformat=",")
            st.plotly_chart(fig_top, use_container_width=True)

        with col2:
            fig_units = create_bar_chart(
                filtered_top.head(15),
                x="product_name",
                y="units_sold",
                title="📦 Top Productos por Unidades Vendidas",
            )
            st.plotly_chart(fig_units, use_container_width=True)

    # ------------------------------------------------------------------
    # Margin by Product (Top 15)
    # ------------------------------------------------------------------
    if not filtered_products.empty and "unit_price" in filtered_products.columns and "cost_price" in filtered_products.columns:
        margin_df = filtered_products.copy()
        margin_df["margin_pct"] = ((margin_df["unit_price"] - margin_df["cost_price"]) / margin_df["unit_price"] * 100)
        margin_df["margin_abs"] = margin_df["unit_price"] - margin_df["cost_price"]

        # Top 15 by margin %
        top_margin = margin_df.nlargest(15, "margin_pct")[["name", "category_name", "unit_price", "cost_price", "margin_pct", "margin_abs"]]

        col1, col2 = st.columns(2)

        with col1:
            fig_margin = create_bar_chart(
                top_margin,
                x="name",
                y="margin_pct",
                title="📊 Top 15 Productos por Margen (%)",
            )
            fig_margin.update_layout(yaxis_ticksuffix="%")
            st.plotly_chart(fig_margin, use_container_width=True)

        with col2:
            # Bottom 15 by margin % (lowest margin products)
            bottom_margin = margin_df.nsmallest(15, "margin_pct")[["name", "category_name", "unit_price", "cost_price", "margin_pct", "margin_abs"]]
            fig_low_margin = create_bar_chart(
                bottom_margin,
                x="name",
                y="margin_pct",
                title="📉 15 Productos con Menor Margen (%)",
            )
            fig_low_margin.update_layout(yaxis_ticksuffix="%")
            st.plotly_chart(fig_low_margin, use_container_width=True)

    # ------------------------------------------------------------------
    # Margin by Category
    # ------------------------------------------------------------------
    if not products.empty and "unit_price" in products.columns and "cost_price" in products.columns and "category_name" in products.columns:
        cat_margin = (
            products.groupby("category_name")
            .apply(lambda g: pd.Series({
                "avg_margin_pct": ((g["unit_price"] - g["cost_price"]) / g["unit_price"] * 100).mean(),
                "avg_price": g["unit_price"].mean(),
                "avg_cost": g["cost_price"].mean(),
                "num_products": len(g),
            }))
            .reset_index()
            .sort_values("avg_margin_pct", ascending=False)
        )

        col1, col2 = st.columns(2)

        with col1:
            fig_cat_margin = create_bar_chart(
                cat_margin,
                x="category_name",
                y="avg_margin_pct",
                title="📊 Margen Promedio por Categoría (%)",
            )
            fig_cat_margin.update_layout(yaxis_ticksuffix="%")
            st.plotly_chart(fig_cat_margin, use_container_width=True)

        with col2:
            fig_cat_price = create_bar_chart(
                cat_margin,
                x="category_name",
                y="avg_price",
                title="💲 Precio Promedio por Categoría",
            )
            fig_cat_price.update_layout(yaxis_tickprefix="$")
            st.plotly_chart(fig_cat_price, use_container_width=True)

    # ------------------------------------------------------------------
    # Products without sales
    # ------------------------------------------------------------------
    if not products.empty and "name" in products.columns and products_without_sales > 0:
        no_sales = products[~products["name"].isin(products_with_sales)]
        if not no_sales.empty:
            # Apply category filter
            if selected_category and selected_category != "Todas" and "category_name" in no_sales.columns:
                no_sales = no_sales[no_sales["category_name"] == selected_category]

            if not no_sales.empty:
                display_cols = [c for c in ["name", "sku", "category_name", "unit_price", "cost_price"] if c in no_sales.columns]
                create_table(no_sales[display_cols].head(20), title="🚫 Productos Sin Ventas")

    # ------------------------------------------------------------------
    # Full product ranking table
    # ------------------------------------------------------------------
    if not filtered_top.empty:
        create_table(filtered_top, title="📋 Ranking Completo de Productos")
