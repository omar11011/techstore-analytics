"""
Tests for the Product API endpoints.

Covers CRUD operations and filtering for /api/v1/products.
"""

import pytest
from starlette.testclient import TestClient


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
PRODUCTS_URL = "/api/v1/products"


# ---------------------------------------------------------------------------
# test_create_product
# ---------------------------------------------------------------------------
def test_create_product(client: TestClient, sample_category: dict, sample_supplier: dict):
    """POST /products should create a new product and return 201."""
    payload = {
        "name": "UltraBook 14",
        "description": "Lightweight ultrabook with 32 GB RAM",
        "sku": "UB14-001",
        "price": "1599.99",
        "cost": "999.99",
        "category_id": sample_category["id"],
        "supplier_id": sample_supplier["id"],
    }
    response = client.post(PRODUCTS_URL, json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == payload["name"]
    assert data["sku"] == payload["sku"]
    assert data["price"] == payload["price"]
    assert data["cost"] == payload["cost"]
    assert data["category_id"] == sample_category["id"]
    assert data["supplier_id"] == sample_supplier["id"]
    assert "id" in data
    assert "created_at" in data


# ---------------------------------------------------------------------------
# test_get_product
# ---------------------------------------------------------------------------
def test_get_product(client: TestClient, sample_product: dict):
    """GET /products/{id} should return the correct product."""
    product_id = sample_product["id"]
    response = client.get(f"{PRODUCTS_URL}/{product_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == product_id
    assert data["sku"] == sample_product["sku"]

    # Non-existent product should 404
    response = client.get(f"{PRODUCTS_URL}/99999")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# test_get_products_with_filters
# ---------------------------------------------------------------------------
def test_get_products_with_filters(client: TestClient, sample_product: dict, sample_category: dict):
    """GET /products with query filters should narrow results correctly."""
    # No filters – at least one product
    response = client.get(PRODUCTS_URL)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1

    # Filter by category_id
    response = client.get(PRODUCTS_URL, params={"category_id": sample_category["id"]})
    assert response.status_code == 200
    filtered = response.json()
    assert filtered["total"] >= 1

    # Filter by min_price / max_price
    response = client.get(PRODUCTS_URL, params={"min_price": 1000, "max_price": 1500})
    assert response.status_code == 200
    price_filtered = response.json()
    for item in price_filtered["items"]:
        assert float(item["price"]) >= 1000
        assert float(item["price"]) <= 1500

    # Filter by non-matching category
    response = client.get(PRODUCTS_URL, params={"category_id": 99999})
    assert response.status_code == 200
    assert response.json()["total"] == 0

    # Search by name
    response = client.get(PRODUCTS_URL, params={"search": "ProBook"})
    assert response.status_code == 200
    assert response.json()["total"] >= 1


# ---------------------------------------------------------------------------
# test_update_product
# ---------------------------------------------------------------------------
def test_update_product(client: TestClient, sample_product: dict):
    """PUT /products/{id} should update specified fields."""
    product_id = sample_product["id"]
    update_payload = {
        "name": "ProBook 15 Updated",
        "price": "1399.99",
    }
    response = client.put(f"{PRODUCTS_URL}/{product_id}", json=update_payload)
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "ProBook 15 Updated"
    assert data["price"] == "1399.99"
    # Unchanged fields remain
    assert data["sku"] == sample_product["sku"]


# ---------------------------------------------------------------------------
# test_delete_product
# ---------------------------------------------------------------------------
def test_delete_product(client: TestClient, sample_product: dict):
    """DELETE /products/{id} should remove the product and return 204."""
    product_id = sample_product["id"]

    # Delete
    response = client.delete(f"{PRODUCTS_URL}/{product_id}")
    assert response.status_code == 204

    # Verify it's gone
    response = client.get(f"{PRODUCTS_URL}/{product_id}")
    assert response.status_code == 404

    # Deleting again should 404
    response = client.delete(f"{PRODUCTS_URL}/{product_id}")
    assert response.status_code == 404
