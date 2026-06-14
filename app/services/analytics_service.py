"""
Analytics service layer.

Provides high-level dashboard and reporting functionality by aggregating
data from multiple specialised repositories.  This is the single entry
point for all analytics / reporting API endpoints.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.models import (
    Customer,
    Order,
    OrderItem,
    Product,
    Category,
    Store,
    Inventory,
    Payment,
    Shipment,
)
from app.repositories.customer_repository import CustomerRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.store_repository import StoreRepository
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.shipment_repository import ShipmentRepository
from app.schemas.schemas import (
    DashboardSummary,
    TopProduct,
    TopCustomer,
    MonthlySales,
    CategorySales,
    InventoryStatus,
    StorePerformance,
    ProductProfitability,
    PaymentMethodStats,
    DeliveryPerformance,
)

logger = logging.getLogger(__name__)

_customer_repo = CustomerRepository()
_product_repo = ProductRepository()
_order_repo = OrderRepository()
_category_repo = CategoryRepository()
_store_repo = StoreRepository()
_inventory_repo = InventoryRepository()
_payment_repo = PaymentRepository()
_shipment_repo = ShipmentRepository()


class AnalyticsService:
    """Aggregated analytics and reporting business logic."""

    # ------------------------------------------------------------------
    # DASHBOARD SUMMARY
    # ------------------------------------------------------------------

    @staticmethod
    def get_dashboard_summary(db: Session) -> DashboardSummary:
        """Return high-level KPIs for the main dashboard."""
        try:
            total_sales = (
                db.query(func.coalesce(func.sum(Order.total_amount), 0))
                .filter(Order.status != "cancelled")
                .scalar()
            ) or Decimal("0")

            num_orders = db.query(func.count(Order.id)).scalar() or 0
            num_customers = _customer_repo.count(db)
            num_products = _product_repo.count(db)
            avg_ticket = (
                total_sales / num_orders if num_orders else Decimal("0")
            )

            # Calculate gross margin: (total_revenue - total_cost) / total_revenue
            total_cost_result = (
                db.query(
                    func.coalesce(
                        func.sum(OrderItem.quantity * Product.cost), 0
                    )
                )
                .join(Product, Product.id == OrderItem.product_id)
                .join(Order, Order.id == OrderItem.order_id)
                .filter(Order.status != "cancelled")
                .scalar()
            ) or Decimal("0")

            gross_margin = Decimal("0")
            if total_sales and total_sales > 0:
                gross_margin = (total_sales - total_cost_result) / total_sales * 100

            pending_orders = (
                db.query(func.count(Order.id))
                .filter(Order.status == "pending")
                .scalar()
            ) or 0
            low_stock_products = _inventory_repo.count_low_stock(db, threshold=10)

            return DashboardSummary(
                total_sales=total_sales,
                num_orders=num_orders,
                num_customers=num_customers,
                num_products=num_products,
                avg_ticket=avg_ticket,
                gross_margin=round(gross_margin, 2),
                pending_orders=pending_orders,
                low_stock_products=low_stock_products,
            )
        except Exception as exc:
            logger.error("Failed to get dashboard summary: %s", exc)
            raise

    # ------------------------------------------------------------------
    # TOP PRODUCTS
    # ------------------------------------------------------------------

    @staticmethod
    def get_top_products(db: Session, limit: int = 10) -> List[TopProduct]:
        """Return products ranked by sales volume or revenue."""
        try:
            rows = _product_repo.get_top_selling_products(db, limit)
            return [TopProduct(**r) for r in rows]
        except Exception as exc:
            logger.error("Failed to get top products: %s", exc)
            raise

    # ------------------------------------------------------------------
    # TOP CUSTOMERS
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

    # ------------------------------------------------------------------
    # MONTHLY SALES
    # ------------------------------------------------------------------

    @staticmethod
    def get_monthly_sales(db: Session, months: int = 12) -> List[MonthlySales]:
        """Return monthly revenue & order-count aggregates."""
        try:
            rows = _order_repo.get_monthly_sales(db, months)
            return [MonthlySales(**r) for r in rows]
        except Exception as exc:
            logger.error("Failed to get monthly sales: %s", exc)
            raise

    # ------------------------------------------------------------------
    # CATEGORY SALES
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

    # ------------------------------------------------------------------
    # INVENTORY STATUS
    # ------------------------------------------------------------------

    @staticmethod
    def get_inventory_status(db: Session, threshold: int = 10) -> InventoryStatus:
        """Return aggregate inventory health metrics."""
        try:
            total_products = _product_repo.count(db)
            low_stock_count = _inventory_repo.count_low_stock(db, threshold)
            out_of_stock_count = _inventory_repo.count_out_of_stock(db)
            in_stock_count = total_products - out_of_stock_count

            return InventoryStatus(
                total_products=total_products,
                low_stock_count=low_stock_count,
                out_of_stock_count=out_of_stock_count,
                in_stock_count=max(in_stock_count, 0),
            )
        except Exception as exc:
            logger.error("Failed to get inventory status: %s", exc)
            raise

    # ------------------------------------------------------------------
    # STORE PERFORMANCE
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

    # ------------------------------------------------------------------
    # PRODUCT PROFITABILITY
    # ------------------------------------------------------------------

    @staticmethod
    def get_product_profitability(db: Session, limit: int = 20) -> List[ProductProfitability]:
        """Return product-level profitability analysis.

        Field names match the ``ProductProfitability`` schema:
        product_id, name, category, revenue, cost, profit, margin.
        """
        try:
            rows = (
                db.query(
                    Product.id.label("product_id"),
                    Product.name,
                    Category.name.label("category"),
                    func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0).label(
                        "revenue"
                    ),
                    func.coalesce(func.sum(OrderItem.quantity * Product.cost), 0).label("cost"),
                )
                .outerjoin(OrderItem, OrderItem.product_id == Product.id)
                .outerjoin(Category, Category.id == Product.category_id)
                .group_by(Product.id, Product.name, Category.name)
                .order_by(
                    func.coalesce(
                        func.sum(OrderItem.quantity * OrderItem.unit_price)
                        - func.sum(OrderItem.quantity * Product.cost),
                        0,
                    ).desc()
                )
                .limit(limit)
                .all()
            )
            results: List[ProductProfitability] = []
            for row in rows:
                revenue = row.revenue
                cost = row.cost
                profit = revenue - cost
                margin = (profit / revenue * 100) if revenue else Decimal("0")
                results.append(
                    ProductProfitability(
                        product_id=row.product_id,
                        name=row.name,
                        category=row.category,
                        revenue=revenue,
                        cost=cost,
                        profit=profit,
                        margin=round(margin, 2),
                    )
                )
            return results
        except Exception as exc:
            logger.error("Failed to get product profitability: %s", exc)
            raise

    # ------------------------------------------------------------------
    # PAYMENT METHOD STATS
    # ------------------------------------------------------------------

    @staticmethod
    def get_payment_method_stats(db: Session) -> List[PaymentMethodStats]:
        """Return usage statistics grouped by payment method."""
        try:
            rows = _payment_repo.get_payment_methods_stats(db)
            return [PaymentMethodStats(**r) for r in rows]
        except Exception as exc:
            logger.error("Failed to get payment method stats: %s", exc)
            raise

    # ------------------------------------------------------------------
    # DELIVERY PERFORMANCE
    # ------------------------------------------------------------------

    @staticmethod
    def get_delivery_performance(db: Session) -> DeliveryPerformance:
        """Return aggregate shipment delivery performance metrics."""
        try:
            data = _shipment_repo.get_delivery_performance(db)
            return DeliveryPerformance(**data)
        except Exception as exc:
            logger.error("Failed to get delivery performance: %s", exc)
            raise
