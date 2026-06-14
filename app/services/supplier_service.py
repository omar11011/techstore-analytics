"""
Supplier service layer.

Orchestrates business logic for supplier-related operations, delegating
persistence to ``SupplierRepository`` and converting ORM models to
Pydantic response schemas.
"""

from __future__ import annotations

import logging
import math
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.models import Supplier
from app.repositories.supplier_repository import SupplierRepository
from app.schemas.schemas import (
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
    SupplierSales,
    PaginatedResponse,
)

logger = logging.getLogger(__name__)

_supplier_repo = SupplierRepository()


class SupplierService:
    """Business logic for ``Supplier`` entities."""

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    @staticmethod
    def create_supplier(db: Session, data: SupplierCreate) -> SupplierResponse:
        """Create a new supplier.

        Raises ``ValueError`` if a supplier with the same email exists.
        """
        try:
            if data.email:
                existing = (
                    db.query(Supplier).filter(Supplier.email == data.email).first()
                )
                if existing:
                    raise ValueError(
                        f"Supplier with email '{data.email}' already exists"
                    )

            supplier = _supplier_repo.create(
                db,
                company_name=data.company_name,
                contact_name=data.contact_name,
                email=data.email,
                phone=data.phone,
                country=data.country,
            )
            db.commit()
            db.refresh(supplier)
            logger.info("Created supplier id=%s", supplier.id)
            return SupplierResponse.model_validate(supplier)
        except ValueError:
            raise
        except Exception as exc:
            db.rollback()
            logger.error("Failed to create supplier: %s", exc)
            raise

    # ------------------------------------------------------------------
    # READ
    # ------------------------------------------------------------------

    @staticmethod
    def get_supplier(db: Session, id: int) -> SupplierResponse:
        """Retrieve a single supplier by ID.

        Raises ``ValueError`` if the supplier is not found.
        """
        try:
            supplier = _supplier_repo.get_by_id(db, id)
            if supplier is None:
                raise ValueError(f"Supplier with id={id} not found")
            return SupplierResponse.model_validate(supplier)
        except ValueError:
            raise
        except Exception as exc:
            logger.error("Failed to get supplier id=%s: %s", id, exc)
            raise

    @staticmethod
    def get_suppliers(
        db: Session,
        skip: int = 0,
        limit: int = 100,
    ) -> PaginatedResponse[SupplierResponse]:
        """Return a paginated list of suppliers."""
        try:
            suppliers = _supplier_repo.get_all(db, skip, limit)
            total = _supplier_repo.count(db)
            items = [SupplierResponse.model_validate(s) for s in suppliers]
            page = (skip // limit) + 1 if limit > 0 else 1
            pages = math.ceil(total / limit) if limit > 0 else 0
            return PaginatedResponse[SupplierResponse](
                items=items, total=total, page=page, per_page=limit, pages=pages
            )
        except Exception as exc:
            logger.error("Failed to list suppliers: %s", exc)
            raise

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------

    @staticmethod
    def update_supplier(db: Session, id: int, data: SupplierUpdate) -> SupplierResponse:
        """Update an existing supplier.

        Raises ``ValueError`` if the supplier is not found.
        """
        try:
            update_fields = data.model_dump(exclude_unset=True)
            if not update_fields:
                return SupplierService.get_supplier(db, id)

            if "email" in update_fields and update_fields["email"]:
                existing = (
                    db.query(Supplier)
                    .filter(Supplier.email == update_fields["email"])
                    .first()
                )
                if existing and existing.id != id:
                    raise ValueError(
                        f"Email '{update_fields['email']}' is already in use"
                    )

            supplier = _supplier_repo.update(db, id, **update_fields)
            if supplier is None:
                raise ValueError(f"Supplier with id={id} not found")
            db.commit()
            db.refresh(supplier)
            logger.info("Updated supplier id=%s", id)
            return SupplierResponse.model_validate(supplier)
        except ValueError:
            raise
        except Exception as exc:
            db.rollback()
            logger.error("Failed to update supplier id=%s: %s", id, exc)
            raise

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------

    @staticmethod
    def delete_supplier(db: Session, id: int) -> bool:
        """Delete a supplier by ID.

        Raises ``ValueError`` if the supplier is not found.
        """
        try:
            deleted = _supplier_repo.delete(db, id)
            if not deleted:
                raise ValueError(f"Supplier with id={id} not found")
            db.commit()
            logger.info("Deleted supplier id=%s", id)
            return True
        except ValueError:
            raise
        except Exception as exc:
            db.rollback()
            logger.error("Failed to delete supplier id=%s: %s", id, exc)
            raise

    # ------------------------------------------------------------------
    # ANALYTICS
    # ------------------------------------------------------------------

    @staticmethod
    def get_supplier_sales(db: Session) -> List[SupplierSales]:
        """Return revenue breakdown per supplier."""
        try:
            rows = _supplier_repo.get_supplier_sales(db)
            return [SupplierSales(**r) for r in rows]
        except Exception as exc:
            logger.error("Failed to get supplier sales: %s", exc)
            raise
