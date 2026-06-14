"""
Payment service layer.

Orchestrates business logic for payment-related operations, delegating
persistence to ``PaymentRepository`` and converting ORM models to
Pydantic response schemas.
"""

from __future__ import annotations

import logging
import math
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.models import Payment
from app.repositories.payment_repository import PaymentRepository
from app.schemas.schemas import (
    PaymentCreate,
    PaymentUpdate,
    PaymentResponse,
    PaymentMethodStats,
    PaginatedResponse,
)

logger = logging.getLogger(__name__)

_payment_repo = PaymentRepository()


class PaymentService:
    """Business logic for ``Payment`` entities."""

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    @staticmethod
    def create_payment(db: Session, data: PaymentCreate) -> PaymentResponse:
        """Create a new payment.

        Raises ``ValueError`` if a payment already exists for the order.
        """
        try:
            existing = _payment_repo.get_by_order(db, data.order_id)
            if existing:
                raise ValueError(
                    f"Payment already exists for order_id={data.order_id}"
                )

            payment = _payment_repo.create(
                db,
                order_id=data.order_id,
                payment_method=data.payment_method,
                payment_status=data.payment_status or "pending",
                amount=data.amount,
            )
            db.commit()
            db.refresh(payment)
            logger.info("Created payment id=%s for order_id=%s", payment.id, data.order_id)
            return PaymentResponse.model_validate(payment)
        except ValueError:
            raise
        except Exception as exc:
            db.rollback()
            logger.error("Failed to create payment: %s", exc)
            raise

    # ------------------------------------------------------------------
    # READ
    # ------------------------------------------------------------------

    @staticmethod
    def get_payment(db: Session, id: int) -> PaymentResponse:
        """Retrieve a single payment by ID.

        Raises ``ValueError`` if the payment is not found.
        """
        try:
            payment = _payment_repo.get_by_id(db, id)
            if payment is None:
                raise ValueError(f"Payment with id={id} not found")
            return PaymentResponse.model_validate(payment)
        except ValueError:
            raise
        except Exception as exc:
            logger.error("Failed to get payment id=%s: %s", id, exc)
            raise

    @staticmethod
    def get_payments(
        db: Session,
        skip: int = 0,
        limit: int = 100,
    ) -> PaginatedResponse[PaymentResponse]:
        """Return a paginated list of payments."""
        try:
            payments = _payment_repo.get_all(db, skip, limit)
            total = _payment_repo.count(db)
            items = [PaymentResponse.model_validate(p) for p in payments]
            page = (skip // limit) + 1 if limit > 0 else 1
            pages = math.ceil(total / limit) if limit > 0 else 0
            return PaginatedResponse[PaymentResponse](
                items=items, total=total, page=page, per_page=limit, pages=pages
            )
        except Exception as exc:
            logger.error("Failed to list payments: %s", exc)
            raise

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------

    @staticmethod
    def update_payment(db: Session, id: int, data: PaymentUpdate) -> PaymentResponse:
        """Update an existing payment.

        Raises ``ValueError`` if the payment is not found.
        """
        try:
            update_fields = data.model_dump(exclude_unset=True)
            if not update_fields:
                return PaymentService.get_payment(db, id)

            payment = _payment_repo.update(db, id, **update_fields)
            if payment is None:
                raise ValueError(f"Payment with id={id} not found")
            db.commit()
            db.refresh(payment)
            logger.info("Updated payment id=%s", id)
            return PaymentResponse.model_validate(payment)
        except ValueError:
            raise
        except Exception as exc:
            db.rollback()
            logger.error("Failed to update payment id=%s: %s", id, exc)
            raise

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------

    @staticmethod
    def delete_payment(db: Session, id: int) -> bool:
        """Delete a payment by ID.

        Raises ``ValueError`` if the payment is not found.
        """
        try:
            deleted = _payment_repo.delete(db, id)
            if not deleted:
                raise ValueError(f"Payment with id={id} not found")
            db.commit()
            logger.info("Deleted payment id=%s", id)
            return True
        except ValueError:
            raise
        except Exception as exc:
            db.rollback()
            logger.error("Failed to delete payment id=%s: %s", id, exc)
            raise

    # ------------------------------------------------------------------
    # ANALYTICS
    # ------------------------------------------------------------------

    @staticmethod
    def get_payment_methods_stats(db: Session) -> List[PaymentMethodStats]:
        """Return usage statistics grouped by payment method."""
        try:
            rows = _payment_repo.get_payment_methods_stats(db)
            return [PaymentMethodStats(**r) for r in rows]
        except Exception as exc:
            logger.error("Failed to get payment methods stats: %s", exc)
            raise
