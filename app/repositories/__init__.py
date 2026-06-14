"""
Repository layer package for TechStore Analytics.

Re-exports every repository class so that consuming code can do::

    from app.repositories import (
        BaseRepository,
        CustomerRepository,
        ProductRepository,
        OrderRepository,
        CategoryRepository,
        SupplierRepository,
        StoreRepository,
        InventoryRepository,
        PaymentRepository,
        ShipmentRepository,
        AnalyticsRepository,
    )
"""

from app.repositories.base_repository import BaseRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.supplier_repository import SupplierRepository
from app.repositories.store_repository import StoreRepository
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.shipment_repository import ShipmentRepository
from app.repositories.analytics_repo import AnalyticsRepository

__all__ = [
    "BaseRepository",
    "CustomerRepository",
    "ProductRepository",
    "OrderRepository",
    "CategoryRepository",
    "SupplierRepository",
    "StoreRepository",
    "InventoryRepository",
    "PaymentRepository",
    "ShipmentRepository",
    "AnalyticsRepository",
]
