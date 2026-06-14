"""
Order repository with specialised query methods.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from datetime import datetime

from sqlalchemy import func, extract
from sqlalchemy.orm import Session

from app.models.models import Order, OrderItem, Product
from app.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class OrderRepository(BaseRepository[Order]):
    """Data-access layer for ``Order`` entities."""

    def __init__(self) -> None:
        super().__init__(Order)

    def get_filtered(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        customer_id: Optional[int] = None,
        store_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> List[Order]:
        """Return orders with optional filtering."""
        query = db.query(Order)
        if status:
            query = query.filter(Order.status == status)
        if customer_id is not None:
            query = query.filter(Order.customer_id == customer_id)
        if store_id is not None:
            query = query.filter(Order.store_id == store_id)
        if date_from:
            query = query.filter(Order.order_date >= date_from)
        if date_to:
            query = query.filter(Order.order_date <= date_to)
        return query.order_by(Order.order_date.desc()).offset(skip).limit(limit).all()

    def count_filtered(
        self,
        db: Session,
        status: Optional[str] = None,
        customer_id: Optional[int] = None,
        store_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> int:
        """Count orders matching the optional filters."""
        query = db.query(func.count(Order.id))
        if status:
            query = query.filter(Order.status == status)
        if customer_id is not None:
            query = query.filter(Order.customer_id == customer_id)
        if store_id is not None:
            query = query.filter(Order.store_id == store_id)
        if date_from:
            query = query.filter(Order.order_date >= date_from)
        if date_to:
            query = query.filter(Order.order_date <= date_to)
        return query.scalar() or 0

    def get_monthly_sales(self, db: Session, months: int = 12) -> List[dict]:
        """Return monthly revenue & order-count aggregates.

        Field names match the ``MonthlySales`` schema:
        year, month, total_sales, num_orders.
        """
        rows = (
            db.query(
                func.extract("year", Order.order_date).label("year"),
                func.extract("month", Order.order_date).label("month"),
                func.coalesce(func.sum(Order.total_amount), 0).label("total_sales"),
                func.count(Order.id).label("num_orders"),
            )
            .filter(Order.status != "cancelled")
            .group_by(
                func.extract("year", Order.order_date),
                func.extract("month", Order.order_date),
            )
            .order_by(
                func.extract("year", Order.order_date).desc(),
                func.extract("month", Order.order_date).desc(),
            )
            .limit(months)
            .all()
        )
        return [
            {
                "year": int(row.year),
                "month": int(row.month),
                "total_sales": row.total_sales,
                "num_orders": row.num_orders,
            }
            for row in rows
        ]

    def add_order_item(self, db: Session, order_id: int, **kwargs) -> Optional[OrderItem]:
        """Add a line item to an existing order."""
        item = OrderItem(order_id=order_id, **kwargs)
        db.add(item)
        db.flush()
        logger.debug("Added OrderItem to order_id=%s", order_id)
        return item

    def recalculate_total(self, db: Session, order_id: int) -> Optional[Order]:
        """Recalculate ``total_amount`` from line items and return the order."""
        order = self.get_by_id(db, order_id)
        if order is None:
            return None
        total = (
            db.query(
                func.coalesce(
                    func.sum(OrderItem.quantity * OrderItem.unit_price), 0
                )
            )
            .filter(OrderItem.order_id == order_id)
            .scalar()
        )
        order.total_amount = total
        db.flush()
        return order
