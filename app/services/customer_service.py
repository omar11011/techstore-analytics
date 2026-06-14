"""
Customer service layer.

Orchestrates business logic for customer-related operations, delegating
persistence to ``CustomerRepository`` and converting ORM models to
Pydantic response schemas.
"""

from __future__ import annotations

import logging
import math
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.models import Customer
from app.repositories.customer_repository import CustomerRepository
from app.schemas.schemas import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    TopCustomer,
    PaginatedResponse,
)

logger = logging.getLogger(__name__)

_customer_repo = CustomerRepository()


class CustomerService:
    """Business logic for ``Customer`` entities."""

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    @staticmethod
    def create_customer(db: Session, data: CustomerCreate) -> CustomerResponse:
        """Create a new customer.

        Raises ``ValueError`` if the e-mail is already registered.
        """
        try:
            existing = _customer_repo.get_by_email(db, data.email)
            if existing:
                raise ValueError(f"Customer with email '{data.email}' already exists")

            customer = _customer_repo.create(
                db,
                first_name=data.first_name,
                last_name=data.last_name,
                email=data.email,
                phone=data.phone,
                city=data.city,
                country=data.country,
            )
            db.commit()
            db.refresh(customer)
            logger.info("Created customer id=%s", customer.id)
            return CustomerResponse.model_validate(customer)
        except ValueError:
            raise
        except Exception as exc:
            db.rollback()
            logger.error("Failed to create customer: %s", exc)
            raise

    # ------------------------------------------------------------------
    # READ
    # ------------------------------------------------------------------

    @staticmethod
    def get_customer(db: Session, id: int) -> CustomerResponse:
        """Retrieve a single customer by ID.

        Raises ``ValueError`` if the customer is not found.
        """
        try:
            customer = _customer_repo.get_by_id(db, id)
            if customer is None:
                raise ValueError(f"Customer with id={id} not found")
            return CustomerResponse.model_validate(customer)
        except ValueError:
            raise
        except Exception as exc:
            logger.error("Failed to get customer id=%s: %s", id, exc)
            raise

    @staticmethod
    def get_customers(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        city: Optional[str] = None,
        country: Optional[str] = None,
    ) -> PaginatedResponse[CustomerResponse]:
        """Return a paginated list of customers, optionally filtered."""
        try:
            customers = _customer_repo.get_filtered(db, skip, limit, city, country)
            total = _customer_repo.count_filtered(db, city, country)
            items = [CustomerResponse.model_validate(c) for c in customers]
            page = (skip // limit) + 1 if limit > 0 else 1
            pages = math.ceil(total / limit) if limit > 0 else 0
            return PaginatedResponse[CustomerResponse](
                items=items, total=total, page=page, per_page=limit, pages=pages
            )
        except Exception as exc:
            logger.error("Failed to list customers: %s", exc)
            raise

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------

    @staticmethod
    def update_customer(db: Session, id: int, data: CustomerUpdate) -> CustomerResponse:
        """Update an existing customer.

        Raises ``ValueError`` if the customer is not found.
        """
        try:
            update_fields = data.model_dump(exclude_unset=True)
            if not update_fields:
                return CustomerService.get_customer(db, id)

            # If email is being changed, check uniqueness
            if "email" in update_fields:
                existing = _customer_repo.get_by_email(db, update_fields["email"])
                if existing and existing.id != id:
                    raise ValueError(
                        f"Email '{update_fields['email']}' is already in use"
                    )

            customer = _customer_repo.update(db, id, **update_fields)
            if customer is None:
                raise ValueError(f"Customer with id={id} not found")
            db.commit()
            db.refresh(customer)
            logger.info("Updated customer id=%s", id)
            return CustomerResponse.model_validate(customer)
        except ValueError:
            raise
        except Exception as exc:
            db.rollback()
            logger.error("Failed to update customer id=%s: %s", id, exc)
            raise

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------

    @staticmethod
    def delete_customer(db: Session, id: int) -> bool:
        """Delete a customer by ID.

        Raises ``ValueError`` if the customer is not found.
        """
        try:
            deleted = _customer_repo.delete(db, id)
            if not deleted:
                raise ValueError(f"Customer with id={id} not found")
            db.commit()
            logger.info("Deleted customer id=%s", id)
            return True
        except ValueError:
            raise
        except Exception as exc:
            db.rollback()
            logger.error("Failed to delete customer id=%s: %s", id, exc)
            raise

    # ------------------------------------------------------------------
    # ANALYTICS
    # ------------------------------------------------------------------

    @staticmethod
    def get_top_customers(db: Session, limit: int = 10) -> List[TopCustomer]:
        """Return customers ranked by total spending."""
        try:
            rows = _customer_repo.get_top_customers(db, limit)
            return [TopCustomer(**r) for r in rows]
        except Exception as exc:
            logger.error("Failed to get top customers: %s", exc)
            raise
