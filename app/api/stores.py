"""
Store API router.

Exposes RESTful endpoints for managing store location records.

Endpoints
---------
POST   /stores          – Create a new store
GET    /stores          – List stores (paginated)
GET    /stores/{id}     – Retrieve a single store
PUT    /stores/{id}     – Update a store
DELETE /stores/{id}     – Delete a store
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.schemas.schemas import (
    StoreCreate,
    StoreUpdate,
    StoreResponse,
    PaginatedResponse,
)
from app.services.store_service import StoreService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stores", tags=["Stores"])


@router.post(
    "",
    response_model=StoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new store",
    description="Add a physical or virtual store location.",
    responses={500: {"description": "Internal server error"}},
)
def create_store(data: StoreCreate, db: Session = Depends(get_db)) -> StoreResponse:
    """Create a new store record.

    Args:
        data: Store creation payload validated by ``StoreCreate``.
        db:   SQLAlchemy session injected via ``get_db``.

    Returns:
        The newly-created store as a ``StoreResponse``.

    Raises:
        HTTPException 500: On unexpected server-side errors.
    """
    try:
        return StoreService.create_store(db, data)
    except Exception as exc:
        logger.error("Unexpected error creating store: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the store.",
        )


@router.get(
    "",
    response_model=PaginatedResponse[StoreResponse],
    summary="List stores",
    description="Return a paginated list of store locations.",
)
def list_stores(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=100, ge=1, le=500, description="Maximum records to return"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[StoreResponse]:
    """Retrieve a paginated list of stores.

    Args:
        skip:  Offset for pagination.
        limit: Page size.
        db:    SQLAlchemy session.

    Returns:
        ``PaginatedResponse`` containing store records.
    """
    try:
        return StoreService.get_stores(db, skip=skip, limit=limit)
    except Exception as exc:
        logger.error("Unexpected error listing stores: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while listing stores.",
        )


@router.get(
    "/{store_id}",
    response_model=StoreResponse,
    summary="Get a store by ID",
    responses={404: {"description": "Store not found"}},
)
def get_store(store_id: int, db: Session = Depends(get_db)) -> StoreResponse:
    """Retrieve a single store by primary key.

    Args:
        store_id: Primary key of the store.
        db:       SQLAlchemy session.

    Returns:
        The matching ``StoreResponse``.

    Raises:
        HTTPException 404: If the store does not exist.
    """
    try:
        return StoreService.get_store(db, store_id)
    except ValueError as exc:
        logger.info("Store not found: %s", exc)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected error retrieving store id=%s: %s", store_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving the store.",
        )


@router.put(
    "/{store_id}",
    response_model=StoreResponse,
    summary="Update a store",
    responses={404: {"description": "Store not found"}},
)
def update_store(
    store_id: int,
    data: StoreUpdate,
    db: Session = Depends(get_db),
) -> StoreResponse:
    """Update an existing store.

    Only fields present in the request body are modified (partial update).

    Args:
        store_id: Primary key of the store to update.
        data:     Partial-update payload.
        db:       SQLAlchemy session.

    Returns:
        The updated ``StoreResponse``.

    Raises:
        HTTPException 404: If the store is not found.
    """
    try:
        return StoreService.update_store(db, store_id, data)
    except ValueError as exc:
        error_msg = str(exc)
        if "not found" in error_msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
    except Exception as exc:
        logger.error("Unexpected error updating store id=%s: %s", store_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while updating the store.",
        )


@router.delete(
    "/{store_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a store",
    responses={404: {"description": "Store not found"}},
)
def delete_store(store_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a store by ID.

    Args:
        store_id: Primary key of the store to delete.
        db:       SQLAlchemy session.

    Raises:
        HTTPException 404: If the store does not exist.
    """
    try:
        StoreService.delete_store(db, store_id)
    except ValueError as exc:
        logger.info("Store delete failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected error deleting store id=%s: %s", store_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while deleting the store.",
        )
