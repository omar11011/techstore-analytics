"""
Supplier repository with specialised query methods.
"""

from __future__ import annotations

import logging
from typing import List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.models import Supplier, Product, OrderItem
from app.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class SupplierRepository(BaseRepository[Supplier]):
    """Data-access layer for ``Supplier`` entities."""

    def __init__(self) -> None:
        super().__init__(Supplier)

    def get_supplier_sales(self, db: Session) -> List[dict]:
        """Return revenue breakdown per supplier.

        Field names match the ``SupplierSales`` schema:
        supplier_id, company_name, total_sales, product_count, num_orders.
        """
        rows = (
            db.query(
                Supplier.id.label("supplier_id"),
                Supplier.company_name,
                func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0).label(
                    "total_sales"
                ),
                func.count(func.distinct(Product.id)).label("product_count"),
                func.count(OrderItem.id).label("num_orders"),
            )
            .outerjoin(Product, Product.supplier_id == Supplier.id)
            .outerjoin(OrderItem, OrderItem.product_id == Product.id)
            .group_by(Supplier.id, Supplier.company_name)
            .order_by(func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0).desc())
            .all()
        )
        return [row._asdict() for row in rows]
