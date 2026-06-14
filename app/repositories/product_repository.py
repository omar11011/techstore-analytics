"""
Product repository with specialised query methods.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.models import Product, OrderItem, Inventory
from app.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class ProductRepository(BaseRepository[Product]):
    """Data-access layer for ``Product`` entities."""

    def __init__(self) -> None:
        super().__init__(Product)

    def get_by_sku(self, db: Session, sku: str) -> Optional[Product]:
        """Return the product matching *sku*, or ``None``."""
        return db.query(Product).filter(Product.sku == sku).first()

    def get_filtered(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        category_id: Optional[int] = None,
        supplier_id: Optional[int] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        search: Optional[str] = None,
    ) -> List[Product]:
        """Return products with optional filtering."""
        query = db.query(Product)
        if category_id is not None:
            query = query.filter(Product.category_id == category_id)
        if supplier_id is not None:
            query = query.filter(Product.supplier_id == supplier_id)
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        if max_price is not None:
            query = query.filter(Product.price <= max_price)
        if search:
            term = f"%{search}%"
            query = query.filter(
                or_(
                    Product.name.ilike(term),
                    Product.description.ilike(term),
                    Product.sku.ilike(term),
                )
            )
        return query.offset(skip).limit(limit).all()

    def count_filtered(
        self,
        db: Session,
        category_id: Optional[int] = None,
        supplier_id: Optional[int] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        search: Optional[str] = None,
    ) -> int:
        """Count products matching the optional filters."""
        query = db.query(func.count(Product.id))
        if category_id is not None:
            query = query.filter(Product.category_id == category_id)
        if supplier_id is not None:
            query = query.filter(Product.supplier_id == supplier_id)
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        if max_price is not None:
            query = query.filter(Product.price <= max_price)
        if search:
            term = f"%{search}%"
            query = query.filter(
                or_(
                    Product.name.ilike(term),
                    Product.description.ilike(term),
                    Product.sku.ilike(term),
                )
            )
        return query.scalar() or 0

    def get_top_selling_products(self, db: Session, limit: int = 10) -> List[dict]:
        """Return products ranked by total quantity sold.

        Field names match the ``TopProduct`` schema:
        product_id, name, category, units_sold, revenue.
        """
        from app.models.models import Category

        rows = (
            db.query(
                Product.id.label("product_id"),
                Product.name,
                Category.name.label("category"),
                func.coalesce(func.sum(OrderItem.quantity), 0).label("units_sold"),
                func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0).label(
                    "revenue"
                ),
            )
            .outerjoin(OrderItem, OrderItem.product_id == Product.id)
            .outerjoin(Category, Category.id == Product.category_id)
            .group_by(Product.id, Product.name, Category.name)
            .order_by(func.coalesce(func.sum(OrderItem.quantity), 0).desc())
            .limit(limit)
            .all()
        )
        return [row._asdict() for row in rows]

    def get_products_without_sales(self, db: Session) -> List[Product]:
        """Return products that have never been ordered."""
        return (
            db.query(Product)
            .filter(~Product.order_items.any())
            .all()
        )

    def get_low_stock_products(self, db: Session, threshold: int = 10) -> List[dict]:
        """Return products whose total stock is below *threshold*."""
        rows = (
            db.query(
                Product.id,
                Product.name,
                Product.sku,
                func.coalesce(func.sum(Inventory.stock_quantity), 0).label("total_stock"),
            )
            .outerjoin(Inventory, Inventory.product_id == Product.id)
            .group_by(Product.id, Product.name, Product.sku)
            .having(func.coalesce(func.sum(Inventory.stock_quantity), 0) < threshold)
            .order_by(func.coalesce(func.sum(Inventory.stock_quantity), 0).asc())
            .all()
        )
        return [row._asdict() for row in rows]
