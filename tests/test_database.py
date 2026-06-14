"""
Tests for database connectivity, table creation, and CSV demo-data loading.

These tests verify that:
1. The SQLAlchemy engine can connect to the test database.
2. All ORM models create their tables successfully.
3. CSV demo files in data/demo/ can be loaded with pandas.
"""

import os
import sys

import pytest
from sqlalchemy import inspect, create_engine
from sqlalchemy.orm import sessionmaker

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database.config import Base  # noqa: E402
from app.models.models import (  # noqa: E402
    Customer,
    Category,
    Supplier,
    Product,
    Store,
    Inventory,
    Order,
    OrderItem,
    Payment,
    Shipment,
)

# ---------------------------------------------------------------------------
# Expected table names from the ORM models
# ---------------------------------------------------------------------------
EXPECTED_TABLES = [
    "customers",
    "categories",
    "suppliers",
    "products",
    "stores",
    "inventory",
    "orders",
    "order_items",
    "payments",
    "shipments",
]

# ---------------------------------------------------------------------------
# CSV files expected in the demo data directory
# ---------------------------------------------------------------------------
DEMO_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "demo")
EXPECTED_CSV_FILES = [
    "customers.csv",
    "products.csv",
    "categories.csv",
    "stores.csv",
    "orders.csv",
    "order_items.csv",
    "monthly_sales.csv",
    "category_sales.csv",
    "top_products.csv",
    "top_customers.csv",
    "inventory_status.csv",
    "store_performance.csv",
]


# ---------------------------------------------------------------------------
# test_database_connection
# ---------------------------------------------------------------------------
def test_database_connection():
    """Verify that a connection to the SQLite test database can be established
    and a simple SELECT 1 succeeds.
    """
    from sqlalchemy import text

    test_db_url = "sqlite:///./test.db"
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        row = result.fetchone()
        assert row is not None
        assert row[0] == 1
    engine.dispose()


# ---------------------------------------------------------------------------
# test_create_tables
# ---------------------------------------------------------------------------
def test_create_tables():
    """Verify that all ORM model tables can be created in the test database."""
    test_db_url = "sqlite:///./test.db"
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Inspect and verify
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    for table_name in EXPECTED_TABLES:
        assert table_name in existing_tables, f"Table '{table_name}' was not created"

    # Also verify key columns exist in a few tables
    customer_columns = {col["name"] for col in inspector.get_columns("customers")}
    assert "id" in customer_columns
    assert "email" in customer_columns
    assert "first_name" in customer_columns

    product_columns = {col["name"] for col in inspector.get_columns("products")}
    assert "id" in product_columns
    assert "sku" in product_columns
    assert "price" in product_columns

    order_columns = {col["name"] for col in inspector.get_columns("orders")}
    assert "id" in order_columns
    assert "customer_id" in order_columns
    assert "status" in order_columns

    # Clean up
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


# ---------------------------------------------------------------------------
# test_demo_data_loading
# ---------------------------------------------------------------------------
def test_demo_data_loading():
    """Verify that CSV demo files exist and can be loaded with pandas.

    This test checks file existence and that pandas can parse each CSV
    into a DataFrame with at least one column.
    """
    import pandas as pd

    # Ensure the demo data directory exists
    assert os.path.isdir(DEMO_DATA_DIR), f"Demo data directory not found: {DEMO_DATA_DIR}"

    for csv_filename in EXPECTED_CSV_FILES:
        csv_path = os.path.join(DEMO_DATA_DIR, csv_filename)
        assert os.path.isfile(csv_path), f"CSV file not found: {csv_path}"

        # Load with pandas
        df = pd.read_csv(csv_path)
        assert len(df.columns) > 0, f"CSV {csv_filename} has no columns"
        # At least one row of data expected in demo files
        assert len(df) > 0, f"CSV {csv_filename} is empty (0 rows)"
