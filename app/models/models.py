"""
SQLAlchemy ORM models for TechStore Analytics.

Defines all database tables and their relationships for the TechStore
Analytics platform, covering customers, products, inventory, orders,
payments, and shipments.

Tables
------
- customers      : End-user accounts
- categories     : Product classification groups
- suppliers      : Product suppliers / vendors
- products       : Catalogue of sellable items
- stores         : Physical or virtual store locations
- inventory      : Per-store stock levels for each product
- orders         : Customer purchase headers
- order_items    : Line items within an order
- payments       : Payment records linked to orders
- shipments      : Shipment tracking information linked to orders
"""

import logging
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Numeric,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.config import Base

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Mixin for common timestamp columns
# ---------------------------------------------------------------------------

class TimestampMixin:
    """Provide ``created_at`` and ``updated_at`` columns."""

    created_at: datetime = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Row creation timestamp (UTC).",
    )
    updated_at: datetime = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Row last-update timestamp (UTC).",
    )


# ═══════════════════════════════════════════════════════════════════════════
# CUSTOMERS
# ═══════════════════════════════════════════════════════════════════════════

class Customer(Base):
    """Represents a customer who places orders."""

    __tablename__ = "customers"
    __allow_unmapped__ = True

    id: int = Column(Integer, primary_key=True, autoincrement=True, doc="Primary key.")
    first_name: str = Column(String(100), nullable=False, doc="Customer first / given name.")
    last_name: str = Column(String(100), nullable=False, doc="Customer last / family name.")
    email: str = Column(String(255), unique=True, nullable=False, index=True, doc="Unique e-mail address.")
    phone: str = Column(String(50), nullable=True, doc="Phone number.")
    city: str = Column(String(100), nullable=True, doc="City of residence.")
    country: str = Column(String(100), nullable=True, doc="Country of residence.")
    created_at: datetime = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Account creation timestamp (UTC).",
    )

    # -- relationships -------------------------------------------------------
    orders: list["Order"] = relationship(
        "Order",
        back_populates="customer",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
        doc="Orders placed by this customer.",
    )

    def __repr__(self) -> str:
        return f"<Customer id={self.id} name='{self.first_name} {self.last_name}' email='{self.email}'>"


# ═══════════════════════════════════════════════════════════════════════════
# CATEGORIES
# ═══════════════════════════════════════════════════════════════════════════

class Category(Base):
    """Product category for classification and reporting."""

    __tablename__ = "categories"
    __allow_unmapped__ = True

    id: int = Column(Integer, primary_key=True, autoincrement=True, doc="Primary key.")
    name: str = Column(String(100), unique=True, nullable=False, doc="Category name (e.g. 'Laptops').")
    description: str = Column(Text, nullable=True, doc="Free-form description of the category.")

    # -- relationships -------------------------------------------------------
    products: list["Product"] = relationship(
        "Product",
        back_populates="category",
        lazy="selectin",
        doc="Products belonging to this category.",
    )

    def __repr__(self) -> str:
        return f"<Category id={self.id} name='{self.name}'>"


# ═══════════════════════════════════════════════════════════════════════════
# SUPPLIERS
# ═══════════════════════════════════════════════════════════════════════════

class Supplier(Base):
    """Supplier / vendor that provides products to the store."""

    __tablename__ = "suppliers"
    __allow_unmapped__ = True

    id: int = Column(Integer, primary_key=True, autoincrement=True, doc="Primary key.")
    company_name: str = Column(String(200), nullable=False, doc="Legal or trading company name.")
    contact_name: str = Column(String(200), nullable=True, doc="Primary contact person.")
    email: str = Column(String(255), unique=True, nullable=True, doc="Supplier e-mail address.")
    phone: str = Column(String(50), nullable=True, doc="Supplier phone number.")
    country: str = Column(String(100), nullable=True, doc="Country of operation.")

    # -- relationships -------------------------------------------------------
    products: list["Product"] = relationship(
        "Product",
        back_populates="supplier",
        lazy="selectin",
        doc="Products supplied by this supplier.",
    )

    def __repr__(self) -> str:
        return f"<Supplier id={self.id} company='{self.company_name}'>"


# ═══════════════════════════════════════════════════════════════════════════
# PRODUCTS
# ═══════════════════════════════════════════════════════════════════════════

class Product(Base):
    """A sellable product in the TechStore catalogue."""

    __tablename__ = "products"
    __allow_unmapped__ = True

    id: int = Column(Integer, primary_key=True, autoincrement=True, doc="Primary key.")
    name: str = Column(String(200), nullable=False, doc="Product display name.")
    description: str = Column(Text, nullable=True, doc="Detailed product description.")
    sku: str = Column(String(50), unique=True, nullable=False, index=True, doc="Stock-keeping unit code.")
    price: float = Column(Numeric(10, 2), nullable=False, doc="Retail / selling price.")
    cost: float = Column(Numeric(10, 2), nullable=False, doc="Wholesale / purchase cost.")
    category_id: int = Column(
        Integer,
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        doc="FK to categories.id.",
    )
    supplier_id: int = Column(
        Integer,
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True,
        doc="FK to suppliers.id.",
    )
    created_at: datetime = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Product creation timestamp (UTC).",
    )

    # -- relationships -------------------------------------------------------
    category: Category | None = relationship(
        "Category",
        back_populates="products",
        lazy="selectin",
        doc="Parent category.",
    )
    supplier: Supplier | None = relationship(
        "Supplier",
        back_populates="products",
        lazy="selectin",
        doc="Supplying vendor.",
    )
    inventory_records: list["Inventory"] = relationship(
        "Inventory",
        back_populates="product",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
        doc="Per-store inventory records.",
    )
    order_items: list["OrderItem"] = relationship(
        "OrderItem",
        back_populates="product",
        lazy="selectin",
        doc="Order line items referencing this product.",
    )

    def __repr__(self) -> str:
        return f"<Product id={self.id} sku='{self.sku}' name='{self.name}'>"


# ═══════════════════════════════════════════════════════════════════════════
# STORES
# ═══════════════════════════════════════════════════════════════════════════

class Store(Base):
    """Physical or virtual store location."""

    __tablename__ = "stores"
    __allow_unmapped__ = True

    id: int = Column(Integer, primary_key=True, autoincrement=True, doc="Primary key.")
    name: str = Column(String(200), nullable=False, doc="Store display name.")
    city: str = Column(String(100), nullable=True, doc="City where the store is located.")
    country: str = Column(String(100), nullable=True, doc="Country where the store is located.")

    # -- relationships -------------------------------------------------------
    inventory_records: list["Inventory"] = relationship(
        "Inventory",
        back_populates="store",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
        doc="Inventory records for this store.",
    )
    orders: list["Order"] = relationship(
        "Order",
        back_populates="store",
        lazy="selectin",
        doc="Orders placed at this store.",
    )

    def __repr__(self) -> str:
        return f"<Store id={self.id} name='{self.name}' city='{self.city}'>"


# ═══════════════════════════════════════════════════════════════════════════
# INVENTORY
# ═══════════════════════════════════════════════════════════════════════════

class Inventory(Base):
    """Stock quantity of a product at a specific store."""

    __tablename__ = "inventory"
    __allow_unmapped__ = True
    __table_args__ = (
        UniqueConstraint("store_id", "product_id", name="uq_inventory_store_product"),
    )

    id: int = Column(Integer, primary_key=True, autoincrement=True, doc="Primary key.")
    store_id: int = Column(
        Integer,
        ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False,
        doc="FK to stores.id.",
    )
    product_id: int = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        doc="FK to products.id.",
    )
    stock_quantity: int = Column(Integer, default=0, nullable=True, doc="Current quantity on hand.")
    updated_at: datetime = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Last update timestamp (UTC).",
    )

    # -- relationships -------------------------------------------------------
    store: Store = relationship(
        "Store",
        back_populates="inventory_records",
        lazy="selectin",
        doc="Owning store.",
    )
    product: Product = relationship(
        "Product",
        back_populates="inventory_records",
        lazy="selectin",
        doc="Referenced product.",
    )

    def __repr__(self) -> str:
        return (
            f"<Inventory id={self.id} store_id={self.store_id} "
            f"product_id={self.product_id} qty={self.stock_quantity}>"
        )


# ═══════════════════════════════════════════════════════════════════════════
# ORDERS
# ═══════════════════════════════════════════════════════════════════════════

class Order(Base):
    """Header record for a customer order."""

    __tablename__ = "orders"
    __allow_unmapped__ = True

    id: int = Column(Integer, primary_key=True, autoincrement=True, doc="Primary key.")
    customer_id: int = Column(
        Integer,
        ForeignKey("customers.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        doc="FK to customers.id.",
    )
    store_id: int = Column(
        Integer,
        ForeignKey("stores.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
        doc="FK to stores.id.",
    )
    order_date: datetime = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
        nullable=False,
        doc="Date and time the order was placed (UTC).",
    )
    total_amount: float = Column(
        Numeric(12, 2),
        default=0,
        nullable=True,
        doc="Total order amount (computed from line items).",
    )
    status: str = Column(
        String(50),
        default="pending",
        nullable=True,
        doc="Order status – pending, confirmed, shipped, delivered, cancelled.",
    )

    # -- relationships -------------------------------------------------------
    customer: Customer = relationship(
        "Customer",
        back_populates="orders",
        lazy="selectin",
        doc="Owning customer.",
    )
    store: Store | None = relationship(
        "Store",
        back_populates="orders",
        lazy="selectin",
        doc="Store where the order was placed.",
    )
    items: list["OrderItem"] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
        doc="Line items within this order.",
    )
    payment: "Payment | None" = relationship(
        "Payment",
        back_populates="order",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
        doc="Payment record for this order.",
    )
    shipment: "Shipment | None" = relationship(
        "Shipment",
        back_populates="order",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
        doc="Shipment record for this order.",
    )

    def __repr__(self) -> str:
        return (
            f"<Order id={self.id} customer_id={self.customer_id} "
            f"status='{self.status}' total={self.total_amount}>"
        )


# ═══════════════════════════════════════════════════════════════════════════
# ORDER_ITEMS
# ═══════════════════════════════════════════════════════════════════════════

class OrderItem(Base):
    """Individual line item within an order."""

    __tablename__ = "order_items"
    __allow_unmapped__ = True

    id: int = Column(Integer, primary_key=True, autoincrement=True, doc="Primary key.")
    order_id: int = Column(
        Integer,
        ForeignKey("orders.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        doc="FK to orders.id.",
    )
    product_id: int = Column(
        Integer,
        ForeignKey("products.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
        doc="FK to products.id.",
    )
    quantity: int = Column(Integer, nullable=False, doc="Number of units ordered.")
    unit_price: float = Column(Numeric(10, 2), nullable=False, doc="Price per unit at time of order.")
    discount: float = Column(Numeric(5, 2), default=0, nullable=True, doc="Discount percentage or amount.")

    # -- relationships -------------------------------------------------------
    order: Order = relationship(
        "Order",
        back_populates="items",
        lazy="selectin",
        doc="Parent order.",
    )
    product: Product | None = relationship(
        "Product",
        back_populates="order_items",
        lazy="selectin",
        doc="Referenced product.",
    )

    def __repr__(self) -> str:
        return (
            f"<OrderItem id={self.id} order_id={self.order_id} "
            f"product_id={self.product_id} qty={self.quantity}>"
        )


# ═══════════════════════════════════════════════════════════════════════════
# PAYMENTS
# ═══════════════════════════════════════════════════════════════════════════

class Payment(Base):
    """Payment record associated with an order."""

    __tablename__ = "payments"
    __allow_unmapped__ = True

    id: int = Column(Integer, primary_key=True, autoincrement=True, doc="Primary key.")
    order_id: int = Column(
        Integer,
        ForeignKey("orders.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        doc="FK to orders.id (one-to-one).",
    )
    payment_method: str = Column(
        String(50),
        nullable=True,
        doc="Payment method – credit_card, paypal, bank_transfer, etc.",
    )
    payment_status: str = Column(
        String(50),
        default="pending",
        nullable=True,
        doc="Payment status – pending, completed, failed, refunded.",
    )
    payment_date: datetime = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=True,
        doc="Timestamp when the payment was processed (UTC).",
    )
    amount: float = Column(Numeric(12, 2), nullable=False, doc="Payment amount.")

    # -- relationships -------------------------------------------------------
    order: Order = relationship(
        "Order",
        back_populates="payment",
        lazy="selectin",
        doc="Parent order.",
    )

    def __repr__(self) -> str:
        return (
            f"<Payment id={self.id} order_id={self.order_id} "
            f"method='{self.payment_method}' status='{self.payment_status}'>"
        )


# ═══════════════════════════════════════════════════════════════════════════
# SHIPMENTS
# ═══════════════════════════════════════════════════════════════════════════

class Shipment(Base):
    """Shipment / fulfilment tracking information for an order."""

    __tablename__ = "shipments"
    __allow_unmapped__ = True

    id: int = Column(Integer, primary_key=True, autoincrement=True, doc="Primary key.")
    order_id: int = Column(
        Integer,
        ForeignKey("orders.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        doc="FK to orders.id (one-to-one).",
    )
    shipment_status: str = Column(
        String(50),
        default="pending",
        nullable=True,
        doc="Shipment status – pending, processing, shipped, delivered, returned.",
    )
    tracking_number: str = Column(
        String(100),
        unique=True,
        nullable=True,
        doc="Carrier tracking number.",
    )
    shipped_date: datetime = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Date the parcel was handed to the carrier (UTC).",
    )
    delivery_date: datetime = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Date the parcel was delivered to the customer (UTC).",
    )

    # -- relationships -------------------------------------------------------
    order: Order = relationship(
        "Order",
        back_populates="shipment",
        lazy="selectin",
        doc="Parent order.",
    )

    def __repr__(self) -> str:
        return (
            f"<Shipment id={self.id} order_id={self.order_id} "
            f"status='{self.shipment_status}' tracking='{self.tracking_number}'>"
        )
