"""
Supplier API router.

Exposes RESTful endpoints for managing supplier / vendor records.

Endpoints
---------
POST   /suppliers          – Create a new supplier
GET    /suppliers          – List suppliers (paginated)
GET    /suppliers/{id}     – Retrieve a single supplier
PUT    /suppliers/{id}     – Update a supplier
DELETE /suppliers/{id}     – Delete a supplier
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.schemas.schemas import (
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
    PaginatedResponse,
)
from app.services.supplier_service import SupplierService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


@router.post(
    "",
    response_model=SupplierResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new supplier",
    description="Register a supplier / vendor.  Email must be unique if provided.",
    responses={
        400: {"description": "Invalid input or duplicate email"},
        500: {"description": "Internal server error"},
    },
)
def create_supplier(data: SupplierCreate, db: Session = Depends(get_db)) -> SupplierResponse:
    """Create a new supplier record.

    Args:
        data: Supplier creation payload validated by ``SupplierCreate``.
        db:   SQLAlchemy session injected via ``get_db``.

    Returns:
        The newly-created supplier as a ``SupplierResponse``.

    Raises:
        HTTPException 400: If the email is already registered.
        HTTPException 500: On unexpected server-side errors.
    """
    try:
        return SupplierService.create_supplier(db, data)
    except ValueError as exc:
        logger.warning("Supplier creation failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected error creating supplier: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the supplier.",
        )


@router.get(
    "",
    response_model=PaginatedResponse[SupplierResponse],
    summary="List suppliers",
    description="Return a paginated list of suppliers.",
)
def list_suppliers(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=100, ge=1, le=500, description="Maximum records to return"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[SupplierResponse]:
    """Retrieve a paginated list of suppliers.

    Args:
        skip:  Offset for pagination.
        limit: Page size.
        db:    SQLAlchemy session.

    Returns:
        ``PaginatedResponse`` containing supplier records.
    """
    try:
        return SupplierService.get_suppliers(db, skip=skip, limit=limit)
    except Exception as exc:
        logger.error("Unexpected error listing suppliers: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while listing suppliers.",
        )


@router.get(
    "/{supplier_id}",
    response_model=SupplierResponse,
    summary="Get a supplier by ID",
    responses={404: {"description": "Supplier not found"}},
)
def get_supplier(supplier_id: int, db: Session = Depends(get_db)) -> SupplierResponse:
    """Retrieve a single supplier by primary key.

    Args:
        supplier_id: Primary key of the supplier.
        db:          SQLAlchemy session.

    Returns:
        The matching ``SupplierResponse``.

    Raises:
        HTTPException 404: If the supplier does not exist.
    """
    try:
        return SupplierService.get_supplier(db, supplier_id)
    except ValueError as exc:
        logger.info("Supplier not found: %s", exc)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected error retrieving supplier id=%s: %s", supplier_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving the supplier.",
        )


@router.put(
    "/{supplier_id}",
    response_model=SupplierResponse,
    summary="Update a supplier",
    responses={
        400: {"description": "Invalid input or duplicate email"},
        404: {"description": "Supplier not found"},
    },
)
def update_supplier(
    supplier_id: int,
    data: SupplierUpdate,
    db: Session = Depends(get_db),
) -> SupplierResponse:
    """Update an existing supplier.

    Only fields present in the request body are modified (partial update).

    Args:
        supplier_id: Primary key of the supplier to update.
        data:        Partial-update payload.
        db:          SQLAlchemy session.

    Returns:
        The updated ``SupplierResponse``.

    Raises:
        HTTPException 404: If the supplier is not found.
        HTTPException 400: If the new email is already in use.
    """
    try:
        return SupplierService.update_supplier(db, supplier_id, data)
    except ValueError as exc:
        error_msg = str(exc)
        if "not found" in error_msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
    except Exception as exc:
        logger.error("Unexpected error updating supplier id=%s: %s", supplier_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while updating the supplier.",
        )


@router.delete(
    "/{supplier_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a supplier",
    responses={404: {"description": "Supplier not found"}},
)
def delete_supplier(supplier_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a supplier by ID.

    Args:
        supplier_id: Primary key of the supplier to delete.
        db:          SQLAlchemy session.

    Raises:
        HTTPException 404: If the supplier does not exist.
    """
    try:
        SupplierService.delete_supplier(db, supplier_id)
    except ValueError as exc:
        logger.info("Supplier delete failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected error deleting supplier id=%s: %s", supplier_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while deleting the supplier.",
        )
