"""
Inventory repository with specialised query methods.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.models import Inventory, Product
from app.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class InventoryRepository(BaseRepository[Inventory]):
    """Data-access layer for ``Inventory`` entities."""

    def __init__(self) -> None:
        super().__init__(Inventory)

    def get_low_stock(self, db: Session, threshold: int = 10) -> List[Inventory]:
        """Return inventory records with stock below *threshold*."""
        return (
            db.query(Inventory)
            .filter(Inventory.stock_quantity < threshold)
            .order_by(Inventory.stock_quantity.asc())
            .all()
        )

    def get_out_of_stock(self, db: Session) -> List[Inventory]:
        """Return inventory records with zero stock."""
        return (
            db.query(Inventory)
            .filter(Inventory.stock_quantity == 0)
            .all()
        )

    def get_by_store(self, db: Session, store_id: int) -> List[Inventory]:
        """Return all inventory records for a given store."""
        return (
            db.query(Inventory)
            .filter(Inventory.store_id == store_id)
            .all()
        )

    def get_by_store_product(
        self, db: Session, store_id: int, product_id: int
    ) -> Optional[Inventory]:
        """Return the inventory record for a specific store/product pair."""
        return (
            db.query(Inventory)
            .filter(Inventory.store_id == store_id, Inventory.product_id == product_id)
            .first()
        )

    def count_low_stock(self, db: Session, threshold: int = 10) -> int:
        """Count inventory records below threshold."""
        return (
            db.query(func.count(Inventory.id))
            .filter(Inventory.stock_quantity < threshold)
            .scalar()
        ) or 0

    def count_out_of_stock(self, db: Session) -> int:
        """Count inventory records with zero stock."""
        return (
            db.query(func.count(Inventory.id))
            .filter(Inventory.stock_quantity == 0)
            .scalar()
        ) or 0
