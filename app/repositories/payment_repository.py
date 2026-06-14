"""
Payment repository with specialised query methods.
"""

from __future__ import annotations

import logging
from typing import List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.models import Payment
from app.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class PaymentRepository(BaseRepository[Payment]):
    """Data-access layer for ``Payment`` entities."""

    def __init__(self) -> None:
        super().__init__(Payment)

    def get_by_order(self, db: Session, order_id: int) -> Payment | None:
        """Return the payment for a given order, or ``None``."""
        return db.query(Payment).filter(Payment.order_id == order_id).first()

    def get_payment_methods_stats(self, db: Session) -> List[dict]:
        """Return usage statistics grouped by payment method.

        Field names match the ``PaymentMethodStats`` schema:
        method, count, total_amount, percentage.
        """
        total_amount_all = (
            db.query(func.coalesce(func.sum(Payment.amount), 0)).scalar() or 0
        )
        rows = (
            db.query(
                Payment.payment_method.label("method"),
                func.count(Payment.id).label("count"),
                func.coalesce(func.sum(Payment.amount), 0).label("total_amount"),
            )
            .filter(Payment.payment_method.isnot(None))
            .group_by(Payment.payment_method)
            .order_by(func.coalesce(func.sum(Payment.amount), 0).desc())
            .all()
        )
        result = []
        for row in rows:
            d = row._asdict()
            d["percentage"] = (
                (d["total_amount"] / total_amount_all * 100) if total_amount_all else 0
            )
            result.append(d)
        return result
