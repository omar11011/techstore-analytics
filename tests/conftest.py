"""
Pytest configuration and shared fixtures for TechStore Analytics test suite.

Provides a SQLite in-memory database, TestClient, session fixtures, and
sample data factories for all test modules.
"""

import os
import sys
from decimal import Decimal
from typing import Generator

# ---------------------------------------------------------------------------
# IMPORTANT: Set the DATABASE_URL environment variable BEFORE importing any
# app modules.  This ensures that the SQLAlchemy engine in config.py is
# created with SQLite instead of trying to connect to PostgreSQL.
# ---------------------------------------------------------------------------
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

# Ensure the project root is on sys.path so that `app.*` imports work.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker, Session  # noqa: E402

# Import Base FIRST, then enable __allow_unmapped__ so that the ORM models
# (which use bare type annotations like ``list["Order"]`` on relationships)
# are accepted by SQLAlchemy 2.0+'s declarative scanner.
from app.database.config import Base, get_db  # noqa: E402
Base.__allow_unmapped__ = True

from app.main import app  # noqa: E402
from starlette.testclient import TestClient  # noqa: E402

# ---------------------------------------------------------------------------
# Test database URL – SQLite in-memory for speed and isolation
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite:///./test.db"

# ---------------------------------------------------------------------------
# Engine & session factory for tests
# ---------------------------------------------------------------------------
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

TestSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


# ---------------------------------------------------------------------------
# Fixture: database tables
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def setup_database():
    """Create all tables before each test and drop them after.

    This ensures every test starts with a clean schema.  Using autouse
    so that individual test files don't need to explicitly request it.
    """
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


# ---------------------------------------------------------------------------
# Fixture: database session
# ---------------------------------------------------------------------------
@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session backed by the test database.

    The session is rolled back and closed after the test to prevent
    data leaking between tests.
    """
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


# ---------------------------------------------------------------------------
# Fixture: test client with overridden get_db dependency
# ---------------------------------------------------------------------------
@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Provide a ``TestClient`` whose ``get_db`` dependency yields the
    test session instead of the production one.
    """

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass  # session cleanup handled by db_session fixture

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Sample data fixtures
# ---------------------------------------------------------------------------
@pytest.fixture()
def sample_customer(client: TestClient) -> dict:
    """Create a sample customer via the API and return the response JSON."""
    payload = {
        "first_name": "Alice",
        "last_name": "Garcia",
        "email": "alice.garcia@example.com",
        "phone": "+34-600-111-222",
        "city": "Madrid",
        "country": "Spain",
    }
    response = client.post("/api/v1/customers", json=payload)
    assert response.status_code == 201, f"Failed to create sample customer: {response.text}"
    return response.json()


@pytest.fixture()
def sample_customer_payload() -> dict:
    """Return a valid customer creation payload (without hitting the API)."""
    return {
        "first_name": "Bob",
        "last_name": "Martinez",
        "email": "bob.martinez@example.com",
        "phone": "+34-600-333-444",
        "city": "Barcelona",
        "country": "Spain",
    }


@pytest.fixture()
def sample_category(client: TestClient) -> dict:
    """Create a sample category via the API and return the response JSON."""
    payload = {
        "name": "Laptops",
        "description": "Portable computers for work and play",
    }
    response = client.post("/api/v1/categories", json=payload)
    assert response.status_code == 201, f"Failed to create sample category: {response.text}"
    return response.json()


@pytest.fixture()
def sample_supplier(client: TestClient) -> dict:
    """Create a sample supplier via the API and return the response JSON."""
    payload = {
        "company_name": "TechSupplier Corp",
        "contact_name": "Carlos Lopez",
        "email": "contact@techsupplier.com",
        "phone": "+34-900-555-666",
        "country": "Spain",
    }
    response = client.post("/api/v1/suppliers", json=payload)
    assert response.status_code == 201, f"Failed to create sample supplier: {response.text}"
    return response.json()


@pytest.fixture()
def sample_product(client: TestClient, sample_category: dict, sample_supplier: dict) -> dict:
    """Create a sample product via the API and return the response JSON."""
    payload = {
        "name": "ProBook 15",
        "description": "Business laptop with 16 GB RAM",
        "sku": "PB15-001",
        "price": "1299.99",
        "cost": "899.99",
        "category_id": sample_category["id"],
        "supplier_id": sample_supplier["id"],
    }
    response = client.post("/api/v1/products", json=payload)
    assert response.status_code == 201, f"Failed to create sample product: {response.text}"
    return response.json()


@pytest.fixture()
def sample_store(client: TestClient) -> dict:
    """Create a sample store via the API and return the response JSON."""
    payload = {
        "name": "TechStore Madrid Centro",
        "city": "Madrid",
        "country": "Spain",
    }
    response = client.post("/api/v1/stores", json=payload)
    assert response.status_code == 201, f"Failed to create sample store: {response.text}"
    return response.json()


@pytest.fixture()
def sample_order(
    client: TestClient,
    sample_customer: dict,
    sample_product: dict,
    sample_store: dict,
) -> dict:
    """Create a sample order with one line item via the API and return the
    response JSON.
    """
    payload = {
        "customer_id": sample_customer["id"],
        "store_id": sample_store["id"],
        "status": "pending",
        "items": [
            {
                "product_id": sample_product["id"],
                "quantity": 2,
                "unit_price": "1299.99",
                "discount": "0.00",
            }
        ],
    }
    response = client.post("/api/v1/orders", json=payload)
    assert response.status_code == 201, f"Failed to create sample order: {response.text}"
    return response.json()


@pytest.fixture()
def sample_inventory(
    client: TestClient,
    sample_product: dict,
    sample_store: dict,
) -> dict:
    """Create a sample inventory record and return the response JSON."""
    payload = {
        "store_id": sample_store["id"],
        "product_id": sample_product["id"],
        "stock_quantity": 50,
    }
    response = client.post("/api/v1/inventory", json=payload)
    assert response.status_code == 201, f"Failed to create sample inventory: {response.text}"
    return response.json()
