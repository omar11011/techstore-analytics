"""
Category API router.

Exposes RESTful endpoints for managing product categories.

Endpoints
---------
POST   /categories          – Create a new category
GET    /categories          – List categories (paginated)
GET    /categories/{id}     – Retrieve a single category
PUT    /categories/{id}     – Update a category
DELETE /categories/{id}     – Delete a category
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.schemas.schemas import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    PaginatedResponse,
)
from app.services.category_service import CategoryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new category",
    description="Add a product category.  Name must be unique.",
    responses={
        400: {"description": "Invalid input or duplicate name"},
        500: {"description": "Internal server error"},
    },
)
def create_category(data: CategoryCreate, db: Session = Depends(get_db)) -> CategoryResponse:
    """Create a new category record.

    Args:
        data: Category creation payload validated by ``CategoryCreate``.
        db:   SQLAlchemy session injected via ``get_db``.

    Returns:
        The newly-created category as a ``CategoryResponse``.

    Raises:
        HTTPException 400: If a category with the same name already exists.
        HTTPException 500: On unexpected server-side errors.
    """
    try:
        return CategoryService.create_category(db, data)
    except ValueError as exc:
        logger.warning("Category creation failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected error creating category: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the category.",
        )


@router.get(
    "",
    response_model=PaginatedResponse[CategoryResponse],
    summary="List categories",
    description="Return a paginated list of product categories.",
)
def list_categories(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=100, ge=1, le=500, description="Maximum records to return"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[CategoryResponse]:
    """Retrieve a paginated list of categories.

    Args:
        skip:  Offset for pagination.
        limit: Page size.
        db:    SQLAlchemy session.

    Returns:
        ``PaginatedResponse`` containing category records.
    """
    try:
        return CategoryService.get_categories(db, skip=skip, limit=limit)
    except Exception as exc:
        logger.error("Unexpected error listing categories: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while listing categories.",
        )


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Get a category by ID",
    responses={404: {"description": "Category not found"}},
)
def get_category(category_id: int, db: Session = Depends(get_db)) -> CategoryResponse:
    """Retrieve a single category by primary key.

    Args:
        category_id: Primary key of the category.
        db:          SQLAlchemy session.

    Returns:
        The matching ``CategoryResponse``.

    Raises:
        HTTPException 404: If the category does not exist.
    """
    try:
        return CategoryService.get_category(db, category_id)
    except ValueError as exc:
        logger.info("Category not found: %s", exc)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected error retrieving category id=%s: %s", category_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving the category.",
        )


@router.put(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Update a category",
    responses={
        400: {"description": "Invalid input"},
        404: {"description": "Category not found"},
    },
)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
) -> CategoryResponse:
    """Update an existing category.

    Only fields present in the request body are modified (partial update).

    Args:
        category_id: Primary key of the category to update.
        data:        Partial-update payload.
        db:          SQLAlchemy session.

    Returns:
        The updated ``CategoryResponse``.

    Raises:
        HTTPException 404: If the category is not found.
        HTTPException 400: If the new name conflicts.
    """
    try:
        return CategoryService.update_category(db, category_id, data)
    except ValueError as exc:
        error_msg = str(exc)
        if "not found" in error_msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
    except Exception as exc:
        logger.error("Unexpected error updating category id=%s: %s", category_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while updating the category.",
        )


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a category",
    responses={404: {"description": "Category not found"}},
)
def delete_category(category_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a category by ID.

    Args:
        category_id: Primary key of the category to delete.
        db:          SQLAlchemy session.

    Raises:
        HTTPException 404: If the category does not exist.
    """
    try:
        CategoryService.delete_category(db, category_id)
    except ValueError as exc:
        logger.info("Category delete failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected error deleting category id=%s: %s", category_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while deleting the category.",
        )
