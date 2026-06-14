"""
Category service layer.

Orchestrates business logic for category-related operations, delegating
persistence to ``CategoryRepository`` and converting ORM models to
Pydantic response schemas.
"""

from __future__ import annotations

import logging
import math
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.models import Category
from app.repositories.category_repository import CategoryRepository
from app.schemas.schemas import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategorySales,
    PaginatedResponse,
)

logger = logging.getLogger(__name__)

_category_repo = CategoryRepository()


class CategoryService:
    """Business logic for ``Category`` entities."""

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    @staticmethod
    def create_category(db: Session, data: CategoryCreate) -> CategoryResponse:
        """Create a new category.

        Raises ``ValueError`` if a category with the same name exists.
        """
        try:
            existing = (
                db.query(Category).filter(Category.name == data.name).first()
            )
            if existing:
                raise ValueError(f"Category with name '{data.name}' already exists")

            category = _category_repo.create(
                db,
                name=data.name,
                description=data.description,
            )
            db.commit()
            db.refresh(category)
            logger.info("Created category id=%s", category.id)
            return CategoryResponse.model_validate(category)
        except ValueError:
            raise
        except Exception as exc:
            db.rollback()
            logger.error("Failed to create category: %s", exc)
            raise

    # ------------------------------------------------------------------
    # READ
    # ------------------------------------------------------------------

    @staticmethod
    def get_category(db: Session, id: int) -> CategoryResponse:
        """Retrieve a single category by ID.

        Raises ``ValueError`` if the category is not found.
        """
        try:
            category = _category_repo.get_by_id(db, id)
            if category is None:
                raise ValueError(f"Category with id={id} not found")
            return CategoryResponse.model_validate(category)
        except ValueError:
            raise
        except Exception as exc:
            logger.error("Failed to get category id=%s: %s", id, exc)
            raise

    @staticmethod
    def get_categories(
        db: Session,
        skip: int = 0,
        limit: int = 100,
    ) -> PaginatedResponse[CategoryResponse]:
        """Return a paginated list of categories."""
        try:
            categories = _category_repo.get_all(db, skip, limit)
            total = _category_repo.count(db)
            items = [CategoryResponse.model_validate(c) for c in categories]
            page = (skip // limit) + 1 if limit > 0 else 1
            pages = math.ceil(total / limit) if limit > 0 else 0
            return PaginatedResponse[CategoryResponse](
                items=items, total=total, page=page, per_page=limit, pages=pages
            )
        except Exception as exc:
            logger.error("Failed to list categories: %s", exc)
            raise

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------

    @staticmethod
    def update_category(db: Session, id: int, data: CategoryUpdate) -> CategoryResponse:
        """Update an existing category.

        Raises ``ValueError`` if the category is not found.
        """
        try:
            update_fields = data.model_dump(exclude_unset=True)
            if not update_fields:
                return CategoryService.get_category(db, id)

            category = _category_repo.update(db, id, **update_fields)
            if category is None:
                raise ValueError(f"Category with id={id} not found")
            db.commit()
            db.refresh(category)
            logger.info("Updated category id=%s", id)
            return CategoryResponse.model_validate(category)
        except ValueError:
            raise
        except Exception as exc:
            db.rollback()
            logger.error("Failed to update category id=%s: %s", id, exc)
            raise

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------

    @staticmethod
    def delete_category(db: Session, id: int) -> bool:
        """Delete a category by ID.

        Raises ``ValueError`` if the category is not found.
        """
        try:
            deleted = _category_repo.delete(db, id)
            if not deleted:
                raise ValueError(f"Category with id={id} not found")
            db.commit()
            logger.info("Deleted category id=%s", id)
            return True
        except ValueError:
            raise
        except Exception as exc:
            db.rollback()
            logger.error("Failed to delete category id=%s: %s", id, exc)
            raise

    # ------------------------------------------------------------------
    # ANALYTICS
    # ------------------------------------------------------------------

    @staticmethod
    def get_category_sales(db: Session) -> List[CategorySales]:
        """Return revenue breakdown per category."""
        try:
            rows = _category_repo.get_category_sales(db)
            return [CategorySales(**r) for r in rows]
        except Exception as exc:
            logger.error("Failed to get category sales: %s", exc)
            raise
