"""
ORM models package for TechStore Analytics.

Re-exports every model class so that consuming code can simply do::

    from app.models import Customer, Order, …

This also ensures that all models are registered with the declarative
metadata when the package is imported, which is required for
``Base.metadata.create_all()`` to work correctly.
"""

from app.models.models import (
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

__all__ = [
    "Customer",
    "Category",
    "Supplier",
    "Product",
    "Store",
    "Inventory",
    "Order",
    "OrderItem",
    "Payment",
    "Shipment",
]
