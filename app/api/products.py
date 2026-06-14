"""
Product API router.

Exposes RESTful endpoints for managing product records, including
CRUD operations, filtered / paginated listing, and search.

Endpoints
---------
POST   /products          – Create a new product
GET    /products          – List products (paginated, filterable, searchable)
GET    /products/{id}     – Retrieve a single product
PUT    /products/{id}     – Update a product
DELETE /products/{id}     – Delete a product
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.schemas.schemas import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    PaginatedResponse,
)
from app.services.product_service import ProductService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/products", tags=["Products"])


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
    description="Add a product to the catalogue.  SKU must be unique; price must exceed cost.",
    responses={
        400: {"description": "Invalid input or duplicate SKU"},
        500: {"description": "Internal server error"},
    },
)
def create_product(data: ProductCreate, db: Session = Depends(get_db)) -> ProductResponse:
    """Create a new product record.

    Args:
        data: Product creation payload validated by ``ProductCreate``.
        db:   SQLAlchemy session injected via ``get_db``.

    Returns:
        The newly-created product as a ``ProductResponse``.

    Raises:
        HTTPException 400: If the SKU is already in use.
        HTTPException 500: On unexpected server-side errors.
    """
    try:
        return ProductService.create_product(db, data)
    except ValueError as exc:
        logger.warning("Product creation failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected error creating product: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the product.",
        )


@router.get(
    "",
    response_model=PaginatedResponse[ProductResponse],
    summary="List products",
    description=(
        "Return a paginated list of products with optional filters for "
        "category, supplier, price range, and full-text search."
    ),
)
def list_products(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=100, ge=1, le=500, description="Maximum records to return"),
    category_id: Optional[int] = Query(default=None, description="Filter by category ID"),
    supplier_id: Optional[int] = Query(default=None, description="Filter by supplier ID"),
    min_price: Optional[float] = Query(default=None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(default=None, ge=0, description="Maximum price filter"),
    search: Optional[str] = Query(default=None, description="Full-text search on name / description"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[ProductResponse]:
    """Retrieve a paginated, filterable list of products.

    Args:
        skip:        Offset for pagination.
        limit:       Page size.
        category_id: Optional category filter.
        supplier_id: Optional supplier filter.
        min_price:   Optional minimum price.
        max_price:   Optional maximum price.
        search:      Optional search term (matches name/description).
        db:          SQLAlchemy session.

    Returns:
        ``PaginatedResponse`` containing matching products.
    """
    try:
        return ProductService.get_products(
            db,
            skip=skip,
            limit=limit,
            category_id=category_id,
            supplier_id=supplier_id,
            min_price=min_price,
            max_price=max_price,
            search=search,
        )
    except Exception as exc:
        logger.error("Unexpected error listing products: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while listing products.",
        )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get a product by ID",
    responses={404: {"description": "Product not found"}},
)
def get_product(product_id: int, db: Session = Depends(get_db)) -> ProductResponse:
    """Retrieve a single product by primary key.

    Args:
        product_id: Primary key of the product.
        db:         SQLAlchemy session.

    Returns:
        The matching ``ProductResponse``.

    Raises:
        HTTPException 404: If the product does not exist.
    """
    try:
        return ProductService.get_product(db, product_id)
    except ValueError as exc:
        logger.info("Product not found: %s", exc)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected error retrieving product id=%s: %s", product_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving the product.",
        )


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update a product",
    responses={
        400: {"description": "Invalid input or duplicate SKU"},
        404: {"description": "Product not found"},
    },
)
def update_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
) -> ProductResponse:
    """Update an existing product.

    Only fields present in the request body are modified (partial update).

    Args:
        product_id: Primary key of the product to update.
        data:       Partial-update payload.
        db:         SQLAlchemy session.

    Returns:
        The updated ``ProductResponse``.

    Raises:
        HTTPException 404: If the product is not found.
        HTTPException 400: If the new SKU is already in use.
    """
    try:
        return ProductService.update_product(db, product_id, data)
    except ValueError as exc:
        error_msg = str(exc)
        if "not found" in error_msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
    except Exception as exc:
        logger.error("Unexpected error updating product id=%s: %s", product_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while updating the product.",
        )


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product",
    responses={404: {"description": "Product not found"}},
)
def delete_product(product_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a product by ID.

    Args:
        product_id: Primary key of the product to delete.
        db:         SQLAlchemy session.

    Raises:
        HTTPException 404: If the product does not exist.
    """
    try:
        ProductService.delete_product(db, product_id)
    except ValueError as exc:
        logger.info("Product delete failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected error deleting product id=%s: %s", product_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while deleting the product.",
        )
