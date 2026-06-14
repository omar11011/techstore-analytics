"""
Category repository with specialised query methods.
"""

from __future__ import annotations

import logging
from typing import List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.models import Category, Product, OrderItem
from app.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class CategoryRepository(BaseRepository[Category]):
    """Data-access layer for ``Category`` entities."""

    def __init__(self) -> None:
        super().__init__(Category)

    def get_category_sales(self, db: Session) -> List[dict]:
        """Return revenue breakdown per category.

        Field names match the ``CategorySales`` schema:
        category_id, name, total_sales, num_products.
        """
        rows = (
            db.query(
                Category.id.label("category_id"),
                Category.name,
                func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0).label(
                    "total_sales"
                ),
                func.count(Product.id).label("num_products"),
            )
            .outerjoin(Product, Product.category_id == Category.id)
            .outerjoin(OrderItem, OrderItem.product_id == Product.id)
            .group_by(Category.id, Category.name)
            .order_by(func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0).desc())
            .all()
        )
        return [row._asdict() for row in rows]
