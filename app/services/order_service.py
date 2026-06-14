"""
Order service layer.

Orchestrates business logic for order-related operations including
automatic total-amount calculation from line items, status transitions,
and monthly sales reporting.
"""

from __future__ import annotations

import logging
import math
from decimal import Decimal
from typing import List, Optional

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.models import Order, OrderItem, Product
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.schemas import (
    OrderCreate,
    OrderUpdate,
    OrderResponse,
    OrderItemCreate,
    OrderItemResponse,
    MonthlySales,
    PaginatedResponse,
)

logger = logging.getLogger(__name__)

_order_repo = OrderRepository()
_product_repo = ProductRepository()


class OrderService:
    """Business logic for ``Order`` entities."""

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    @staticmethod
    def create_order(db: Session, data: OrderCreate) -> OrderResponse:
        """Create a new order together with its line items.

        The ``total_amount`` is automatically calculated from the items.
        If ``unit_price`` is not provided for an item, the product's
        current selling price is used.
        """
        try:
            # Build order header
            order = _order_repo.create(
                db,
                customer_id=data.customer_id,
                store_id=data.store_id,
                status=data.status or "pending",
                total_amount=Decimal("0"),
            )

            # Create line items
            total = Decimal("0")
            for item_data in data.items:
                unit_price = item_data.unit_price
                if unit_price is None:
                    product = _product_repo.get_by_id(db, item_data.product_id)
                    if product is None:
                        raise ValueError(
                            f"Product with id={item_data.product_id} not found"
                        )
                    unit_price = product.price

                discount = item_data.discount or Decimal("0")
                line_total = Decimal(str(unit_price)) * item_data.quantity * (
                    1 - Decimal(str(discount)) / 100
                )
                total += line_total

                _order_repo.add_order_item(
                    db,
                    order_id=order.id,
                    product_id=item_data.product_id,
                    quantity=item_data.quantity,
                    unit_price=unit_price,
                    discount=discount,
                )

            # Persist total
            order.total_amount = total
            db.flush()
            db.commit()
            db.refresh(order)
            logger.info(
                "Created order id=%s with %s items, total=%s",
                order.id, len(data.items), total,
            )
            return OrderResponse.model_validate(order)
        except ValueError:
            raise
        except Exception as exc:
            db.rollback()
            logger.error("Failed to create order: %s", exc)
            raise

    # ------------------------------------------------------------------
    # READ
    # ------------------------------------------------------------------

    @staticmethod
    def get_order(db: Session, id: int) -> OrderResponse:
        """Retrieve a single order by ID (with items).

        Raises ``ValueError`` if the order is not found.
        """
        try:
            order = _order_repo.get_by_id(db, id)
            if order is None:
                raise ValueError(f"Order with id={id} not found")
            return OrderResponse.model_validate(order)
        except ValueError:
            raise
        except Exception as exc:
            logger.error("Failed to get order id=%s: %s", id, exc)
            raise

    @staticmethod
    def get_orders(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        customer_id: Optional[int] = None,
        store_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> PaginatedResponse[OrderResponse]:
        """Return a paginated list of orders with optional filters."""
        try:
            orders = _order_repo.get_filtered(
                db, skip, limit, status, customer_id, store_id, date_from, date_to
            )
            total = _order_repo.count_filtered(
                db, status, customer_id, store_id, date_from, date_to
            )
            items = [OrderResponse.model_validate(o) for o in orders]
            page = (skip // limit) + 1 if limit > 0 else 1
            pages = math.ceil(total / limit) if limit > 0 else 0
            return PaginatedResponse[OrderResponse](
                items=items, total=total, page=page, per_page=limit, pages=pages
            )
        except Exception as exc:
            logger.error("Failed to list orders: %s", exc)
            raise

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------

    @staticmethod
    def update_order_status(db: Session, id: int, status: str) -> OrderResponse:
        """Update only the status field of an order.

        Raises ``ValueError`` if the order is not found.
        """
        try:
            order = _order_repo.update(db, id, status=status)
            if order is None:
                raise ValueError(f"Order with id={id} not found")
            db.commit()
            db.refresh(order)
            logger.info("Updated order id=%s status='%s'", id, status)
            return OrderResponse.model_validate(order)
        except ValueError:
            raise
        except Exception as exc:
            db.rollback()
            logger.error("Failed to update order status id=%s: %s", id, exc)
            raise

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------

    @staticmethod
    def delete_order(db: Session, id: int) -> bool:
        """Delete an order by ID.

        Raises ``ValueError`` if the order is not found.
        """
        try:
            deleted = _order_repo.delete(db, id)
            if not deleted:
                raise ValueError(f"Order with id={id} not found")
            db.commit()
            logger.info("Deleted order id=%s", id)
            return True
        except ValueError:
            raise
        except Exception as exc:
            db.rollback()
            logger.error("Failed to delete order id=%s: %s", id, exc)
            raise

    # ------------------------------------------------------------------
    # ORDER ITEMS
    # ------------------------------------------------------------------

    @staticmethod
    def add_order_item(db: Session, order_id: int, item_data: OrderItemCreate) -> OrderItemResponse:
        """Add a line item to an existing order and recalculate total.

        Raises ``ValueError`` if the order is not found.
        """
        try:
            order = _order_repo.get_by_id(db, order_id)
            if order is None:
                raise ValueError(f"Order with id={order_id} not found")

            unit_price = item_data.unit_price
            if unit_price is None:
                product = _product_repo.get_by_id(db, item_data.product_id)
                if product is None:
                    raise ValueError(
                        f"Product with id={item_data.product_id} not found"
                    )
                unit_price = product.price

            item = _order_repo.add_order_item(
                db,
                order_id=order_id,
                product_id=item_data.product_id,
                quantity=item_data.quantity,
                unit_price=unit_price,
                discount=item_data.discount or Decimal("0"),
            )

            # Recalculate total
            _order_repo.recalculate_total(db, order_id)
            db.commit()
            db.refresh(item)
            logger.info("Added item to order id=%s", order_id)
            return OrderItemResponse.model_validate(item)
        except ValueError:
            raise
        except Exception as exc:
            db.rollback()
            logger.error("Failed to add order item: %s", exc)
            raise

    # ------------------------------------------------------------------
    # ANALYTICS
    # ------------------------------------------------------------------

    @staticmethod
    def get_monthly_sales(db: Session, months: int = 12) -> List[MonthlySales]:
        """Return monthly sales aggregates for the last *months* months."""
        try:
            rows = _order_repo.get_monthly_sales(db, months)
            return [MonthlySales(**r) for r in rows]
        except Exception as exc:
            logger.error("Failed to get monthly sales: %s", exc)
            raise
