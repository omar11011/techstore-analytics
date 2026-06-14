"""
TechStore Analytics — Data Loader
===================================
Dual-mode data loader: PostgreSQL primary, CSV demo fallback.

Provides cached DataFrames for all dashboard pages with consistent
column naming across both modes.
"""

from __future__ import annotations

import logging
import os
import pathlib
from typing import Optional

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

_PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
_DEMO_DIR = _PROJECT_ROOT / "data" / "demo"

# ---------------------------------------------------------------------------
# Colour palette (used across charts)
# ---------------------------------------------------------------------------
CHART_COLORS = [
    "#2563eb",
    "#f59e0b",
    "#10b981",
    "#ef4444",
    "#8b5cf6",
    "#ec4899",
    "#06b6d4",
    "#f97316",
    "#6366f1",
    "#14b8a6",
]


class DataLoader:
    """Load data from PostgreSQL or fall back to demo CSVs."""

    def __init__(self) -> None:
        self._engine = None
        self._demo_mode = True
        self._init_connection()

    # ------------------------------------------------------------------
    # Connection helpers
    # ------------------------------------------------------------------
    def _init_connection(self) -> None:
        """Try PostgreSQL; silently fall back to CSV on any error."""
        try:
            from sqlalchemy import create_engine, text
        except ImportError:
            logger.info("SQLAlchemy not installed — CSV demo mode.")
            self._engine = None
            self._demo_mode = True
            return

        try:
            database_url: Optional[str] = None

            # 1. st.secrets
            try:
                db_secrets = st.secrets.get("database", {})
                if db_secrets:
                    database_url = db_secrets.get("url") or db_secrets.get("DATABASE_URL")
            except Exception:
                pass

            # 2. Environment variable
            if not database_url:
                database_url = os.environ.get("DATABASE_URL")

            if not database_url:
                logger.info("No DATABASE_URL found — using CSV demo mode.")
                return

            from sqlalchemy import create_engine, text

            engine = create_engine(database_url, pool_pre_ping=True, pool_size=5, max_overflow=10)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            self._engine = engine
            self._demo_mode = False
            logger.info("Connected to PostgreSQL successfully.")

        except Exception as exc:
            logger.warning("PostgreSQL connection failed (%s) — CSV demo mode.", exc)
            self._engine = None
            self._demo_mode = True

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------
    def is_demo_mode(self) -> bool:
        """Return True if using CSV demo data instead of PostgreSQL."""
        return self._demo_mode

    # ------------------------------------------------------------------
    # Core table loaders
    # ------------------------------------------------------------------
    @st.cache_data(ttl=600, show_spinner=False)
    def get_customers(_self) -> pd.DataFrame:
        """Load customers table."""
        if _self._demo_mode:
            df = _self._read_csv("customers.csv")
            # Normalize column names for consistency
            if "id" in df.columns and "customer_id" not in df.columns:
                df = df.rename(columns={"id": "customer_id"})
            return df
        return pd.read_sql("SELECT * FROM customers ORDER BY customer_id", _self._engine)

    @st.cache_data(ttl=600, show_spinner=False)
    def get_products(_self) -> pd.DataFrame:
        """Load products with category name."""
        if _self._demo_mode:
            df = _self._read_csv("products.csv")
            if "id" in df.columns and "product_id" not in df.columns:
                df = df.rename(columns={"id": "product_id"})
            # Normalize price/cost columns
            if "price" in df.columns and "unit_price" not in df.columns:
                df = df.rename(columns={"price": "unit_price"})
            if "cost" in df.columns and "cost_price" not in df.columns:
                df = df.rename(columns={"cost": "cost_price"})
            return df
        return pd.read_sql(
            """SELECT p.*, c.name AS category_name
               FROM products p
               JOIN categories c ON p.category_id = c.category_id
               ORDER BY p.product_id""",
            _self._engine,
        )

    @st.cache_data(ttl=600, show_spinner=False)
    def get_categories(_self) -> pd.DataFrame:
        """Load categories table."""
        if _self._demo_mode:
            df = _self._read_csv("categories.csv")
            if "id" in df.columns and "category_id" not in df.columns:
                df = df.rename(columns={"id": "category_id"})
            return df
        return pd.read_sql("SELECT * FROM categories ORDER BY category_id", _self._engine)

    @st.cache_data(ttl=600, show_spinner=False)
    def get_orders(_self) -> pd.DataFrame:
        """Load orders table."""
        if _self._demo_mode:
            df = _self._read_csv("orders.csv")
            if "id" in df.columns and "order_id" not in df.columns:
                df = df.rename(columns={"id": "order_id"})
            return df
        return pd.read_sql("SELECT * FROM orders ORDER BY order_id", _self._engine)

    @st.cache_data(ttl=600, show_spinner=False)
    def get_order_items(_self) -> pd.DataFrame:
        """Load order items, computing line_total if missing."""
        if _self._demo_mode:
            df = _self._read_csv("order_items.csv")
            if "id" in df.columns and "order_item_id" not in df.columns:
                df = df.rename(columns={"id": "order_item_id"})
            # Compute line_total if not present
            if "line_total" not in df.columns and "quantity" in df.columns and "unit_price" in df.columns:
                discount = df.get("discount", df.get("discount_pct", 0))
                df["line_total"] = df["quantity"] * df["unit_price"] * (1 - discount.fillna(0) / 100)
            return df
        return pd.read_sql("SELECT * FROM order_items ORDER BY order_item_id", _self._engine)

    @st.cache_data(ttl=600, show_spinner=False)
    def get_stores(_self) -> pd.DataFrame:
        """Load stores table."""
        if _self._demo_mode:
            df = _self._read_csv("stores.csv")
            if "id" in df.columns and "store_id" not in df.columns:
                df = df.rename(columns={"id": "store_id"})
            return df
        return pd.read_sql("SELECT * FROM stores ORDER BY store_id", _self._engine)

    # ------------------------------------------------------------------
    # Analytical views
    # ------------------------------------------------------------------
    @st.cache_data(ttl=600, show_spinner=False)
    def get_monthly_sales(_self) -> pd.DataFrame:
        """Monthly sales aggregation: year, month, total_sales, num_orders, avg_ticket."""
        if _self._demo_mode:
            return _self._read_csv("monthly_sales.csv")

        query = """
            SELECT
                EXTRACT(YEAR  FROM o.order_date)::INT  AS year,
                EXTRACT(MONTH FROM o.order_date)::INT  AS month,
                SUM(o.total_amount)::NUMERIC(14,2)     AS total_sales,
                COUNT(DISTINCT o.order_id)             AS num_orders,
                ROUND((SUM(o.total_amount) / NULLIF(COUNT(DISTINCT o.order_id),0))::NUMERIC, 2)
                                                    AS avg_ticket
            FROM orders o
            WHERE o.status NOT IN ('cancelled')
            GROUP BY EXTRACT(YEAR FROM o.order_date), EXTRACT(MONTH FROM o.order_date)
            ORDER BY year, month;
        """
        return pd.read_sql(query, _self._engine)

    @st.cache_data(ttl=600, show_spinner=False)
    def get_top_products(_self, limit: int = 20) -> pd.DataFrame:
        """Top products by revenue: product_name, category, units_sold, revenue."""
        if _self._demo_mode:
            df = _self._read_csv("top_products.csv")
            # Rename 'category' to 'category_name' for consistency
            if "category" in df.columns and "category_name" not in df.columns:
                df = df.rename(columns={"category": "category_name"})
            return df

        query = f"""
            SELECT
                p.name             AS product_name,
                cat.name           AS category_name,
                SUM(oi.quantity)   AS units_sold,
                SUM(oi.line_total)::NUMERIC(14,2) AS revenue
            FROM order_items oi
            JOIN products p   ON oi.product_id = p.product_id
            JOIN categories cat ON p.category_id = cat.category_id
            JOIN orders o     ON oi.order_id = o.order_id
            WHERE o.status NOT IN ('cancelled')
            GROUP BY p.product_id, p.name, cat.name
            ORDER BY revenue DESC
            LIMIT {limit};
        """
        return pd.read_sql(query, _self._engine)

    @st.cache_data(ttl=600, show_spinner=False)
    def get_top_customers(_self, limit: int = 20) -> pd.DataFrame:
        """Top customers by spend: customer_name, total_spent, num_orders."""
        if _self._demo_mode:
            return _self._read_csv("top_customers.csv")

        query = f"""
            SELECT
                (c.first_name || ' ' || c.last_name) AS customer_name,
                SUM(o.total_amount)::NUMERIC(14,2)   AS total_spent,
                COUNT(o.order_id)                     AS num_orders
            FROM customers c
            JOIN orders o ON c.customer_id = o.customer_id
            WHERE o.status NOT IN ('cancelled')
            GROUP BY c.customer_id, c.first_name, c.last_name
            ORDER BY total_spent DESC
            LIMIT {limit};
        """
        return pd.read_sql(query, _self._engine)

    @st.cache_data(ttl=600, show_spinner=False)
    def get_category_sales(_self) -> pd.DataFrame:
        """Sales by category: category_name, total_sales, num_products."""
        if _self._demo_mode:
            return _self._read_csv("category_sales.csv")

        query = """
            SELECT
                cat.name             AS category_name,
                SUM(oi.line_total)::NUMERIC(14,2) AS total_sales,
                COUNT(DISTINCT p.product_id)      AS num_products
            FROM categories cat
            JOIN products p      ON cat.category_id = p.category_id
            JOIN order_items oi  ON p.product_id = oi.product_id
            JOIN orders o        ON oi.order_id = o.order_id
            WHERE o.status NOT IN ('cancelled')
            GROUP BY cat.category_id, cat.name
            ORDER BY total_sales DESC;
        """
        return pd.read_sql(query, _self._engine)

    @st.cache_data(ttl=600, show_spinner=False)
    def get_inventory_status(_self) -> pd.DataFrame:
        """Inventory status: product_name, store_name, stock_quantity, reorder_level, status."""
        if _self._demo_mode:
            df = _self._read_csv("inventory_status.csv")
            # Demo CSV may not have reorder_level, compute status if missing
            if "reorder_level" not in df.columns:
                df["reorder_level"] = 10  # default reorder level
            if "status" not in df.columns and "stock_quantity" in df.columns:
                df["status"] = df["stock_quantity"].apply(
                    lambda q: "out_of_stock" if q == 0
                    else ("low_stock" if q <= 10
                    else ("overstocked" if q > 30 else "normal"))
                )
            return df

        query = """
            SELECT
                p.name              AS product_name,
                st.name             AS store_name,
                inv.stock_quantity,
                inv.reorder_level,
                CASE
                    WHEN inv.stock_quantity = 0 THEN 'out_of_stock'
                    WHEN inv.stock_quantity <= inv.reorder_level THEN 'low_stock'
                    WHEN inv.stock_quantity > inv.reorder_level * 3 THEN 'overstocked'
                    ELSE 'normal'
                END AS status
            FROM inventory inv
            JOIN products p  ON inv.product_id = p.product_id
            JOIN stores st   ON inv.store_id  = st.store_id
            ORDER BY inv.stock_quantity ASC;
        """
        return pd.read_sql(query, _self._engine)

    @st.cache_data(ttl=600, show_spinner=False)
    def get_store_performance(_self) -> pd.DataFrame:
        """Store performance: store_name, city, total_sales, num_orders."""
        if _self._demo_mode:
            return _self._read_csv("store_performance.csv")

        query = """
            SELECT
                st.name             AS store_name,
                st.city,
                SUM(o.total_amount)::NUMERIC(14,2) AS total_sales,
                COUNT(o.order_id)                  AS num_orders
            FROM stores st
            JOIN orders o ON st.store_id = o.store_id
            WHERE o.status NOT IN ('cancelled')
            GROUP BY st.store_id, st.name, st.city
            ORDER BY total_sales DESC;
        """
        return pd.read_sql(query, _self._engine)

    # ------------------------------------------------------------------
    # Dashboard summary (KPIs)
    # ------------------------------------------------------------------
    @st.cache_data(ttl=600, show_spinner=False)
    def get_dashboard_summary(_self) -> dict:
        """Compute key KPIs: total_sales, num_orders, num_customers, num_products, avg_ticket, gross_margin."""
        orders = _self.get_orders()
        products = _self.get_products()
        customers = _self.get_customers()
        order_items = _self.get_order_items()

        # Filter cancelled orders
        valid = orders[~orders["status"].isin(["cancelled"])] if "status" in orders.columns else orders

        total_sales = float(valid["total_amount"].sum()) if "total_amount" in valid.columns else 0.0
        num_orders = int(len(valid))
        num_customers = int(customers["customer_id"].nunique()) if "customer_id" in customers.columns and len(customers) > 0 else 0
        num_products = int(products["product_id"].nunique()) if "product_id" in products.columns and len(products) > 0 else 0
        avg_ticket = total_sales / num_orders if num_orders > 0 else 0.0

        # Gross margin calculation
        gross_margin = 0.0
        if len(products) > 0 and len(order_items) > 0:
            try:
                cost_col = "cost_price" if "cost_price" in products.columns else "cost"
                id_col = "product_id" if "product_id" in products.columns else "id"
                cost_map = dict(zip(products[id_col], products[cost_col]))
                if "product_id" in order_items.columns and "quantity" in order_items.columns:
                    order_items_copy = order_items.copy()
                    order_items_copy["unit_cost"] = order_items_copy["product_id"].map(cost_map).fillna(0)
                    total_cost = float((order_items_copy["unit_cost"] * order_items_copy["quantity"]).sum())
                    gross_margin = ((total_sales - total_cost) / total_sales * 100) if total_sales > 0 else 0.0
            except Exception as exc:
                logger.warning("Could not compute gross margin: %s", exc)
                gross_margin = 0.0

        return {
            "total_sales": total_sales,
            "num_orders": num_orders,
            "num_customers": num_customers,
            "num_products": num_products,
            "avg_ticket": avg_ticket,
            "gross_margin": gross_margin,
        }

    # ------------------------------------------------------------------
    # CSV fallback reader
    # ------------------------------------------------------------------
    @staticmethod
    def _read_csv(filename: str) -> pd.DataFrame:
        """Read a CSV file from the demo data directory."""
        path = _DEMO_DIR / filename
        if path.exists():
            try:
                df = pd.read_csv(path)
                return df
            except Exception as exc:
                logger.error("Error reading %s: %s", path, exc)
                return pd.DataFrame()
        logger.warning("Demo file not found: %s", path)
        return pd.DataFrame()
