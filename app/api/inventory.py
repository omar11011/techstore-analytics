"""
Inventory API router.

Exposes RESTful endpoints for managing inventory records (per-store stock
levels for products), plus specialised query endpoints for low-stock and
out-of-stock items.

Endpoints
---------
POST   /inventory                     – Create an inventory record
GET    /inventory                     – List inventory records (paginated)
GET    /inventory/low-stock           – Get items below stock threshold
GET    /inventory/out-of-stock        – Get items with zero stock
GET    /inventory/by-store/{store_id} – Get inventory for a specific store
GET    /inventory/{id}                – Retrieve a single inventory record
PUT    /inventory/{id}                – Update an inventory record
DELETE /inventory/{id}                – Delete an inventory record
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.schemas.schemas import (
    InventoryCreate,
    InventoryUpdate,
    InventoryResponse,
    PaginatedResponse,
)
from app.services.inventory_service import InventoryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inventory", tags=["Inventory"])


# ---------------------------------------------------------------------------
# Specialised query endpoints (must be defined before {id} routes)
# ---------------------------------------------------------------------------

@router.get(
    "/low-stock",
    response_model=List[InventoryResponse],
    summary="Get low-stock items",
    description="Return inventory records with stock below the given threshold.",
)
def get_low_stock(
    threshold: int = Query(default=10, ge=0, description="Stock threshold (default 10)"),
    db: Session = Depends(get_db),
) -> List[InventoryResponse]:
    """Retrieve inventory records with stock below *threshold*.

    Args:
        threshold: Minimum stock level; records below this are returned.
        db:        SQLAlchemy session.

    Returns:
        List of ``InventoryResponse`` items with low stock.
    """
    try:
        return InventoryService.get_low_stock(db, threshold=threshold)
    except Exception as exc:
        logger.error("Unexpected error fetching low-stock inventory: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching low-stock items.",
        )


@router.get(
    "/out-of-stock",
    response_model=List[InventoryResponse],
    summary="Get out-of-stock items",
    description="Return inventory records with zero stock.",
)
def get_out_of_stock(db: Session = Depends(get_db)) -> List[InventoryResponse]:
    """Retrieve inventory records with zero stock.

    Args:
        db: SQLAlchemy session.

    Returns:
        List of ``InventoryResponse`` items with no stock.
    """
    try:
        return InventoryService.get_out_of_stock(db)
    except Exception as exc:
        logger.error("Unexpected error fetching out-of-stock inventory: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching out-of-stock items.",
        )


@router.get(
    "/by-store/{store_id}",
    response_model=List[InventoryResponse],
    summary="Get inventory by store",
    description="Return all inventory records for a given store.",
)
def get_inventory_by_store(
    store_id: int,
    db: Session = Depends(get_db),
) -> List[InventoryResponse]:
    """Retrieve all inventory records for a specific store.

    Args:
        store_id: Primary key of the store.
        db:       SQLAlchemy session.

    Returns:
        List of ``InventoryResponse`` items for the store.
    """
    try:
        return InventoryService.get_inventory_by_store(db, store_id)
    except Exception as exc:
        logger.error("Unexpected error fetching inventory for store_id=%s: %s", store_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching store inventory.",
        )


# ---------------------------------------------------------------------------
# CRUD endpoints
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=InventoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an inventory record",
    description="Add a stock record for a product at a store.  Each store/product pair must be unique.",
    responses={
        400: {"description": "Invalid input or duplicate store/product pair"},
        500: {"description": "Internal server error"},
    },
)
def create_inventory(data: InventoryCreate, db: Session = Depends(get_db)) -> InventoryResponse:
    """Create a new inventory record.

    Args:
        data: Inventory creation payload validated by ``InventoryCreate``.
        db:   SQLAlchemy session injected via ``get_db``.

    Returns:
        The newly-created record as an ``InventoryResponse``.

    Raises:
        HTTPException 400: If a record for the same store/product exists.
        HTTPException 500: On unexpected server-side errors.
    """
    try:
        return InventoryService.create_inventory(db, data)
    except ValueError as exc:
        logger.warning("Inventory creation failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected error creating inventory: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the inventory record.",
        )


@router.get(
    "",
    response_model=PaginatedResponse[InventoryResponse],
    summary="List inventory records",
    description="Return a paginated list of inventory records.",
)
def list_inventory(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=100, ge=1, le=500, description="Maximum records to return"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[InventoryResponse]:
    """Retrieve a paginated list of inventory records.

    Args:
        skip:  Offset for pagination.
        limit: Page size.
        db:    SQLAlchemy session.

    Returns:
        ``PaginatedResponse`` containing inventory records.
    """
    try:
        return InventoryService.get_inventories(db, skip=skip, limit=limit)
    except Exception as exc:
        logger.error("Unexpected error listing inventory: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while listing inventory.",
        )


@router.get(
    "/{inventory_id}",
    response_model=InventoryResponse,
    summary="Get an inventory record by ID",
    responses={404: {"description": "Inventory record not found"}},
)
def get_inventory(inventory_id: int, db: Session = Depends(get_db)) -> InventoryResponse:
    """Retrieve a single inventory record by primary key.

    Args:
        inventory_id: Primary key of the inventory record.
        db:           SQLAlchemy session.

    Returns:
        The matching ``InventoryResponse``.

    Raises:
        HTTPException 404: If the record does not exist.
    """
    try:
        return InventoryService.get_inventory(db, inventory_id)
    except ValueError as exc:
        logger.info("Inventory record not found: %s", exc)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected error retrieving inventory id=%s: %s", inventory_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving the inventory record.",
        )


@router.put(
    "/{inventory_id}",
    response_model=InventoryResponse,
    summary="Update an inventory record",
    responses={
        400: {"description": "Invalid input or duplicate store/product pair"},
        404: {"description": "Inventory record not found"},
    },
)
def update_inventory(
    inventory_id: int,
    data: InventoryUpdate,
    db: Session = Depends(get_db),
) -> InventoryResponse:
    """Update an existing inventory record.

    Only fields present in the request body are modified (partial update).

    Args:
        inventory_id: Primary key of the inventory record to update.
        data:         Partial-update payload.
        db:           SQLAlchemy session.

    Returns:
        The updated ``InventoryResponse``.

    Raises:
        HTTPException 404: If the record is not found.
        HTTPException 400: If the new store/product pair already exists.
    """
    try:
        return InventoryService.update_inventory(db, inventory_id, data)
    except ValueError as exc:
        error_msg = str(exc)
        if "not found" in error_msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
    except Exception as exc:
        logger.error("Unexpected error updating inventory id=%s: %s", inventory_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while updating the inventory record.",
        )


@router.delete(
    "/{inventory_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an inventory record",
    responses={404: {"description": "Inventory record not found"}},
)
def delete_inventory(inventory_id: int, db: Session = Depends(get_db)) -> None:
    """Delete an inventory record by ID.

    Args:
        inventory_id: Primary key of the record to delete.
        db:           SQLAlchemy session.

    Raises:
        HTTPException 404: If the record does not exist.
    """
    try:
        InventoryService.delete_inventory(db, inventory_id)
    except ValueError as exc:
        logger.info("Inventory delete failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected error deleting inventory id=%s: %s", inventory_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while deleting the inventory record.",
        )
