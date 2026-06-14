"""
Store repository with specialised query methods.
"""

from __future__ import annotations

import logging
from typing import List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.models import Store, Order
from app.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class StoreRepository(BaseRepository[Store]):
    """Data-access layer for ``Store`` entities."""

    def __init__(self) -> None:
        super().__init__(Store)

    def get_store_performance(self, db: Session) -> List[dict]:
        """Return performance metrics per store.

        Field names match the ``StorePerformance`` schema:
        store_id, name, city, total_sales, num_orders.
        """
        rows = (
            db.query(
                Store.id.label("store_id"),
                Store.name,
                Store.city,
                func.coalesce(func.sum(Order.total_amount), 0).label("total_sales"),
                func.count(Order.id).label("num_orders"),
            )
            .outerjoin(Order, Order.store_id == Store.id)
            .group_by(Store.id, Store.name, Store.city)
            .order_by(func.coalesce(func.sum(Order.total_amount), 0).desc())
            .all()
        )
        return [row._asdict() for row in rows]
