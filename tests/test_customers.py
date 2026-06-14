"""
Tests for the Customer API endpoints.

Covers CRUD operations and duplicate-email validation for /api/v1/customers.
"""

import pytest
from starlette.testclient import TestClient


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
CUSTOMERS_URL = "/api/v1/customers"


# ---------------------------------------------------------------------------
# test_create_customer
# ---------------------------------------------------------------------------
def test_create_customer(client: TestClient, sample_customer_payload: dict):
    """POST /customers should create a new customer and return 201."""
    response = client.post(CUSTOMERS_URL, json=sample_customer_payload)
    assert response.status_code == 201

    data = response.json()
    assert data["first_name"] == sample_customer_payload["first_name"]
    assert data["last_name"] == sample_customer_payload["last_name"]
    assert data["email"] == sample_customer_payload["email"]
    assert data["phone"] == sample_customer_payload["phone"]
    assert data["city"] == sample_customer_payload["city"]
    assert data["country"] == sample_customer_payload["country"]
    assert "id" in data
    assert "created_at" in data


# ---------------------------------------------------------------------------
# test_get_customer
# ---------------------------------------------------------------------------
def test_get_customer(client: TestClient, sample_customer: dict):
    """GET /customers/{id} should return the correct customer."""
    customer_id = sample_customer["id"]
    response = client.get(f"{CUSTOMERS_URL}/{customer_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == customer_id
    assert data["email"] == sample_customer["email"]

    # Non-existent customer should 404
    response = client.get(f"{CUSTOMERS_URL}/99999")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# test_get_customers_list
# ---------------------------------------------------------------------------
def test_get_customers_list(client: TestClient, sample_customer: dict):
    """GET /customers should return a paginated list with at least one item."""
    response = client.get(CUSTOMERS_URL)
    assert response.status_code == 200

    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "per_page" in data
    assert "pages" in data
    assert data["total"] >= 1
    assert len(data["items"]) >= 1

    # Filter by city
    response = client.get(CUSTOMERS_URL, params={"city": "Madrid"})
    assert response.status_code == 200
    filtered = response.json()
    assert filtered["total"] >= 1

    # Filter by non-existent city
    response = client.get(CUSTOMERS_URL, params={"city": "NonExistentCity"})
    assert response.status_code == 200
    empty = response.json()
    assert empty["total"] == 0


# ---------------------------------------------------------------------------
# test_update_customer
# ---------------------------------------------------------------------------
def test_update_customer(client: TestClient, sample_customer: dict):
    """PUT /customers/{id} should update specified fields."""
    customer_id = sample_customer["id"]
    update_payload = {
        "first_name": "Alicia",
        "city": "Valencia",
    }
    response = client.put(f"{CUSTOMERS_URL}/{customer_id}", json=update_payload)
    assert response.status_code == 200

    data = response.json()
    assert data["first_name"] == "Alicia"
    assert data["city"] == "Valencia"
    # Unchanged fields remain
    assert data["last_name"] == sample_customer["last_name"]
    assert data["email"] == sample_customer["email"]


# ---------------------------------------------------------------------------
# test_delete_customer
# ---------------------------------------------------------------------------
def test_delete_customer(client: TestClient, sample_customer: dict):
    """DELETE /customers/{id} should remove the customer and return 204."""
    customer_id = sample_customer["id"]

    # Delete
    response = client.delete(f"{CUSTOMERS_URL}/{customer_id}")
    assert response.status_code == 204

    # Verify it's gone
    response = client.get(f"{CUSTOMERS_URL}/{customer_id}")
    assert response.status_code == 404

    # Deleting again should also 404
    response = client.delete(f"{CUSTOMERS_URL}/{customer_id}")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# test_create_customer_duplicate_email
# ---------------------------------------------------------------------------
def test_create_customer_duplicate_email(
    client: TestClient,
    sample_customer: dict,
):
    """POST /customers with an already-registered email should return 400."""
    duplicate_payload = {
        "first_name": "Another",
        "last_name": "Person",
        "email": sample_customer["email"],  # same email
    }
    response = client.post(CUSTOMERS_URL, json=duplicate_payload)
    assert response.status_code == 400
    assert "already" in response.json()["detail"].lower()
