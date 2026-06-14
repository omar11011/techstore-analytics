"""
Customer API router.

Exposes RESTful endpoints for managing customer records, including
CRUD operations and filtered / paginated listing.

Endpoints
---------
POST   /customers          – Create a new customer
GET    /customers          – List customers (paginated, filterable)
GET    /customers/{id}     – Retrieve a single customer
PUT    /customers/{id}     – Update a customer
DELETE /customers/{id}     – Delete a customer
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.schemas.schemas import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    PaginatedResponse,
)
from app.services.customer_service import CustomerService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new customer",
    description="Register a new customer.  Email must be unique.",
    responses={
        400: {"description": "Invalid input or duplicate email"},
        500: {"description": "Internal server error"},
    },
)
def create_customer(data: CustomerCreate, db: Session = Depends(get_db)) -> CustomerResponse:
    """Create a new customer record.

    Args:
        data: Customer creation payload validated by ``CustomerCreate``.
        db:   SQLAlchemy session injected via ``get_db``.

    Returns:
        The newly-created customer as a ``CustomerResponse``.

    Raises:
        HTTPException 400: If the email is already registered.
        HTTPException 500: On unexpected server-side errors.
    """
    try:
        return CustomerService.create_customer(db, data)
    except ValueError as exc:
        logger.warning("Customer creation failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected error creating customer: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the customer.",
        )


@router.get(
    "",
    response_model=PaginatedResponse[CustomerResponse],
    summary="List customers",
    description="Return a paginated list of customers with optional city / country filters.",
)
def list_customers(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=100, ge=1, le=500, description="Maximum records to return"),
    city: Optional[str] = Query(default=None, description="Filter by city"),
    country: Optional[str] = Query(default=None, description="Filter by country"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[CustomerResponse]:
    """Retrieve a paginated list of customers.

    Args:
        skip:    Offset for pagination.
        limit:   Page size.
        city:    Optional city filter.
        country: Optional country filter.
        db:      SQLAlchemy session.

    Returns:
        ``PaginatedResponse`` containing matching customers.
    """
    try:
        return CustomerService.get_customers(db, skip=skip, limit=limit, city=city, country=country)
    except Exception as exc:
        logger.error("Unexpected error listing customers: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while listing customers.",
        )


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
    summary="Get a customer by ID",
    responses={404: {"description": "Customer not found"}},
)
def get_customer(customer_id: int, db: Session = Depends(get_db)) -> CustomerResponse:
    """Retrieve a single customer by primary key.

    Args:
        customer_id: Primary key of the customer.
        db:          SQLAlchemy session.

    Returns:
        The matching ``CustomerResponse``.

    Raises:
        HTTPException 404: If the customer does not exist.
    """
    try:
        return CustomerService.get_customer(db, customer_id)
    except ValueError as exc:
        logger.info("Customer not found: %s", exc)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected error retrieving customer id=%s: %s", customer_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving the customer.",
        )


@router.put(
    "/{customer_id}",
    response_model=CustomerResponse,
    summary="Update a customer",
    responses={
        400: {"description": "Invalid input or duplicate email"},
        404: {"description": "Customer not found"},
    },
)
def update_customer(
    customer_id: int,
    data: CustomerUpdate,
    db: Session = Depends(get_db),
) -> CustomerResponse:
    """Update an existing customer.

    Only fields present in the request body are modified (partial update).

    Args:
        customer_id: Primary key of the customer to update.
        data:        Partial-update payload.
        db:          SQLAlchemy session.

    Returns:
        The updated ``CustomerResponse``.

    Raises:
        HTTPException 404: If the customer is not found.
        HTTPException 400: If the new email is already in use.
    """
    try:
        return CustomerService.update_customer(db, customer_id, data)
    except ValueError as exc:
        error_msg = str(exc)
        if "not found" in error_msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
    except Exception as exc:
        logger.error("Unexpected error updating customer id=%s: %s", customer_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while updating the customer.",
        )


@router.delete(
    "/{customer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a customer",
    responses={404: {"description": "Customer not found"}},
)
def delete_customer(customer_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a customer by ID.

    Args:
        customer_id: Primary key of the customer to delete.
        db:          SQLAlchemy session.

    Raises:
        HTTPException 404: If the customer does not exist.
    """
    try:
        CustomerService.delete_customer(db, customer_id)
    except ValueError as exc:
        logger.info("Customer delete failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected error deleting customer id=%s: %s", customer_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while deleting the customer.",
        )
