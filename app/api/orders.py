"""
Order API router.

Exposes RESTful endpoints for managing orders, including creation with
auto-calculated totals, status transitions, and line-item management.

Endpoints
---------
POST   /orders                – Create an order with items
GET    /orders                – List orders (paginated, filterable)
GET    /orders/{id}           – Retrieve a single order
PUT    /orders/{id}/status    – Update order status
DELETE /orders/{id}           – Delete an order
POST   /orders/{id}/items     – Add an item to an existing order
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.schemas.schemas import (
    OrderCreate,
    OrderResponse,
    OrderItemCreate,
    OrderItemResponse,
    PaginatedResponse,
)
from app.services.order_service import OrderService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orders", tags=["Orders"])


# ---------------------------------------------------------------------------
# Helper schema for the status-update endpoint
# ---------------------------------------------------------------------------

class OrderStatusUpdate(BaseModel):
    """Request body for updating an order's status."""

    status: str = Field(
        ...,
        description="New order status – pending, confirmed, processing, shipped, delivered, cancelled.",
    )


# ---------------------------------------------------------------------------
# CRUD endpoints
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new order",
    description=(
        "Place a new order with one or more line items.  The total amount "
        "is automatically calculated from the items.  If ``unit_price`` is "
        "omitted for an item, the product's current selling price is used."
    ),
    responses={
        400: {"description": "Invalid input (e.g. unknown product)"},
        500: {"description": "Internal server error"},
    },
)
def create_order(data: OrderCreate, db: Session = Depends(get_db)) -> OrderResponse:
    """Create a new order together with its line items.

    Args:
        data: Order creation payload validated by ``OrderCreate``.
        db:   SQLAlchemy session injected via ``get_db``.

    Returns:
        The newly-created order as an ``OrderResponse``.

    Raises:
        HTTPException 400: If a referenced product is not found.
        HTTPException 500: On unexpected server-side errors.
    """
    try:
        return OrderService.create_order(db, data)
    except ValueError as exc:
        logger.warning("Order creation failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected error creating order: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the order.",
        )


@router.get(
    "",
    response_model=PaginatedResponse[OrderResponse],
    summary="List orders",
    description="Return a paginated list of orders with optional filters.",
)
def list_orders(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=100, ge=1, le=500, description="Maximum records to return"),
    status_filter: Optional[str] = Query(
        default=None, alias="status", description="Filter by order status",
    ),
    customer_id: Optional[int] = Query(default=None, description="Filter by customer ID"),
    store_id: Optional[int] = Query(default=None, description="Filter by store ID"),
    date_from: Optional[datetime] = Query(default=None, description="Filter orders from this date"),
    date_to: Optional[datetime] = Query(default=None, description="Filter orders up to this date"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[OrderResponse]:
    """Retrieve a paginated, filterable list of orders.

    Args:
        skip:         Offset for pagination.
        limit:        Page size.
        status_filter: Optional status filter.
        customer_id:  Optional customer filter.
        store_id:     Optional store filter.
        date_from:    Optional start-date filter.
        date_to:      Optional end-date filter.
        db:           SQLAlchemy session.

    Returns:
        ``PaginatedResponse`` containing matching orders.
    """
    try:
        return OrderService.get_orders(
            db,
            skip=skip,
            limit=limit,
            status=status_filter,
            customer_id=customer_id,
            store_id=store_id,
            date_from=date_from,
            date_to=date_to,
        )
    except Exception as exc:
        logger.error("Unexpected error listing orders: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while listing orders.",
        )


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get an order by ID",
    responses={404: {"description": "Order not found"}},
)
def get_order(order_id: int, db: Session = Depends(get_db)) -> OrderResponse:
    """Retrieve a single order by primary key (includes line items).

    Args:
        order_id: Primary key of the order.
        db:       SQLAlchemy session.

    Returns:
        The matching ``OrderResponse`` with items.

    Raises:
        HTTPException 404: If the order does not exist.
    """
    try:
        return OrderService.get_order(db, order_id)
    except ValueError as exc:
        logger.info("Order not found: %s", exc)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected error retrieving order id=%s: %s", order_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving the order.",
        )


@router.put(
    "/{order_id}/status",
    response_model=OrderResponse,
    summary="Update order status",
    description="Transition an order to a new status.",
    responses={
        400: {"description": "Invalid status value"},
        404: {"description": "Order not found"},
    },
)
def update_order_status(
    order_id: int,
    body: OrderStatusUpdate,
    db: Session = Depends(get_db),
) -> OrderResponse:
    """Update only the status field of an order.

    Args:
        order_id: Primary key of the order.
        body:     Payload containing the new status string.
        db:       SQLAlchemy session.

    Returns:
        The updated ``OrderResponse``.

    Raises:
        HTTPException 404: If the order is not found.
        HTTPException 400: If the status value is invalid.
    """
    try:
        return OrderService.update_order_status(db, order_id, body.status)
    except ValueError as exc:
        error_msg = str(exc)
        if "not found" in error_msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
    except Exception as exc:
        logger.error("Unexpected error updating order status id=%s: %s", order_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while updating order status.",
        )


@router.delete(
    "/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an order",
    responses={404: {"description": "Order not found"}},
)
def delete_order(order_id: int, db: Session = Depends(get_db)) -> None:
    """Delete an order by ID.

    Args:
        order_id: Primary key of the order to delete.
        db:       SQLAlchemy session.

    Raises:
        HTTPException 404: If the order does not exist.
    """
    try:
        OrderService.delete_order(db, order_id)
    except ValueError as exc:
        logger.info("Order delete failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected error deleting order id=%s: %s", order_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while deleting the order.",
        )


# ---------------------------------------------------------------------------
# Line-item management
# ---------------------------------------------------------------------------

@router.post(
    "/{order_id}/items",
    response_model=OrderItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an item to an order",
    description=(
        "Append a line item to an existing order.  The order total is "
        "automatically recalculated."
    ),
    responses={
        400: {"description": "Invalid input or unknown product"},
        404: {"description": "Order not found"},
    },
)
def add_order_item(
    order_id: int,
    item_data: OrderItemCreate,
    db: Session = Depends(get_db),
) -> OrderItemResponse:
    """Add a line item to an existing order.

    If ``unit_price`` is not provided, the product's current selling price
    is used.  The order total is recalculated automatically.

    Args:
        order_id:  Primary key of the order.
        item_data: Line-item payload validated by ``OrderItemCreate``.
        db:        SQLAlchemy session.

    Returns:
        The newly-created ``OrderItemResponse``.

    Raises:
        HTTPException 404: If the order or product is not found.
        HTTPException 400: On validation errors.
    """
    try:
        return OrderService.add_order_item(db, order_id, item_data)
    except ValueError as exc:
        error_msg = str(exc)
        if "not found" in error_msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
    except Exception as exc:
        logger.error("Unexpected error adding item to order id=%s: %s", order_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while adding the order item.",
        )
