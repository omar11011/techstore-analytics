"""
Inventory service layer.

Orchestrates business logic for inventory-related operations, delegating
persistence to ``InventoryRepository`` and converting ORM models to
Pydantic response schemas.
"""

from __future__ import annotations

import logging
import math
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.models import Inventory
from app.repositories.inventory_repository import InventoryRepository
from app.schemas.schemas import (
    InventoryCreate,
    InventoryUpdate,
    InventoryResponse,
    PaginatedResponse,
)

logger = logging.getLogger(__name__)

_inventory_repo = InventoryRepository()


class InventoryService:
    """Business logic for ``Inventory`` entities."""

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    @staticmethod
    def create_inventory(db: Session, data: InventoryCreate) -> InventoryResponse:
        """Create a new inventory record.

        Raises ``ValueError`` if a record for the same store/product pair
        already exists.
        """
        try:
            existing = _inventory_repo.get_by_store_product(
                db, data.store_id, data.product_id
            )
            if existing:
                raise ValueError(
                    f"Inventory record already exists for "
                    f"store_id={data.store_id}, product_id={data.product_id}"
                )

            inventory = _inventory_repo.create(
                db,
                store_id=data.store_id,
                product_id=data.product_id,
                stock_quantity=data.stock_quantity,
            )
            db.commit()
            db.refresh(inventory)
            logger.info(
                "Created inventory id=%s (store=%s, product=%s)",
                inventory.id, data.store_id, data.product_id,
            )
            return InventoryResponse.model_validate(inventory)
        except ValueError:
            raise
        except Exception as exc:
            db.rollback()
            logger.error("Failed to create inventory: %s", exc)
            raise

    # ------------------------------------------------------------------
    # READ
    # ------------------------------------------------------------------

    @staticmethod
    def get_inventory(db: Session, id: int) -> InventoryResponse:
        """Retrieve a single inventory record by ID.

        Raises ``ValueError`` if the record is not found.
        """
        try:
            inventory = _inventory_repo.get_by_id(db, id)
            if inventory is None:
                raise ValueError(f"Inventory record with id={id} not found")
            return InventoryResponse.model_validate(inventory)
        except ValueError:
            raise
        except Exception as exc:
            logger.error("Failed to get inventory id=%s: %s", id, exc)
            raise

    @staticmethod
    def get_inventories(
        db: Session,
        skip: int = 0,
        limit: int = 100,
    ) -> PaginatedResponse[InventoryResponse]:
        """Return a paginated list of inventory records."""
        try:
            records = _inventory_repo.get_all(db, skip, limit)
            total = _inventory_repo.count(db)
            items = [InventoryResponse.model_validate(r) for r in records]
            page = (skip // limit) + 1 if limit > 0 else 1
            pages = math.ceil(total / limit) if limit > 0 else 0
            return PaginatedResponse[InventoryResponse](
                items=items, total=total, page=page, per_page=limit, pages=pages
            )
        except Exception as exc:
            logger.error("Failed to list inventories: %s", exc)
            raise

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------

    @staticmethod
    def update_inventory(db: Session, id: int, data: InventoryUpdate) -> InventoryResponse:
        """Update an existing inventory record.

        Raises ``ValueError`` if the record is not found.
        """
        try:
            update_fields = data.model_dump(exclude_unset=True)
            if not update_fields:
                return InventoryService.get_inventory(db, id)

            # If store/product is changing, check uniqueness
            if "store_id" in update_fields or "product_id" in update_fields:
                current = _inventory_repo.get_by_id(db, id)
                if current is None:
                    raise ValueError(f"Inventory record with id={id} not found")
                new_store = update_fields.get("store_id", current.store_id)
                new_product = update_fields.get("product_id", current.product_id)
                dup = _inventory_repo.get_by_store_product(db, new_store, new_product)
                if dup and dup.id != id:
                    raise ValueError(
                        f"Inventory record already exists for "
                        f"store_id={new_store}, product_id={new_product}"
                    )

            inventory = _inventory_repo.update(db, id, **update_fields)
            if inventory is None:
                raise ValueError(f"Inventory record with id={id} not found")
            db.commit()
            db.refresh(inventory)
            logger.info("Updated inventory id=%s", id)
            return InventoryResponse.model_validate(inventory)
        except ValueError:
            raise
        except Exception as exc:
            db.rollback()
            logger.error("Failed to update inventory id=%s: %s", id, exc)
            raise

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------

    @staticmethod
    def delete_inventory(db: Session, id: int) -> bool:
        """Delete an inventory record by ID.

        Raises ``ValueError`` if the record is not found.
        """
        try:
            deleted = _inventory_repo.delete(db, id)
            if not deleted:
                raise ValueError(f"Inventory record with id={id} not found")
            db.commit()
            logger.info("Deleted inventory id=%s", id)
            return True
        except ValueError:
            raise
        except Exception as exc:
            db.rollback()
            logger.error("Failed to delete inventory id=%s: %s", id, exc)
            raise

    # ------------------------------------------------------------------
    # ANALYTICS
    # ------------------------------------------------------------------

    @staticmethod
    def get_low_stock(db: Session, threshold: int = 10) -> List[InventoryResponse]:
        """Return inventory records with stock below *threshold*."""
        try:
            records = _inventory_repo.get_low_stock(db, threshold)
            return [InventoryResponse.model_validate(r) for r in records]
        except Exception as exc:
            logger.error("Failed to get low stock: %s", exc)
            raise

    @staticmethod
    def get_inventory_by_store(db: Session, store_id: int) -> List[InventoryResponse]:
        """Return all inventory records for a given store."""
        try:
            records = _inventory_repo.get_by_store(db, store_id)
            return [InventoryResponse.model_validate(r) for r in records]
        except Exception as exc:
            logger.error("Failed to get inventory by store: %s", exc)
            raise

    @staticmethod
    def get_out_of_stock(db: Session) -> List[InventoryResponse]:
        """Return inventory records with zero stock."""
        try:
            records = _inventory_repo.get_out_of_stock(db)
            return [InventoryResponse.model_validate(r) for r in records]
        except Exception as exc:
            logger.error("Failed to get out of stock: %s", exc)
            raise
