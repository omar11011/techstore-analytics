"""
Payment API router.

Exposes RESTful endpoints for managing payment records, including
CRUD operations and payment-method usage statistics.

Endpoints
---------
POST   /payments                – Create a payment
GET    /payments                – List payments (paginated)
GET    /payments/methods-stats  – Get payment method usage statistics
GET    /payments/{id}           – Retrieve a single payment
PUT    /payments/{id}           – Update a payment
DELETE /payments/{id}           – Delete a payment
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.schemas.schemas import (
    PaymentCreate,
    PaymentUpdate,
    PaymentResponse,
    PaymentMethodStats,
    PaginatedResponse,
)
from app.services.payment_service import PaymentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["Payments"])


# ---------------------------------------------------------------------------
# Specialised query endpoints (must be before {id} routes)
# ---------------------------------------------------------------------------

@router.get(
    "/methods-stats",
    response_model=List[PaymentMethodStats],
    summary="Payment method usage statistics",
    description="Return usage counts, totals, and percentages grouped by payment method.",
)
def get_payment_methods_stats(
    db: Session = Depends(get_db),
) -> List[PaymentMethodStats]:
    """Retrieve aggregated payment method statistics.

    Args:
        db: SQLAlchemy session.

    Returns:
        List of ``PaymentMethodStats`` grouped by method.
    """
    try:
        return PaymentService.get_payment_methods_stats(db)
    except Exception as exc:
        logger.error("Unexpected error fetching payment method stats: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching payment method statistics.",
        )


# ---------------------------------------------------------------------------
# CRUD endpoints
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a payment",
    description="Record a payment against an order.  Only one payment per order is allowed.",
    responses={
        400: {"description": "Invalid input or payment already exists for the order"},
        500: {"description": "Internal server error"},
    },
)
def create_payment(data: PaymentCreate, db: Session = Depends(get_db)) -> PaymentResponse:
    """Create a new payment record.

    Args:
        data: Payment creation payload validated by ``PaymentCreate``.
        db:   SQLAlchemy session injected via ``get_db``.

    Returns:
        The newly-created payment as a ``PaymentResponse``.

    Raises:
        HTTPException 400: If a payment already exists for the order.
        HTTPException 500: On unexpected server-side errors.
    """
    try:
        return PaymentService.create_payment(db, data)
    except ValueError as exc:
        logger.warning("Payment creation failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected error creating payment: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the payment.",
        )


@router.get(
    "",
    response_model=PaginatedResponse[PaymentResponse],
    summary="List payments",
    description="Return a paginated list of payment records.",
)
def list_payments(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=100, ge=1, le=500, description="Maximum records to return"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[PaymentResponse]:
    """Retrieve a paginated list of payments.

    Args:
        skip:  Offset for pagination.
        limit: Page size.
        db:    SQLAlchemy session.

    Returns:
        ``PaginatedResponse`` containing payment records.
    """
    try:
        return PaymentService.get_payments(db, skip=skip, limit=limit)
    except Exception as exc:
        logger.error("Unexpected error listing payments: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while listing payments.",
        )


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
    summary="Get a payment by ID",
    responses={404: {"description": "Payment not found"}},
)
def get_payment(payment_id: int, db: Session = Depends(get_db)) -> PaymentResponse:
    """Retrieve a single payment by primary key.

    Args:
        payment_id: Primary key of the payment.
        db:         SQLAlchemy session.

    Returns:
        The matching ``PaymentResponse``.

    Raises:
        HTTPException 404: If the payment does not exist.
    """
    try:
        return PaymentService.get_payment(db, payment_id)
    except ValueError as exc:
        logger.info("Payment not found: %s", exc)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected error retrieving payment id=%s: %s", payment_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving the payment.",
        )


@router.put(
    "/{payment_id}",
    response_model=PaymentResponse,
    summary="Update a payment",
    responses={
        400: {"description": "Invalid input"},
        404: {"description": "Payment not found"},
    },
)
def update_payment(
    payment_id: int,
    data: PaymentUpdate,
    db: Session = Depends(get_db),
) -> PaymentResponse:
    """Update an existing payment.

    Only fields present in the request body are modified (partial update).

    Args:
        payment_id: Primary key of the payment to update.
        data:       Partial-update payload.
        db:         SQLAlchemy session.

    Returns:
        The updated ``PaymentResponse``.

    Raises:
        HTTPException 404: If the payment is not found.
        HTTPException 400: On validation errors.
    """
    try:
        return PaymentService.update_payment(db, payment_id, data)
    except ValueError as exc:
        error_msg = str(exc)
        if "not found" in error_msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
    except Exception as exc:
        logger.error("Unexpected error updating payment id=%s: %s", payment_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while updating the payment.",
        )


@router.delete(
    "/{payment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a payment",
    responses={404: {"description": "Payment not found"}},
)
def delete_payment(payment_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a payment by ID.

    Args:
        payment_id: Primary key of the payment to delete.
        db:         SQLAlchemy session.

    Raises:
        HTTPException 404: If the payment does not exist.
    """
    try:
        PaymentService.delete_payment(db, payment_id)
    except ValueError as exc:
        logger.info("Payment delete failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected error deleting payment id=%s: %s", payment_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while deleting the payment.",
        )
