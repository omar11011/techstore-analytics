"""
Customer repository with specialised query methods.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.models import Customer, Order, OrderItem
from app.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class CustomerRepository(BaseRepository[Customer]):
    """Data-access layer for ``Customer`` entities."""

    def __init__(self) -> None:
        super().__init__(Customer)

    def get_by_email(self, db: Session, email: str) -> Optional[Customer]:
        """Return the customer matching *email*, or ``None``."""
        return db.query(Customer).filter(Customer.email == email).first()

    def get_filtered(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        city: Optional[str] = None,
        country: Optional[str] = None,
    ) -> List[Customer]:
        """Return customers optionally filtered by city / country."""
        query = db.query(Customer)
        if city:
            query = query.filter(Customer.city.ilike(f"%{city}%"))
        if country:
            query = query.filter(Customer.country.ilike(f"%{country}%"))
        return query.offset(skip).limit(limit).all()

    def count_filtered(
        self,
        db: Session,
        city: Optional[str] = None,
        country: Optional[str] = None,
    ) -> int:
        """Count customers matching the optional filters."""
        query = db.query(func.count(Customer.id))
        if city:
            query = query.filter(Customer.city.ilike(f"%{city}%"))
        if country:
            query = query.filter(Customer.country.ilike(f"%{country}%"))
        return query.scalar() or 0

    def get_top_customers(self, db: Session, limit: int = 10) -> List[dict]:
        """Return customers ranked by total spending.

        Field names match the ``TopCustomer`` schema:
        customer_id, name, total_spent, num_orders.
        """
        rows = (
            db.query(
                Customer.id.label("customer_id"),
                (Customer.first_name + " " + Customer.last_name).label("name"),
                func.coalesce(func.sum(Order.total_amount), 0).label("total_spent"),
                func.count(Order.id).label("num_orders"),
            )
            .outerjoin(Order, Order.customer_id == Customer.id)
            .filter(Order.status != "cancelled")
            .group_by(Customer.id, Customer.first_name, Customer.last_name)
            .order_by(func.coalesce(func.sum(Order.total_amount), 0).desc())
            .limit(limit)
            .all()
        )
        return [row._asdict() for row in rows]
