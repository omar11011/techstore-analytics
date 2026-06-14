"""
Product service layer.

Orchestrates business logic for product-related operations, delegating
persistence to ``ProductRepository`` and converting ORM models to
Pydantic response schemas.
"""

from __future__ import annotations

import logging
import math
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.models import Product
from app.repositories.product_repository import ProductRepository
from app.schemas.schemas import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    TopProduct,
    PaginatedResponse,
)

logger = logging.getLogger(__name__)

_product_repo = ProductRepository()


class ProductService:
    """Business logic for ``Product`` entities."""

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    @staticmethod
    def create_product(db: Session, data: ProductCreate) -> ProductResponse:
        """Create a new product.

        Raises ``ValueError`` if the SKU is already in use.
        """
        try:
            existing = _product_repo.get_by_sku(db, data.sku)
            if existing:
                raise ValueError(f"Product with SKU '{data.sku}' already exists")

            product = _product_repo.create(
                db,
                name=data.name,
                description=data.description,
                sku=data.sku,
                price=data.price,
                cost=data.cost,
                category_id=data.category_id,
                supplier_id=data.supplier_id,
            )
            db.commit()
            db.refresh(product)
            logger.info("Created product id=%s", product.id)
            return ProductResponse.model_validate(product)
        except ValueError:
            raise
        except Exception as exc:
            db.rollback()
            logger.error("Failed to create product: %s", exc)
            raise

    # ------------------------------------------------------------------
    # READ
    # ------------------------------------------------------------------

    @staticmethod
    def get_product(db: Session, id: int) -> ProductResponse:
        """Retrieve a single product by ID.

        Raises ``ValueError`` if the product is not found.
        """
        try:
            product = _product_repo.get_by_id(db, id)
            if product is None:
                raise ValueError(f"Product with id={id} not found")
            return ProductResponse.model_validate(product)
        except ValueError:
            raise
        except Exception as exc:
            logger.error("Failed to get product id=%s: %s", id, exc)
            raise

    @staticmethod
    def get_products(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        category_id: Optional[int] = None,
        supplier_id: Optional[int] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        search: Optional[str] = None,
    ) -> PaginatedResponse[ProductResponse]:
        """Return a paginated list of products with optional filters."""
        try:
            products = _product_repo.get_filtered(
                db, skip, limit, category_id, supplier_id, min_price, max_price, search
            )
            total = _product_repo.count_filtered(
                db, category_id, supplier_id, min_price, max_price, search
            )
            items = [ProductResponse.model_validate(p) for p in products]
            page = (skip // limit) + 1 if limit > 0 else 1
            pages = math.ceil(total / limit) if limit > 0 else 0
            return PaginatedResponse[ProductResponse](
                items=items, total=total, page=page, per_page=limit, pages=pages
            )
        except Exception as exc:
            logger.error("Failed to list products: %s", exc)
            raise

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------

    @staticmethod
    def update_product(db: Session, id: int, data: ProductUpdate) -> ProductResponse:
        """Update an existing product.

        Raises ``ValueError`` if the product is not found, or if the new
        SKU conflicts with an existing one.
        """
        try:
            update_fields = data.model_dump(exclude_unset=True)
            if not update_fields:
                return ProductService.get_product(db, id)

            if "sku" in update_fields:
                existing = _product_repo.get_by_sku(db, update_fields["sku"])
                if existing and existing.id != id:
                    raise ValueError(
                        f"SKU '{update_fields['sku']}' is already in use"
                    )

            product = _product_repo.update(db, id, **update_fields)
            if product is None:
                raise ValueError(f"Product with id={id} not found")
            db.commit()
            db.refresh(product)
            logger.info("Updated product id=%s", id)
            return ProductResponse.model_validate(product)
        except ValueError:
            raise
        except Exception as exc:
            db.rollback()
            logger.error("Failed to update product id=%s: %s", id, exc)
            raise

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------

    @staticmethod
    def delete_product(db: Session, id: int) -> bool:
        """Delete a product by ID.

        Raises ``ValueError`` if the product is not found.
        """
        try:
            deleted = _product_repo.delete(db, id)
            if not deleted:
                raise ValueError(f"Product with id={id} not found")
            db.commit()
            logger.info("Deleted product id=%s", id)
            return True
        except ValueError:
            raise
        except Exception as exc:
            db.rollback()
            logger.error("Failed to delete product id=%s: %s", id, exc)
            raise

    # ------------------------------------------------------------------
    # ANALYTICS
    # ------------------------------------------------------------------

    @staticmethod
    def get_top_selling_products(db: Session, limit: int = 10) -> List[TopProduct]:
        """Return products ranked by total quantity sold."""
        try:
            rows = _product_repo.get_top_selling_products(db, limit)
            return [TopProduct(**r) for r in rows]
        except Exception as exc:
            logger.error("Failed to get top selling products: %s", exc)
            raise

    @staticmethod
    def get_products_without_sales(db: Session) -> List[ProductResponse]:
        """Return products that have never been ordered."""
        try:
            products = _product_repo.get_products_without_sales(db)
            return [ProductResponse.model_validate(p) for p in products]
        except Exception as exc:
            logger.error("Failed to get products without sales: %s", exc)
            raise

    @staticmethod
    def get_low_stock_products(db: Session, threshold: int = 10) -> List[dict]:
        """Return products whose total stock is below *threshold*."""
        try:
            return _product_repo.get_low_stock_products(db, threshold)
        except Exception as exc:
            logger.error("Failed to get low stock products: %s", exc)
            raise
