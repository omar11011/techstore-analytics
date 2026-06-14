"""
Store service layer.

Orchestrates business logic for store-related operations, delegating
persistence to ``StoreRepository`` and converting ORM models to
Pydantic response schemas.
"""

from __future__ import annotations

import logging
import math
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.models import Store
from app.repositories.store_repository import StoreRepository
from app.schemas.schemas import (
    StoreCreate,
    StoreUpdate,
    StoreResponse,
    StorePerformance,
    PaginatedResponse,
)

logger = logging.getLogger(__name__)

_store_repo = StoreRepository()


class StoreService:
    """Business logic for ``Store`` entities."""

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    @staticmethod
    def create_store(db: Session, data: StoreCreate) -> StoreResponse:
        """Create a new store."""
        try:
            store = _store_repo.create(
                db,
                name=data.name,
                city=data.city,
                country=data.country,
            )
            db.commit()
            db.refresh(store)
            logger.info("Created store id=%s", store.id)
            return StoreResponse.model_validate(store)
        except Exception as exc:
            db.rollback()
            logger.error("Failed to create store: %s", exc)
            raise

    # ------------------------------------------------------------------
    # READ
    # ------------------------------------------------------------------

    @staticmethod
    def get_store(db: Session, id: int) -> StoreResponse:
        """Retrieve a single store by ID.

        Raises ``ValueError`` if the store is not found.
        """
        try:
            store = _store_repo.get_by_id(db, id)
            if store is None:
                raise ValueError(f"Store with id={id} not found")
            return StoreResponse.model_validate(store)
        except ValueError:
            raise
        except Exception as exc:
            logger.error("Failed to get store id=%s: %s", id, exc)
            raise

    @staticmethod
    def get_stores(
        db: Session,
        skip: int = 0,
        limit: int = 100,
    ) -> PaginatedResponse[StoreResponse]:
        """Return a paginated list of stores."""
        try:
            stores = _store_repo.get_all(db, skip, limit)
            total = _store_repo.count(db)
            items = [StoreResponse.model_validate(s) for s in stores]
            page = (skip // limit) + 1 if limit > 0 else 1
            pages = math.ceil(total / limit) if limit > 0 else 0
            return PaginatedResponse[StoreResponse](
                items=items, total=total, page=page, per_page=limit, pages=pages
            )
        except Exception as exc:
            logger.error("Failed to list stores: %s", exc)
            raise

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------

    @staticmethod
    def update_store(db: Session, id: int, data: StoreUpdate) -> StoreResponse:
        """Update an existing store.

        Raises ``ValueError`` if the store is not found.
        """
        try:
            update_fields = data.model_dump(exclude_unset=True)
            if not update_fields:
                return StoreService.get_store(db, id)

            store = _store_repo.update(db, id, **update_fields)
            if store is None:
                raise ValueError(f"Store with id={id} not found")
            db.commit()
            db.refresh(store)
            logger.info("Updated store id=%s", id)
            return StoreResponse.model_validate(store)
        except ValueError:
            raise
        except Exception as exc:
            db.rollback()
            logger.error("Failed to update store id=%s: %s", id, exc)
            raise

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------

    @staticmethod
    def delete_store(db: Session, id: int) -> bool:
        """Delete a store by ID.

        Raises ``ValueError`` if the store is not found.
        """
        try:
            deleted = _store_repo.delete(db, id)
            if not deleted:
                raise ValueError(f"Store with id={id} not found")
            db.commit()
            logger.info("Deleted store id=%s", id)
            return True
        except ValueError:
            raise
        except Exception as exc:
            db.rollback()
            logger.error("Failed to delete store id=%s: %s", id, exc)
            raise

    # ------------------------------------------------------------------
    # ANALYTICS
    # ------------------------------------------------------------------

    @staticmethod
    def get_store_performance(db: Session) -> List[StorePerformance]:
        """Return performance metrics per store."""
        try:
            rows = _store_repo.get_store_performance(db)
            return [StorePerformance(**r) for r in rows]
        except Exception as exc:
            logger.error("Failed to get store performance: %s", exc)
            raise
