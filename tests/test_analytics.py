"""
Tests for the Analytics API endpoints.

Covers dashboard-summary, top-products, monthly-sales, and category-sales
endpoints under /api/v1/analytics.
"""

import pytest
from starlette.testclient import TestClient


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
ANALYTICS_URL = "/api/v1/analytics"


# ---------------------------------------------------------------------------
# test_dashboard_summary
# ---------------------------------------------------------------------------
def test_dashboard_summary(client: TestClient, sample_order: dict):
    """GET /analytics/dashboard-summary should return KPIs with expected fields."""
    response = client.get(f"{ANALYTICS_URL}/dashboard-summary")
    assert response.status_code == 200

    data = response.json()
    # Verify all expected fields are present
    assert "total_sales" in data
    assert "num_orders" in data
    assert "num_customers" in data
    assert "num_products" in data
    assert "avg_ticket" in data
    assert "gross_margin" in data
    assert "pending_orders" in data
    assert "low_stock_products" in data

    # With at least one order, some metrics should be non-zero
    assert data["num_orders"] >= 1
    assert data["num_customers"] >= 1
    assert data["num_products"] >= 1


# ---------------------------------------------------------------------------
# test_top_products
# ---------------------------------------------------------------------------
def test_top_products(client: TestClient, sample_order: dict):
    """GET /analytics/top-products should return a list of TopProduct entries."""
    response = client.get(f"{ANALYTICS_URL}/top-products")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)

    if len(data) > 0:
        first = data[0]
        assert "product_id" in first
        assert "name" in first
        assert "category" in first
        assert "units_sold" in first
        assert "revenue" in first

    # With a limit parameter
    response = client.get(f"{ANALYTICS_URL}/top-products", params={"limit": 5})
    assert response.status_code == 200
    assert len(response.json()) <= 5


# ---------------------------------------------------------------------------
# test_monthly_sales
# ---------------------------------------------------------------------------
def test_monthly_sales(client: TestClient, sample_order: dict):
    """GET /analytics/monthly-sales should return a list of MonthlySales entries."""
    response = client.get(f"{ANALYTICS_URL}/monthly-sales")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)

    if len(data) > 0:
        first = data[0]
        assert "year" in first
        assert "month" in first
        assert "total_sales" in first
        assert "num_orders" in first
        assert isinstance(first["year"], int)
        assert 1 <= first["month"] <= 12

    # With months parameter
    response = client.get(f"{ANALYTICS_URL}/monthly-sales", params={"months": 3})
    assert response.status_code == 200
    assert len(response.json()) <= 3


# ---------------------------------------------------------------------------
# test_category_sales
# ---------------------------------------------------------------------------
def test_category_sales(client: TestClient, sample_order: dict):
    """GET /analytics/category-sales should return a list of CategorySales entries."""
    response = client.get(f"{ANALYTICS_URL}/category-sales")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)

    if len(data) > 0:
        first = data[0]
        assert "category_id" in first
        assert "name" in first
        assert "total_sales" in first
        assert "num_products" in first
