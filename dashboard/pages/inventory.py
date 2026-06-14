"""
TechStore Analytics — Inventory Page
======================================
Inventory status: low stock, out of stock, distribution charts.
Monitors stock levels, identifies critical items, and analyzes distribution.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.components.charts import (
    CHART_COLORS,
    create_bar_chart,
    create_pie_chart,
    create_table,
)
from dashboard.data_loader import DataLoader


def render(loader: DataLoader, filters: dict | None = None) -> None:
    """Render the Inventory status page."""
    st.markdown("## 📦 Estado de Inventario")
    st.markdown(
        "Monitorea el nivel de stock, identifica productos con baja existencia "
        "y analiza la distribución por sucursal."
    )
    st.divider()

    inventory = loader.get_inventory_status()

    if inventory.empty:
        st.warning("No hay datos de inventario disponibles.")
        return

    # ------------------------------------------------------------------
    # Apply store filter
    # ------------------------------------------------------------------
    display_inv = inventory.copy()
    if filters and filters.get("store") and "store_name" in display_inv.columns:
        display_inv = display_inv[display_inv["store_name"] == filters["store"]]

    # ------------------------------------------------------------------
    # Quick metrics
    # ------------------------------------------------------------------
    total_items = len(display_inv)
    out_of_stock = int((display_inv["status"] == "out_of_stock").sum()) if "status" in display_inv.columns else 0
    low_stock = int((display_inv["status"] == "low_stock").sum()) if "status" in display_inv.columns else 0
    normal_stock = int((display_inv["status"] == "normal").sum()) if "status" in display_inv.columns else 0
    overstocked = int((display_inv["status"] == "overstocked").sum()) if "status" in display_inv.columns else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Registros", f"{total_items:,}")
    col2.metric("🔴 Sin Stock", f"{out_of_stock:,}")
    col3.metric("🟡 Stock Bajo", f"{low_stock:,}")
    col4.metric("🟢 Normal", f"{normal_stock:,}")
    col5.metric("🔵 Sobre-stock", f"{overstocked:,}")

    st.divider()

    # ------------------------------------------------------------------
    # Inventory Status Distribution
    # ------------------------------------------------------------------
    if "status" in display_inv.columns:
        status_counts = display_inv["status"].value_counts().reset_index()
        status_counts.columns = ["status", "count"]

        status_labels = {
            "out_of_stock": "Sin Stock",
            "low_stock": "Stock Bajo",
            "normal": "Normal",
            "overstocked": "Sobre-stock",
        }
        status_counts["status_label"] = status_counts["status"].map(status_labels).fillna(status_counts["status"])

        col1, col2 = st.columns(2)

        with col1:
            fig_status = create_pie_chart(
                status_counts,
                values="count",
                names="status_label",
                title="📊 Distribución del Estado de Inventario",
            )
            st.plotly_chart(fig_status, use_container_width=True)

        with col2:
            fig_status_bar = create_bar_chart(
                status_counts,
                x="status_label",
                y="count",
                title="📊 Cantidad de Registros por Estado",
            )
            st.plotly_chart(fig_status_bar, use_container_width=True)

    # ------------------------------------------------------------------
    # Out of Stock Products
    # ------------------------------------------------------------------
    if "status" in display_inv.columns:
        out_stock = display_inv[display_inv["status"] == "out_of_stock"]
        if not out_stock.empty:
            st.markdown("### 🔴 Productos Sin Stock")
            st.error(f"⚠️ {len(out_stock)} productos sin stock requieren atención inmediata.")
            display_cols = [c for c in ["product_name", "store_name", "stock_quantity"] if c in out_stock.columns]
            create_table(out_stock[display_cols], title=None)
        else:
            st.success("✅ No hay productos sin stock.")

    # ------------------------------------------------------------------
    # Low Stock Products
    # ------------------------------------------------------------------
    if "status" in display_inv.columns:
        low_stock_df = display_inv[display_inv["status"] == "low_stock"]
        if not low_stock_df.empty:
            st.markdown("### 🟡 Productos con Stock Bajo")
            st.warning(f"⚠️ {len(low_stock_df)} productos con stock por debajo del punto de reorden.")
            display_cols = [c for c in ["product_name", "store_name", "stock_quantity", "reorder_level"] if c in low_stock_df.columns]
            create_table(low_stock_df[display_cols], title=None)

    # ------------------------------------------------------------------
    # Inventory by Store
    # ------------------------------------------------------------------
    if "store_name" in display_inv.columns and "stock_quantity" in display_inv.columns:
        store_inv = (
            display_inv.groupby("store_name")
            .agg(
                total_units=("stock_quantity", "sum"),
                num_products=("product_name", "count"),
                avg_stock=("stock_quantity", "mean"),
            )
            .reset_index()
            .sort_values("total_units", ascending=False)
        )

        col1, col2 = st.columns(2)

        with col1:
            fig_store = create_bar_chart(
                store_inv,
                x="store_name",
                y="total_units",
                title="🏪 Unidades Totales por Sucursal",
            )
            st.plotly_chart(fig_store, use_container_width=True)

        with col2:
            fig_avg = create_bar_chart(
                store_inv,
                x="store_name",
                y="avg_stock",
                title="🏪 Stock Promedio por Sucursal",
            )
            st.plotly_chart(fig_avg, use_container_width=True)

    # ------------------------------------------------------------------
    # Stock Distribution Histogram
    # ------------------------------------------------------------------
    if "stock_quantity" in display_inv.columns:
        fig_hist = px.histogram(
            display_inv,
            x="stock_quantity",
            nbins=30,
            title="📊 Distribución de Cantidades en Stock",
            color_discrete_sequence=[CHART_COLORS[0]],
        )
        fig_hist.update_traces(marker_line_width=0, marker_opacity=0.85)
        fig_hist.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, system-ui, sans-serif", size=13, color="#374151"),
            xaxis_title="Cantidad en Stock",
            yaxis_title="Número de Registros",
            title=dict(font=dict(size=18, color="#111827"), x=0.03, xanchor="left"),
        )
        fig_hist.update_xaxes(gridcolor="#f3f4f6", linecolor="#e5e7eb")
        fig_hist.update_yaxes(gridcolor="#f3f4f6", linecolor="#e5e7eb")
        st.plotly_chart(fig_hist, use_container_width=True)
