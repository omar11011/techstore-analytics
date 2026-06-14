"""
Shipment repository with specialised query methods.
"""

from __future__ import annotations

import logging
from typing import List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.models import Shipment
from app.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class ShipmentRepository(BaseRepository[Shipment]):
    """Data-access layer for ``Shipment`` entities."""

    def __init__(self) -> None:
        super().__init__(Shipment)

    def get_by_order(self, db: Session, order_id: int) -> Shipment | None:
        """Return the shipment for a given order, or ``None``."""
        return db.query(Shipment).filter(Shipment.order_id == order_id).first()

    def get_pending_shipments(self, db: Session) -> List[Shipment]:
        """Return shipments that have not yet been delivered."""
        return (
            db.query(Shipment)
            .filter(Shipment.shipment_status.in_(["pending", "processing"]))
            .all()
        )

    def get_delivery_performance(self, db: Session) -> dict:
        """Return aggregate delivery performance metrics.

        Field names match the ``DeliveryPerformance`` schema:
        total_shipments, delivered_on_time, avg_days, on_time_rate.
        """
        total = db.query(func.count(Shipment.id)).scalar() or 0
        delivered = (
            db.query(func.count(Shipment.id))
            .filter(Shipment.shipment_status == "delivered")
            .scalar()
        ) or 0
        avg_days = (
            db.query(
                func.avg(
                    func.extract("epoch", Shipment.delivery_date - Shipment.shipped_date) / 86400
                )
            )
            .filter(
                Shipment.shipment_status == "delivered",
                Shipment.shipped_date.isnot(None),
                Shipment.delivery_date.isnot(None),
            )
            .scalar()
        )
        on_time_rate = (delivered / total * 100) if total else 0
        return {
            "total_shipments": total,
            "delivered_on_time": delivered,
            "avg_days": avg_days,
            "on_time_rate": on_time_rate,
        }
