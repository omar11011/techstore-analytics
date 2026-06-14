"""
Tests for the Order API endpoints.

Covers order creation with items, retrieval, filtered listing,
status updates, and adding line items to existing orders.
"""

import pytest
from starlette.testclient import TestClient


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
ORDERS_URL = "/api/v1/orders"


# ---------------------------------------------------------------------------
# test_create_order_with_items
# ---------------------------------------------------------------------------
def test_create_order_with_items(
    client: TestClient,
    sample_customer: dict,
    sample_product: dict,
    sample_store: dict,
):
    """POST /orders should create an order with line items and auto-calculate total."""
    payload = {
        "customer_id": sample_customer["id"],
        "store_id": sample_store["id"],
        "status": "pending",
        "items": [
            {
                "product_id": sample_product["id"],
                "quantity": 3,
                "unit_price": "1299.99",
                "discount": "0.00",
            },
            {
                "product_id": sample_product["id"],
                "quantity": 1,
                "unit_price": "1299.99",
                "discount": "10.00",
            },
        ],
    }
    response = client.post(ORDERS_URL, json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["customer_id"] == sample_customer["id"]
    assert data["store_id"] == sample_store["id"]
    assert data["status"] == "pending"
    assert len(data["items"]) == 2
    assert "total_amount" in data
    assert data["total_amount"] is not None

    # Verify total is correct: 3*1299.99 + 1*1299.99*(1-0.10) = 3899.97 + 1169.991 = 5069.961
    expected_total = round(3 * 1299.99 + 1299.99 * (1 - 0.10), 2)
    assert float(data["total_amount"]) == pytest.approx(expected_total, rel=0.01)


# ---------------------------------------------------------------------------
# test_get_order
# ---------------------------------------------------------------------------
def test_get_order(client: TestClient, sample_order: dict):
    """GET /orders/{id} should return the order with its items."""
    order_id = sample_order["id"]
    response = client.get(f"{ORDERS_URL}/{order_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == order_id
    assert "items" in data
    assert len(data["items"]) >= 1

    # Non-existent order should 404
    response = client.get(f"{ORDERS_URL}/99999")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# test_get_orders_with_filters
# ---------------------------------------------------------------------------
def test_get_orders_with_filters(client: TestClient, sample_order: dict, sample_customer: dict):
    """GET /orders with query filters should narrow results correctly."""
    # No filters – at least one order
    response = client.get(ORDERS_URL)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1

    # Filter by customer_id
    response = client.get(ORDERS_URL, params={"customer_id": sample_customer["id"]})
    assert response.status_code == 200
    filtered = response.json()
    assert filtered["total"] >= 1

    # Filter by status
    response = client.get(ORDERS_URL, params={"status": "pending"})
    assert response.status_code == 200
    status_filtered = response.json()
    for item in status_filtered["items"]:
        assert item["status"] == "pending"

    # Filter by non-matching status
    response = client.get(ORDERS_URL, params={"status": "delivered"})
    assert response.status_code == 200
    assert response.json()["total"] == 0

    # Filter by non-matching customer
    response = client.get(ORDERS_URL, params={"customer_id": 99999})
    assert response.status_code == 200
    assert response.json()["total"] == 0


# ---------------------------------------------------------------------------
# test_update_order_status
# ---------------------------------------------------------------------------
def test_update_order_status(client: TestClient, sample_order: dict):
    """PUT /orders/{id}/status should update the order's status."""
    order_id = sample_order["id"]

    # Update to 'confirmed'
    response = client.put(
        f"{ORDERS_URL}/{order_id}/status",
        json={"status": "confirmed"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "confirmed"

    # Update to 'shipped'
    response = client.put(
        f"{ORDERS_URL}/{order_id}/status",
        json={"status": "shipped"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "shipped"

    # Update to 'delivered'
    response = client.put(
        f"{ORDERS_URL}/{order_id}/status",
        json={"status": "delivered"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "delivered"

    # Non-existent order should 404
    response = client.put(
        f"{ORDERS_URL}/99999/status",
        json={"status": "confirmed"},
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# test_add_order_item
# ---------------------------------------------------------------------------
def test_add_order_item(
    client: TestClient,
    sample_order: dict,
    sample_product: dict,
):
    """POST /orders/{id}/items should add a line item and recalculate the total."""
    order_id = sample_order["id"]
    original_total = float(sample_order["total_amount"])

    new_item = {
        "product_id": sample_product["id"],
        "quantity": 1,
        "unit_price": "1299.99",
        "discount": "0.00",
    }
    response = client.post(
        f"{ORDERS_URL}/{order_id}/items",
        json=new_item,
    )
    assert response.status_code == 201

    item_data = response.json()
    assert item_data["order_id"] == order_id
    assert item_data["quantity"] == 1
    assert item_data["product_id"] == sample_product["id"]

    # Verify the order total was recalculated
    response = client.get(f"{ORDERS_URL}/{order_id}")
    assert response.status_code == 200
    updated_order = response.json()
    new_total = float(updated_order["total_amount"])
    assert new_total == pytest.approx(original_total + 1299.99, rel=0.01)
