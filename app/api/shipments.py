"""
Shipment API router.

Exposes RESTful endpoints for managing shipment / fulfilment records,
including CRUD operations and delivery-performance analytics.

Endpoints
---------
POST   /shipments                    – Create a shipment
GET    /shipments                    – List shipments (paginated)
GET    /shipments/pending            – Get pending shipments
GET    /shipments/delivery-performance – Get delivery performance metrics
GET    /shipments/{id}               – Retrieve a single shipment
PUT    /shipments/{id}               – Update a shipment
DELETE /shipments/{id}               – Delete a shipment
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.schemas.schemas import (
    ShipmentCreate,
    ShipmentUpdate,
    ShipmentResponse,
    DeliveryPerformance,
    PaginatedResponse,
)
from app.services.shipment_service import ShipmentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/shipments", tags=["Shipments"])


# ---------------------------------------------------------------------------
# Specialised query endpoints (must be before {id} routes)
# ---------------------------------------------------------------------------

@router.get(
    "/pending",
    response_model=List[ShipmentResponse],
    summary="Get pending shipments",
    description="Return shipments that have not yet been delivered.",
)
def get_pending_shipments(db: Session = Depends(get_db)) -> List[ShipmentResponse]:
    """Retrieve all shipments that are still pending delivery.

    Args:
        db: SQLAlchemy session.

    Returns:
        List of ``ShipmentResponse`` items with pending status.
    """
    try:
        return ShipmentService.get_pending_shipments(db)
    except Exception as exc:
        logger.error("Unexpected error fetching pending shipments: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching pending shipments.",
        )


@router.get(
    "/delivery-performance",
    response_model=DeliveryPerformance,
    summary="Delivery performance metrics",
    description="Return aggregate delivery performance statistics across all shipments.",
)
def get_delivery_performance(db: Session = Depends(get_db)) -> DeliveryPerformance:
    """Retrieve aggregate delivery performance metrics.

    Args:
        db: SQLAlchemy session.

    Returns:
        ``DeliveryPerformance`` with on-time rate, average days, etc.
    """
    try:
        return ShipmentService.get_delivery_performance(db)
    except Exception as exc:
        logger.error("Unexpected error fetching delivery performance: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching delivery performance.",
        )


# ---------------------------------------------------------------------------
# CRUD endpoints
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=ShipmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a shipment",
    description="Create a shipment record for an order.  Only one shipment per order is allowed.",
    responses={
        400: {"description": "Invalid input or shipment already exists for the order"},
        500: {"description": "Internal server error"},
    },
)
def create_shipment(data: ShipmentCreate, db: Session = Depends(get_db)) -> ShipmentResponse:
    """Create a new shipment record.

    Args:
        data: Shipment creation payload validated by ``ShipmentCreate``.
        db:   SQLAlchemy session injected via ``get_db``.

    Returns:
        The newly-created shipment as a ``ShipmentResponse``.

    Raises:
        HTTPException 400: If a shipment already exists for the order.
        HTTPException 500: On unexpected server-side errors.
    """
    try:
        return ShipmentService.create_shipment(db, data)
    except ValueError as exc:
        logger.warning("Shipment creation failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected error creating shipment: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the shipment.",
        )


@router.get(
    "",
    response_model=PaginatedResponse[ShipmentResponse],
    summary="List shipments",
    description="Return a paginated list of shipment records.",
)
def list_shipments(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=100, ge=1, le=500, description="Maximum records to return"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[ShipmentResponse]:
    """Retrieve a paginated list of shipments.

    Args:
        skip:  Offset for pagination.
        limit: Page size.
        db:    SQLAlchemy session.

    Returns:
        ``PaginatedResponse`` containing shipment records.
    """
    try:
        return ShipmentService.get_shipments(db, skip=skip, limit=limit)
    except Exception as exc:
        logger.error("Unexpected error listing shipments: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while listing shipments.",
        )


@router.get(
    "/{shipment_id}",
    response_model=ShipmentResponse,
    summary="Get a shipment by ID",
    responses={404: {"description": "Shipment not found"}},
)
def get_shipment(shipment_id: int, db: Session = Depends(get_db)) -> ShipmentResponse:
    """Retrieve a single shipment by primary key.

    Args:
        shipment_id: Primary key of the shipment.
        db:          SQLAlchemy session.

    Returns:
        The matching ``ShipmentResponse``.

    Raises:
        HTTPException 404: If the shipment does not exist.
    """
    try:
        return ShipmentService.get_shipment(db, shipment_id)
    except ValueError as exc:
        logger.info("Shipment not found: %s", exc)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected error retrieving shipment id=%s: %s", shipment_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving the shipment.",
        )


@router.put(
    "/{shipment_id}",
    response_model=ShipmentResponse,
    summary="Update a shipment",
    responses={
        400: {"description": "Invalid input"},
        404: {"description": "Shipment not found"},
    },
)
def update_shipment(
    shipment_id: int,
    data: ShipmentUpdate,
    db: Session = Depends(get_db),
) -> ShipmentResponse:
    """Update an existing shipment.

    Only fields present in the request body are modified (partial update).

    Args:
        shipment_id: Primary key of the shipment to update.
        data:        Partial-update payload.
        db:          SQLAlchemy session.

    Returns:
        The updated ``ShipmentResponse``.

    Raises:
        HTTPException 404: If the shipment is not found.
        HTTPException 400: On validation errors.
    """
    try:
        return ShipmentService.update_shipment(db, shipment_id, data)
    except ValueError as exc:
        error_msg = str(exc)
        if "not found" in error_msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
    except Exception as exc:
        logger.error("Unexpected error updating shipment id=%s: %s", shipment_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while updating the shipment.",
        )


@router.delete(
    "/{shipment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a shipment",
    responses={404: {"description": "Shipment not found"}},
)
def delete_shipment(shipment_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a shipment by ID.

    Args:
        shipment_id: Primary key of the shipment to delete.
        db:          SQLAlchemy session.

    Raises:
        HTTPException 404: If the shipment does not exist.
    """
    try:
        ShipmentService.delete_shipment(db, shipment_id)
    except ValueError as exc:
        logger.info("Shipment delete failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected error deleting shipment id=%s: %s", shipment_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while deleting the shipment.",
        )
