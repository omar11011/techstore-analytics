"""
Shipment service layer.

Orchestrates business logic for shipment-related operations, delegating
persistence to ``ShipmentRepository`` and converting ORM models to
Pydantic response schemas.
"""

from __future__ import annotations

import logging
import math
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.models import Shipment
from app.repositories.shipment_repository import ShipmentRepository
from app.schemas.schemas import (
    ShipmentCreate,
    ShipmentUpdate,
    ShipmentResponse,
    DeliveryPerformance,
    PaginatedResponse,
)

logger = logging.getLogger(__name__)

_shipment_repo = ShipmentRepository()


class ShipmentService:
    """Business logic for ``Shipment`` entities."""

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    @staticmethod
    def create_shipment(db: Session, data: ShipmentCreate) -> ShipmentResponse:
        """Create a new shipment.

        Raises ``ValueError`` if a shipment already exists for the order.
        """
        try:
            existing = _shipment_repo.get_by_order(db, data.order_id)
            if existing:
                raise ValueError(
                    f"Shipment already exists for order_id={data.order_id}"
                )

            shipment = _shipment_repo.create(
                db,
                order_id=data.order_id,
                shipment_status=data.shipment_status or "pending",
                tracking_number=data.tracking_number,
                shipped_date=data.shipped_date,
                delivery_date=data.delivery_date,
            )
            db.commit()
            db.refresh(shipment)
            logger.info("Created shipment id=%s for order_id=%s", shipment.id, data.order_id)
            return ShipmentResponse.model_validate(shipment)
        except ValueError:
            raise
        except Exception as exc:
            db.rollback()
            logger.error("Failed to create shipment: %s", exc)
            raise

    # ------------------------------------------------------------------
    # READ
    # ------------------------------------------------------------------

    @staticmethod
    def get_shipment(db: Session, id: int) -> ShipmentResponse:
        """Retrieve a single shipment by ID.

        Raises ``ValueError`` if the shipment is not found.
        """
        try:
            shipment = _shipment_repo.get_by_id(db, id)
            if shipment is None:
                raise ValueError(f"Shipment with id={id} not found")
            return ShipmentResponse.model_validate(shipment)
        except ValueError:
            raise
        except Exception as exc:
            logger.error("Failed to get shipment id=%s: %s", id, exc)
            raise

    @staticmethod
    def get_shipments(
        db: Session,
        skip: int = 0,
        limit: int = 100,
    ) -> PaginatedResponse[ShipmentResponse]:
        """Return a paginated list of shipments."""
        try:
            shipments = _shipment_repo.get_all(db, skip, limit)
            total = _shipment_repo.count(db)
            items = [ShipmentResponse.model_validate(s) for s in shipments]
            page = (skip // limit) + 1 if limit > 0 else 1
            pages = math.ceil(total / limit) if limit > 0 else 0
            return PaginatedResponse[ShipmentResponse](
                items=items, total=total, page=page, per_page=limit, pages=pages
            )
        except Exception as exc:
            logger.error("Failed to list shipments: %s", exc)
            raise

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------

    @staticmethod
    def update_shipment(db: Session, id: int, data: ShipmentUpdate) -> ShipmentResponse:
        """Update an existing shipment.

        Raises ``ValueError`` if the shipment is not found.
        """
        try:
            update_fields = data.model_dump(exclude_unset=True)
            if not update_fields:
                return ShipmentService.get_shipment(db, id)

            shipment = _shipment_repo.update(db, id, **update_fields)
            if shipment is None:
                raise ValueError(f"Shipment with id={id} not found")
            db.commit()
            db.refresh(shipment)
            logger.info("Updated shipment id=%s", id)
            return ShipmentResponse.model_validate(shipment)
        except ValueError:
            raise
        except Exception as exc:
            db.rollback()
            logger.error("Failed to update shipment id=%s: %s", id, exc)
            raise

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------

    @staticmethod
    def delete_shipment(db: Session, id: int) -> bool:
        """Delete a shipment by ID.

        Raises ``ValueError`` if the shipment is not found.
        """
        try:
            deleted = _shipment_repo.delete(db, id)
            if not deleted:
                raise ValueError(f"Shipment with id={id} not found")
            db.commit()
            logger.info("Deleted shipment id=%s", id)
            return True
        except ValueError:
            raise
        except Exception as exc:
            db.rollback()
            logger.error("Failed to delete shipment id=%s: %s", id, exc)
            raise

    # ------------------------------------------------------------------
    # ANALYTICS
    # ------------------------------------------------------------------

    @staticmethod
    def get_pending_shipments(db: Session) -> List[ShipmentResponse]:
        """Return shipments that have not yet been delivered."""
        try:
            shipments = _shipment_repo.get_pending_shipments(db)
            return [ShipmentResponse.model_validate(s) for s in shipments]
        except Exception as exc:
            logger.error("Failed to get pending shipments: %s", exc)
            raise

    @staticmethod
    def get_delivery_performance(db: Session) -> DeliveryPerformance:
        """Return aggregate delivery performance metrics."""
        try:
            data = _shipment_repo.get_delivery_performance(db)
            return DeliveryPerformance(**data)
        except Exception as exc:
            logger.error("Failed to get delivery performance: %s", exc)
            raise
