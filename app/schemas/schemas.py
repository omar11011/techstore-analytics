"""
Pydantic schemas for TechStore Analytics Backend.

Defines request/response/update schemas for all entities, analytics
aggregations, and pagination utilities.  Uses Pydantic v2 conventions
(`model_config = ConfigDict(...)`) throughout.

Schema categories
-----------------
- **Create schemas**  : Validate inbound data for POST endpoints.
- **Response schemas** : Shape outbound data for GET endpoints, with
  ``from_attributes=True`` so ORM objects can be converted directly.
- **Update schemas**  : Partial-update payloads where every field is
  optional (PATCH semantics).
- **Analytics schemas**: Typed containers for dashboard & reporting
  aggregation queries.
- **Pagination**      : Generic paginated-response wrapper.
"""

from __future__ import annotations

import math
import re
from datetime import datetime
from decimal import Decimal
from typing import Generic, List, Optional, TypeVar

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


# ═══════════════════════════════════════════════════════════════════════════
# CONSTANTS & HELPERS
# ═══════════════════════════════════════════════════════════════════════════

_EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

VALID_ORDER_STATUSES: set[str] = {
    "pending",
    "confirmed",
    "processing",
    "shipped",
    "delivered",
    "cancelled",
}

VALID_PAYMENT_METHODS: set[str] = {
    "credit_card",
    "debit_card",
    "cash",
    "bank_transfer",
    "paypal",
    "stripe",
    "other",
}

VALID_PAYMENT_STATUSES: set[str] = {
    "pending",
    "completed",
    "failed",
    "refunded",
}

VALID_SHIPMENT_STATUSES: set[str] = {
    "pending",
    "picked_up",
    "in_transit",
    "out_for_delivery",
    "delivered",
    "returned",
}

T = TypeVar("T")


# ═══════════════════════════════════════════════════════════════════════════
# 1.  CUSTOMER CREATE
# ═══════════════════════════════════════════════════════════════════════════


class CustomerCreate(BaseModel):
    """Schema for creating a new customer.

    Validates that required fields are present and the email is
    well-formed.  ``phone``, ``city``, and ``country`` are optional.
    """

    first_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Customer first / given name.",
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Customer last / family name.",
    )
    email: str = Field(
        ...,
        max_length=255,
        description="Unique e-mail address.",
    )
    phone: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Phone number.",
    )
    city: Optional[str] = Field(
        default=None,
        max_length=100,
        description="City of residence.",
    )
    country: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Country of residence.",
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Ensure the e-mail address matches a basic RFC-like pattern."""
        if not _EMAIL_REGEX.match(v):
            raise ValueError(f"Invalid email address: {v!r}")
        return v.strip().lower()

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_names(cls, v: str) -> str:
        """Trim surrounding whitespace from name fields."""
        return v.strip()


# ═══════════════════════════════════════════════════════════════════════════
# 2.  CATEGORY CREATE
# ═══════════════════════════════════════════════════════════════════════════


class CategoryCreate(BaseModel):
    """Schema for creating a new product category."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Category name (e.g. 'Laptops').",
    )
    description: Optional[str] = Field(
        default=None,
        description="Free-form description of the category.",
    )

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        """Trim surrounding whitespace."""
        return v.strip()


# ═══════════════════════════════════════════════════════════════════════════
# 3.  SUPPLIER CREATE
# ═══════════════════════════════════════════════════════════════════════════


class SupplierCreate(BaseModel):
    """Schema for creating a new supplier / vendor."""

    company_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Legal or trading company name.",
    )
    contact_name: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Primary contact person.",
    )
    email: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Supplier e-mail address.",
    )
    phone: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Supplier phone number.",
    )
    country: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Country of operation.",
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Validate e-mail format when provided."""
        if v is not None and not _EMAIL_REGEX.match(v):
            raise ValueError(f"Invalid email address: {v!r}")
        return v.strip().lower() if v else v

    @field_validator("company_name")
    @classmethod
    def strip_company_name(cls, v: str) -> str:
        """Trim surrounding whitespace."""
        return v.strip()


# ═══════════════════════════════════════════════════════════════════════════
# 4.  PRODUCT CREATE
# ═══════════════════════════════════════════════════════════════════════════


class ProductCreate(BaseModel):
    """Schema for creating a new product.

    Enforces positive ``price`` and non-negative ``cost``, and validates
    that ``price`` exceeds ``cost`` to guarantee a margin.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Product display name.",
    )
    description: Optional[str] = Field(
        default=None,
        description="Detailed product description.",
    )
    sku: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Stock-keeping unit code (unique).",
    )
    price: Decimal = Field(
        ...,
        gt=0,
        decimal_places=2,
        description="Retail / selling price (must be > 0).",
    )
    cost: Decimal = Field(
        ...,
        ge=0,
        decimal_places=2,
        description="Wholesale / purchase cost (>= 0).",
    )
    category_id: Optional[int] = Field(
        default=None,
        description="FK to categories.id.",
    )
    supplier_id: Optional[int] = Field(
        default=None,
        description="FK to suppliers.id.",
    )

    @field_validator("name", "sku")
    @classmethod
    def strip_text(cls, v: str) -> str:
        """Trim surrounding whitespace."""
        return v.strip()

    @model_validator(mode="after")
    def price_exceeds_cost(self) -> "ProductCreate":
        """Ensure selling price is greater than cost for a positive margin."""
        if self.price <= self.cost:
            raise ValueError(
                f"Selling price ({self.price}) must be greater than cost ({self.cost})."
            )
        return self


# ═══════════════════════════════════════════════════════════════════════════
# 5.  STORE CREATE
# ═══════════════════════════════════════════════════════════════════════════


class StoreCreate(BaseModel):
    """Schema for creating a new store location."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Store display name.",
    )
    city: Optional[str] = Field(
        default=None,
        max_length=100,
        description="City where the store is located.",
    )
    country: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Country where the store is located.",
    )

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        """Trim surrounding whitespace."""
        return v.strip()


# ═══════════════════════════════════════════════════════════════════════════
# 6.  INVENTORY CREATE
# ═══════════════════════════════════════════════════════════════════════════


class InventoryCreate(BaseModel):
    """Schema for creating an inventory record (product-stock at a store)."""

    store_id: int = Field(
        ...,
        gt=0,
        description="FK to stores.id.",
    )
    product_id: int = Field(
        ...,
        gt=0,
        description="FK to products.id.",
    )
    stock_quantity: int = Field(
        default=0,
        ge=0,
        description="Current quantity on hand (>= 0).",
    )


# ═══════════════════════════════════════════════════════════════════════════
# 7.  ORDER CREATE
# ═══════════════════════════════════════════════════════════════════════════


class OrderCreate(BaseModel):
    """Schema for creating a new order with line items.

    The ``total_amount`` is automatically calculated from the items
    by the service layer.  Items can specify ``unit_price`` or leave
    it blank to use the product's current selling price.
    """

    customer_id: int = Field(
        ...,
        gt=0,
        description="FK to customers.id.",
    )
    store_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="FK to stores.id.",
    )
    status: Optional[str] = Field(
        default="pending",
        description="Initial order status.  Defaults to 'pending'.",
    )
    items: List["OrderItemCreate"] = Field(
        default_factory=list,
        description="Line items to add to the order.",
    )


# ═══════════════════════════════════════════════════════════════════════════
# 8.  ORDER ITEM CREATE
# ═══════════════════════════════════════════════════════════════════════════


class OrderItemCreate(BaseModel):
    """Schema for adding a line item to an order.

    If ``unit_price`` is not provided the service layer will look up
    the product's current selling price.
    """

    product_id: int = Field(
        ...,
        gt=0,
        description="FK to products.id.",
    )
    quantity: int = Field(
        ...,
        gt=0,
        description="Number of units ordered (must be > 0).",
    )
    unit_price: Optional[Decimal] = Field(
        default=None,
        gt=0,
        decimal_places=2,
        description="Price per unit at time of order.  If omitted the product price is used.",
    )
    discount: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        le=100,
        decimal_places=2,
        description="Discount percentage (0–100). Defaults to 0.",
    )


# ═══════════════════════════════════════════════════════════════════════════
# 9.  PAYMENT CREATE
# ═══════════════════════════════════════════════════════════════════════════


class PaymentCreate(BaseModel):
    """Schema for recording a payment against an order."""

    order_id: int = Field(
        ...,
        gt=0,
        description="FK to orders.id.",
    )
    payment_method: Optional[str] = Field(
        default=None,
        description="Payment method used.",
    )
    payment_status: Optional[str] = Field(
        default="pending",
        description="Payment status.  Defaults to 'pending'.",
    )
    amount: Decimal = Field(
        ...,
        gt=0,
        decimal_places=2,
        description="Payment amount (must be > 0).",
    )

    @field_validator("payment_method")
    @classmethod
    def validate_payment_method(cls, v: Optional[str]) -> Optional[str]:
        """Ensure the payment method is one of the accepted values."""
        if v is None:
            return v
        v = v.strip().lower()
        if v not in VALID_PAYMENT_METHODS:
            raise ValueError(
                f"Invalid payment method {v!r}. "
                f"Expected one of: {sorted(VALID_PAYMENT_METHODS)}"
            )
        return v


# ═══════════════════════════════════════════════════════════════════════════
# 10. SHIPMENT CREATE
# ═══════════════════════════════════════════════════════════════════════════


class ShipmentCreate(BaseModel):
    """Schema for creating a shipment record for an order."""

    order_id: int = Field(
        ...,
        gt=0,
        description="FK to orders.id.",
    )
    shipment_status: Optional[str] = Field(
        default="pending",
        description="Initial shipment status.  Defaults to 'pending'.",
    )
    tracking_number: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Carrier tracking number (unique).",
    )
    shipped_date: Optional[datetime] = Field(
        default=None,
        description="Date parcel was handed to carrier (UTC).",
    )
    delivery_date: Optional[datetime] = Field(
        default=None,
        description="Date parcel was delivered (UTC).",
    )

    @field_validator("tracking_number")
    @classmethod
    def strip_tracking(cls, v: Optional[str]) -> Optional[str]:
        """Trim surrounding whitespace from tracking number."""
        return v.strip() if v else v


# ═══════════════════════════════════════════════════════════════════════════
# 11. CUSTOMER RESPONSE
# ═══════════════════════════════════════════════════════════════════════════


class CustomerResponse(BaseModel):
    """Response schema for Customer, including id and creation timestamp.

    Supports ``from_attributes=True`` so SQLAlchemy model instances can
    be converted without manual mapping.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Primary key.")
    first_name: str = Field(description="Customer first / given name.")
    last_name: str = Field(description="Customer last / family name.")
    email: str = Field(description="Unique e-mail address.")
    phone: Optional[str] = Field(default=None, description="Phone number.")
    city: Optional[str] = Field(default=None, description="City of residence.")
    country: Optional[str] = Field(default=None, description="Country of residence.")
    created_at: datetime = Field(description="Account creation timestamp (UTC).")


# ═══════════════════════════════════════════════════════════════════════════
# 12. CATEGORY RESPONSE
# ═══════════════════════════════════════════════════════════════════════════


class CategoryResponse(BaseModel):
    """Response schema for Category, including id."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Primary key.")
    name: str = Field(description="Category name.")
    description: Optional[str] = Field(default=None, description="Category description.")


# ═══════════════════════════════════════════════════════════════════════════
# 13. SUPPLIER RESPONSE
# ═══════════════════════════════════════════════════════════════════════════


class SupplierResponse(BaseModel):
    """Response schema for Supplier, including id."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Primary key.")
    company_name: str = Field(description="Legal or trading company name.")
    contact_name: Optional[str] = Field(default=None, description="Primary contact person.")
    email: Optional[str] = Field(default=None, description="Supplier e-mail address.")
    phone: Optional[str] = Field(default=None, description="Supplier phone number.")
    country: Optional[str] = Field(default=None, description="Country of operation.")


# ═══════════════════════════════════════════════════════════════════════════
# 14. PRODUCT RESPONSE
# ═══════════════════════════════════════════════════════════════════════════


class ProductResponse(BaseModel):
    """Response schema for Product, including id, timestamps, and optional
    related category/supplier names.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Primary key.")
    name: str = Field(description="Product display name.")
    description: Optional[str] = Field(default=None, description="Detailed product description.")
    sku: str = Field(description="Stock-keeping unit code.")
    price: Decimal = Field(description="Retail / selling price.")
    cost: Decimal = Field(description="Wholesale / purchase cost.")
    category_id: Optional[int] = Field(default=None, description="FK to categories.id.")
    supplier_id: Optional[int] = Field(default=None, description="FK to suppliers.id.")
    created_at: datetime = Field(description="Product creation timestamp (UTC).")

    # --- denormalised related names (populated by service layer) -----------
    category_name: Optional[str] = Field(
        default=None,
        description="Name of the parent category (if any).",
    )
    supplier_name: Optional[str] = Field(
        default=None,
        description="Company name of the supplier (if any).",
    )


# ═══════════════════════════════════════════════════════════════════════════
# 15. STORE RESPONSE
# ═══════════════════════════════════════════════════════════════════════════


class StoreResponse(BaseModel):
    """Response schema for Store, including id."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Primary key.")
    name: str = Field(description="Store display name.")
    city: Optional[str] = Field(default=None, description="City where the store is located.")
    country: Optional[str] = Field(default=None, description="Country where the store is located.")


# ═══════════════════════════════════════════════════════════════════════════
# 16. INVENTORY RESPONSE
# ═══════════════════════════════════════════════════════════════════════════


class InventoryResponse(BaseModel):
    """Response schema for Inventory, including id, timestamp, and
    denormalised product/store names.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Primary key.")
    store_id: int = Field(description="FK to stores.id.")
    product_id: int = Field(description="FK to products.id.")
    stock_quantity: int = Field(description="Current quantity on hand.")
    updated_at: datetime = Field(description="Last update timestamp (UTC).")

    # --- denormalised names ------------------------------------------------
    product_name: Optional[str] = Field(
        default=None,
        description="Name of the referenced product.",
    )
    store_name: Optional[str] = Field(
        default=None,
        description="Name of the owning store.",
    )


# ═══════════════════════════════════════════════════════════════════════════
# 17. ORDER ITEM RESPONSE  (forward declaration helper for OrderResponse)
# ═══════════════════════════════════════════════════════════════════════════


class OrderItemResponse(BaseModel):
    """Response schema for an OrderItem, including id and product name."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Primary key.")
    order_id: int = Field(description="FK to orders.id.")
    product_id: Optional[int] = Field(default=None, description="FK to products.id.")
    quantity: int = Field(description="Number of units ordered.")
    unit_price: Decimal = Field(description="Price per unit at time of order.")
    discount: Optional[Decimal] = Field(default=Decimal("0.00"), description="Discount percentage or amount.")

    # --- denormalised name -------------------------------------------------
    product_name: Optional[str] = Field(
        default=None,
        description="Name of the referenced product.",
    )


# ═══════════════════════════════════════════════════════════════════════════
# 17. ORDER RESPONSE
# ═══════════════════════════════════════════════════════════════════════════


class OrderResponse(BaseModel):
    """Response schema for Order, including id, timestamp, items list,
    and customer name.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Primary key.")
    customer_id: int = Field(description="FK to customers.id.")
    store_id: Optional[int] = Field(default=None, description="FK to stores.id.")
    order_date: datetime = Field(description="Date and time the order was placed (UTC).")
    total_amount: Optional[Decimal] = Field(default=None, description="Total order amount.")
    status: Optional[str] = Field(default=None, description="Order status.")

    # --- related data ------------------------------------------------------
    items: List[OrderItemResponse] = Field(
        default_factory=list,
        description="Line items within this order.",
    )
    customer_name: Optional[str] = Field(
        default=None,
        description="Full name of the customer who placed the order.",
    )


# ═══════════════════════════════════════════════════════════════════════════
# 19. PAYMENT RESPONSE
# ═══════════════════════════════════════════════════════════════════════════


class PaymentResponse(BaseModel):
    """Response schema for Payment, including id and payment timestamp."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Primary key.")
    order_id: int = Field(description="FK to orders.id.")
    payment_method: Optional[str] = Field(default=None, description="Payment method used.")
    payment_status: Optional[str] = Field(default="pending", description="Payment status.")
    payment_date: Optional[datetime] = Field(default=None, description="Timestamp when payment was processed (UTC).")
    amount: Decimal = Field(description="Payment amount.")


# ═══════════════════════════════════════════════════════════════════════════
# 20. SHIPMENT RESPONSE
# ═══════════════════════════════════════════════════════════════════════════


class ShipmentResponse(BaseModel):
    """Response schema for Shipment, including id and shipping timestamps."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Primary key.")
    order_id: int = Field(description="FK to orders.id.")
    shipment_status: Optional[str] = Field(default="pending", description="Shipment status.")
    tracking_number: Optional[str] = Field(default=None, description="Carrier tracking number.")
    shipped_date: Optional[datetime] = Field(default=None, description="Date parcel was handed to carrier (UTC).")
    delivery_date: Optional[datetime] = Field(default=None, description="Date parcel was delivered (UTC).")


# ═══════════════════════════════════════════════════════════════════════════
# 21. CUSTOMER UPDATE
# ═══════════════════════════════════════════════════════════════════════════


class CustomerUpdate(BaseModel):
    """Partial-update schema for Customer.

    All fields are optional; only supplied fields will be updated.
    """

    first_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    email: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=50)
    city: Optional[str] = Field(default=None, max_length=100)
    country: Optional[str] = Field(default=None, max_length=100)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Validate e-mail format when provided."""
        if v is not None and not _EMAIL_REGEX.match(v):
            raise ValueError(f"Invalid email address: {v!r}")
        return v.strip().lower() if v else v

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_names(cls, v: Optional[str]) -> Optional[str]:
        """Trim whitespace from name fields when provided."""
        return v.strip() if v else v


# ═══════════════════════════════════════════════════════════════════════════
# 22. PRODUCT UPDATE
# ═══════════════════════════════════════════════════════════════════════════


class ProductUpdate(BaseModel):
    """Partial-update schema for Product.

    All fields are optional; ``price`` must remain > 0 and the price-must-
    exceed-cost rule is enforced when both are supplied together.
    """

    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None)
    sku: Optional[str] = Field(default=None, min_length=1, max_length=50)
    price: Optional[Decimal] = Field(default=None, gt=0, decimal_places=2)
    cost: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2)
    category_id: Optional[int] = Field(default=None)
    supplier_id: Optional[int] = Field(default=None)

    @field_validator("name", "sku")
    @classmethod
    def strip_text(cls, v: Optional[str]) -> Optional[str]:
        """Trim whitespace when provided."""
        return v.strip() if v else v

    @model_validator(mode="after")
    def price_exceeds_cost_if_both_set(self) -> "ProductUpdate":
        """When both price and cost are provided, enforce price > cost."""
        if self.price is not None and self.cost is not None and self.price <= self.cost:
            raise ValueError(
                f"Selling price ({self.price}) must be greater than cost ({self.cost})."
            )
        return self


# ═══════════════════════════════════════════════════════════════════════════
# 23. ORDER UPDATE
# ═══════════════════════════════════════════════════════════════════════════


class OrderUpdate(BaseModel):
    """Partial-update schema for Order.

    Primarily used for status transitions; other fields can be updated
    as needed.
    """

    status: Optional[str] = Field(
        default=None,
        description="Order status – pending, confirmed, processing, shipped, delivered, cancelled.",
    )
    total_amount: Optional[Decimal] = Field(
        default=None,
        ge=0,
        decimal_places=2,
        description="Total order amount (>= 0).",
    )
    store_id: Optional[int] = Field(default=None, gt=0)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Ensure status is one of the allowed values."""
        if v is not None and v not in VALID_ORDER_STATUSES:
            raise ValueError(
                f"Invalid order status {v!r}. "
                f"Expected one of: {sorted(VALID_ORDER_STATUSES)}"
            )
        return v


# ═══════════════════════════════════════════════════════════════════════════
# 24. INVENTORY UPDATE
# ═══════════════════════════════════════════════════════════════════════════


class InventoryUpdate(BaseModel):
    """Partial-update schema for Inventory.

    Typically used to adjust ``stock_quantity`` after restocking or sales.
    """

    stock_quantity: Optional[int] = Field(
        default=None,
        ge=0,
        description="Updated quantity on hand (>= 0).",
    )
    store_id: Optional[int] = Field(default=None, gt=0)
    product_id: Optional[int] = Field(default=None, gt=0)


# ═══════════════════════════════════════════════════════════════════════════
# 25. PAYMENT UPDATE
# ═══════════════════════════════════════════════════════════════════════════


class PaymentUpdate(BaseModel):
    """Partial-update schema for Payment.

    Used mainly to transition payment status or update the payment method.
    """

    payment_method: Optional[str] = Field(default=None)
    payment_status: Optional[str] = Field(default=None)
    amount: Optional[Decimal] = Field(default=None, gt=0, decimal_places=2)

    @field_validator("payment_method")
    @classmethod
    def validate_payment_method(cls, v: Optional[str]) -> Optional[str]:
        """Validate payment method when provided."""
        if v is not None:
            v = v.strip().lower()
            if v not in VALID_PAYMENT_METHODS:
                raise ValueError(
                    f"Invalid payment method {v!r}. "
                    f"Expected one of: {sorted(VALID_PAYMENT_METHODS)}"
                )
        return v

    @field_validator("payment_status")
    @classmethod
    def validate_payment_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate payment status when provided."""
        if v is not None and v not in VALID_PAYMENT_STATUSES:
            raise ValueError(
                f"Invalid payment status {v!r}. "
                f"Expected one of: {sorted(VALID_PAYMENT_STATUSES)}"
            )
        return v


# ═══════════════════════════════════════════════════════════════════════════
# 26. SHIPMENT UPDATE
# ═══════════════════════════════════════════════════════════════════════════


class ShipmentUpdate(BaseModel):
    """Partial-update schema for Shipment.

    Used for status transitions and recording shipped / delivery dates.
    """

    shipment_status: Optional[str] = Field(default=None)
    tracking_number: Optional[str] = Field(default=None, min_length=1, max_length=100)
    shipped_date: Optional[datetime] = Field(default=None)
    delivery_date: Optional[datetime] = Field(default=None)

    @field_validator("shipment_status")
    @classmethod
    def validate_shipment_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate shipment status when provided."""
        if v is not None and v not in VALID_SHIPMENT_STATUSES:
            raise ValueError(
                f"Invalid shipment status {v!r}. "
                f"Expected one of: {sorted(VALID_SHIPMENT_STATUSES)}"
            )
        return v

    @field_validator("tracking_number")
    @classmethod
    def strip_tracking(cls, v: Optional[str]) -> Optional[str]:
        """Trim whitespace from tracking number when provided."""
        return v.strip() if v else v

    @model_validator(mode="after")
    def delivery_after_shipped(self) -> "ShipmentUpdate":
        """When both dates are provided, delivery must be after shipment."""
        if (
            self.shipped_date is not None
            and self.delivery_date is not None
            and self.delivery_date < self.shipped_date
        ):
            raise ValueError("delivery_date must be on or after shipped_date.")
        return self


# ═══════════════════════════════════════════════════════════════════════════
# 26a. CATEGORY UPDATE
# ═══════════════════════════════════════════════════════════════════════════


class CategoryUpdate(BaseModel):
    """Partial-update schema for Category.

    All fields are optional; only supplied fields will be updated.
    """

    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: Optional[str]) -> Optional[str]:
        """Trim surrounding whitespace when provided."""
        return v.strip() if v else v


# ═══════════════════════════════════════════════════════════════════════════
# 26b. SUPPLIER UPDATE
# ═══════════════════════════════════════════════════════════════════════════


class SupplierUpdate(BaseModel):
    """Partial-update schema for Supplier.

    All fields are optional; only supplied fields will be updated.
    """

    company_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    contact_name: Optional[str] = Field(default=None, max_length=200)
    email: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=50)
    country: Optional[str] = Field(default=None, max_length=100)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Validate e-mail format when provided."""
        if v is not None and not _EMAIL_REGEX.match(v):
            raise ValueError(f"Invalid email address: {v!r}")
        return v.strip().lower() if v else v

    @field_validator("company_name")
    @classmethod
    def strip_company_name(cls, v: Optional[str]) -> Optional[str]:
        """Trim surrounding whitespace when provided."""
        return v.strip() if v else v


# ═══════════════════════════════════════════════════════════════════════════
# 26c. STORE UPDATE
# ═══════════════════════════════════════════════════════════════════════════


class StoreUpdate(BaseModel):
    """Partial-update schema for Store.

    All fields are optional; only supplied fields will be updated.
    """

    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    city: Optional[str] = Field(default=None, max_length=100)
    country: Optional[str] = Field(default=None, max_length=100)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: Optional[str]) -> Optional[str]:
        """Trim surrounding whitespace when provided."""
        return v.strip() if v else v


# ═══════════════════════════════════════════════════════════════════════════
# 26d. SUPPLIER SALES
# ═══════════════════════════════════════════════════════════════════════════


class SupplierSales(BaseModel):
    """Sales aggregation for a supplier."""

    supplier_id: int = Field(description="Supplier primary key.")
    company_name: str = Field(description="Supplier company name.")
    total_sales: Decimal = Field(
        default=Decimal("0"), ge=0, description="Total revenue from this supplier's products."
    )
    product_count: int = Field(
        default=0, ge=0, description="Number of products supplied."
    )
    num_orders: int = Field(
        default=0, ge=0, description="Number of orders containing this supplier's products."
    )


# ═══════════════════════════════════════════════════════════════════════════
# ANALYTICS SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════
# 27. DASHBOARD SUMMARY
# ═══════════════════════════════════════════════════════════════════════════


class DashboardSummary(BaseModel):
    """High-level KPIs for the analytics dashboard.

    Provides a snapshot of key business metrics across sales, customers,
    products, and profitability.
    """

    total_sales: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        description="Total revenue across all orders.",
    )
    num_orders: int = Field(
        default=0,
        ge=0,
        description="Total number of orders.",
    )
    num_customers: int = Field(
        default=0,
        ge=0,
        description="Total number of registered customers.",
    )
    num_products: int = Field(
        default=0,
        ge=0,
        description="Total number of products in catalogue.",
    )
    avg_ticket: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        description="Average order value (total_sales / num_orders).",
    )
    gross_margin: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        le=100,
        description="Gross margin percentage (0–100).",
    )
    pending_orders: int = Field(
        default=0,
        ge=0,
        description="Number of orders in 'pending' status.",
    )
    low_stock_products: int = Field(
        default=0,
        ge=0,
        description="Number of products with stock below threshold.",
    )


# ═══════════════════════════════════════════════════════════════════════════
# 28. TOP PRODUCT
# ═══════════════════════════════════════════════════════════════════════════


class TopProduct(BaseModel):
    """A single entry in the top-selling products ranking."""

    product_id: int = Field(description="Product primary key.")
    name: str = Field(description="Product display name.")
    category: Optional[str] = Field(default=None, description="Product category name.")
    units_sold: int = Field(ge=0, description="Total units sold.")
    revenue: Decimal = Field(ge=0, description="Total revenue generated.")


# ═══════════════════════════════════════════════════════════════════════════
# 29. TOP CUSTOMER
# ═══════════════════════════════════════════════════════════════════════════


class TopCustomer(BaseModel):
    """A single entry in the top-spending customers ranking."""

    customer_id: int = Field(description="Customer primary key.")
    name: str = Field(description="Full customer name.")
    total_spent: Decimal = Field(ge=0, description="Total amount spent across all orders.")
    num_orders: int = Field(ge=0, description="Number of orders placed.")


# ═══════════════════════════════════════════════════════════════════════════
# 30. MONTHLY SALES
# ═══════════════════════════════════════════════════════════════════════════


class MonthlySales(BaseModel):
    """Sales aggregation for a single month, used in time-series charts."""

    year: int = Field(ge=2000, le=2100, description="Calendar year.")
    month: int = Field(ge=1, le=12, description="Calendar month (1–12).")
    total_sales: Decimal = Field(ge=0, description="Total revenue for the month.")
    num_orders: int = Field(ge=0, description="Number of orders in the month.")


# ═══════════════════════════════════════════════════════════════════════════
# 31. CATEGORY SALES
# ═══════════════════════════════════════════════════════════════════════════


class CategorySales(BaseModel):
    """Sales aggregation for a product category."""

    category_id: int = Field(description="Category primary key.")
    name: str = Field(description="Category name.")
    total_sales: Decimal = Field(ge=0, description="Total revenue for this category.")
    num_products: int = Field(ge=0, description="Number of products in this category.")


# ═══════════════════════════════════════════════════════════════════════════
# 32. INVENTORY STATUS
# ═══════════════════════════════════════════════════════════════════════════


class InventoryStatus(BaseModel):
    """Aggregate inventory health metrics across all stores and products."""

    total_products: int = Field(
        default=0, ge=0, description="Total number of products in catalogue."
    )
    low_stock_count: int = Field(
        default=0, ge=0, description="Number of products below stock threshold."
    )
    out_of_stock_count: int = Field(
        default=0, ge=0, description="Number of products with zero stock."
    )
    in_stock_count: int = Field(
        default=0, ge=0, description="Number of products with stock available."
    )


# ═══════════════════════════════════════════════════════════════════════════
# 33. STORE PERFORMANCE
# ═══════════════════════════════════════════════════════════════════════════


class StorePerformance(BaseModel):
    """Performance metrics for a single store."""

    store_id: int = Field(description="Store primary key.")
    name: str = Field(description="Store display name.")
    city: Optional[str] = Field(default=None, description="City where the store is located.")
    total_sales: Decimal = Field(ge=0, description="Total revenue for this store.")
    num_orders: int = Field(ge=0, description="Number of orders at this store.")


# ═══════════════════════════════════════════════════════════════════════════
# 34. PRODUCT PROFITABILITY
# ═══════════════════════════════════════════════════════════════════════════


class ProductProfitability(BaseModel):
    """Profitability breakdown for a single product."""

    product_id: int = Field(description="Product primary key.")
    name: str = Field(description="Product display name.")
    category: Optional[str] = Field(default=None, description="Product category name.")
    revenue: Decimal = Field(ge=0, description="Total revenue (units * selling price).")
    cost: Decimal = Field(ge=0, description="Total cost (units * purchase cost).")
    profit: Decimal = Field(description="Profit (revenue - cost).")
    margin: Decimal = Field(
        ge=0,
        le=100,
        description="Profit margin percentage (0–100).",
    )


# ═══════════════════════════════════════════════════════════════════════════
# 35. PAYMENT METHOD STATS
# ═══════════════════════════════════════════════════════════════════════════


class PaymentMethodStats(BaseModel):
    """Usage statistics for a single payment method."""

    method: str = Field(description="Payment method identifier.")
    count: int = Field(ge=0, description="Number of transactions.")
    total_amount: Decimal = Field(ge=0, description="Total amount processed.")
    percentage: Decimal = Field(
        ge=0,
        le=100,
        description="Percentage of total transactions (0–100).",
    )


# ═══════════════════════════════════════════════════════════════════════════
# 36. DELIVERY PERFORMANCE
# ═══════════════════════════════════════════════════════════════════════════


class DeliveryPerformance(BaseModel):
    """Aggregate delivery / fulfilment performance metrics."""

    total_shipments: int = Field(
        default=0,
        ge=0,
        description="Total number of shipments considered.",
    )
    delivered_on_time: int = Field(
        default=0,
        ge=0,
        description="Number of shipments delivered on time.",
    )
    avg_days: Optional[Decimal] = Field(
        default=None,
        ge=0,
        decimal_places=1,
        description="Average days from shipment to delivery.",
    )
    on_time_rate: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        le=100,
        decimal_places=2,
        description="Percentage of shipments delivered on time (0–100).",
    )


# ═══════════════════════════════════════════════════════════════════════════
# 37. PAGINATED RESPONSE
# ═══════════════════════════════════════════════════════════════════════════


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper.

    Carries the page of items together with pagination metadata
    so clients can render page controls without a second request.

    Attributes
    ----------
    items : list[T]
        The slice of results for the current page.
    total : int
        Total number of matching records across all pages.
    page : int
        Current page number (1-indexed).
    per_page : int
        Number of items requested per page.
    pages : int
        Total number of pages (computed from ``total`` and ``per_page``).
    """

    items: List[T] = Field(
        default_factory=list,
        description="Result items for the current page.",
    )
    total: int = Field(
        ge=0,
        description="Total number of records across all pages.",
    )
    page: int = Field(
        ge=1,
        description="Current page number (1-indexed).",
    )
    per_page: int = Field(
        ge=1,
        le=500,
        description="Number of items per page.",
    )
    pages: int = Field(
        ge=0,
        description="Total number of pages.",
    )

    @model_validator(mode="after")
    def compute_pages(self) -> "PaginatedResponse[T]":
        """Auto-compute ``pages`` from ``total`` and ``per_page``.

        This ensures consistency even if the caller forgets to calculate
        the page count.
        """
        if self.pages == 0 and self.total > 0:
            object.__setattr__(
                self,
                "pages",
                math.ceil(self.total / self.per_page),
            )
        return self
