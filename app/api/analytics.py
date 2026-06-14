"""
Analytics API router.

Exposes read-only endpoints for dashboard and reporting analytics,
aggregating data across customers, products, orders, payments, and shipments.

Endpoints
---------
GET /analytics/dashboard-summary    – High-level KPIs
GET /analytics/top-products         – Top-selling products
GET /analytics/top-customers        – Top-spending customers
GET /analytics/monthly-sales        – Monthly revenue aggregates
GET /analytics/category-sales       – Revenue by category
GET /analytics/inventory-status     – Inventory health overview
GET /analytics/store-performance    – Per-store performance metrics
GET /analytics/product-profitability – Product profitability analysis
GET /analytics/payment-methods      – Payment method usage stats
GET /analytics/delivery-performance – Shipment delivery metrics
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.config import get_db
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
from app.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/dashboard-summary",
    response_model=DashboardSummary,
    summary="Dashboard summary KPIs",
    description="Return high-level key performance indicators for the main dashboard.",
)
def get_dashboard_summary(db: Session = Depends(get_db)) -> DashboardSummary:
    """Retrieve aggregate dashboard KPIs.

    Includes total sales, order count, customer count, product count,
    average ticket, gross margin, pending orders, and low-stock product count.

    Args:
        db: SQLAlchemy session.

    Returns:
        ``DashboardSummary`` with current KPIs.
    """
    try:
        return AnalyticsService.get_dashboard_summary(db)
    except Exception as exc:
        logger.error("Unexpected error fetching dashboard summary: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching the dashboard summary.",
        )


@router.get(
    "/top-products",
    response_model=List[TopProduct],
    summary="Top-selling products",
    description="Return products ranked by sales volume or revenue.",
)
def get_top_products(
    limit: int = Query(default=10, ge=1, le=100, description="Number of top products to return"),
    db: Session = Depends(get_db),
) -> List[TopProduct]:
    """Retrieve the top-selling products.

    Args:
        limit: Maximum number of products to return.
        db:    SQLAlchemy session.

    Returns:
        List of ``TopProduct`` entries sorted by revenue.
    """
    try:
        return AnalyticsService.get_top_products(db, limit=limit)
    except Exception as exc:
        logger.error("Unexpected error fetching top products: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching top products.",
        )


@router.get(
    "/top-customers",
    response_model=List[TopCustomer],
    summary="Top-spending customers",
    description="Return customers ranked by total spending.",
)
def get_top_customers(
    limit: int = Query(default=10, ge=1, le=100, description="Number of top customers to return"),
    db: Session = Depends(get_db),
) -> List[TopCustomer]:
    """Retrieve the top-spending customers.

    Args:
        limit: Maximum number of customers to return.
        db:    SQLAlchemy session.

    Returns:
        List of ``TopCustomer`` entries sorted by total spent.
    """
    try:
        return AnalyticsService.get_top_customers(db, limit=limit)
    except Exception as exc:
        logger.error("Unexpected error fetching top customers: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching top customers.",
        )


@router.get(
    "/monthly-sales",
    response_model=List[MonthlySales],
    summary="Monthly sales aggregates",
    description="Return monthly revenue and order-count time series.",
)
def get_monthly_sales(
    months: int = Query(default=12, ge=1, le=120, description="Number of months to include"),
    db: Session = Depends(get_db),
) -> List[MonthlySales]:
    """Retrieve monthly sales aggregates.

    Args:
        months: Number of recent months to include.
        db:     SQLAlchemy session.

    Returns:
        List of ``MonthlySales`` entries.
    """
    try:
        return AnalyticsService.get_monthly_sales(db, months=months)
    except Exception as exc:
        logger.error("Unexpected error fetching monthly sales: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching monthly sales.",
        )


@router.get(
    "/category-sales",
    response_model=List[CategorySales],
    summary="Revenue by category",
    description="Return revenue breakdown per product category.",
)
def get_category_sales(db: Session = Depends(get_db)) -> List[CategorySales]:
    """Retrieve revenue aggregated by category.

    Args:
        db: SQLAlchemy session.

    Returns:
        List of ``CategorySales`` entries.
    """
    try:
        return AnalyticsService.get_category_sales(db)
    except Exception as exc:
        logger.error("Unexpected error fetching category sales: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching category sales.",
        )


@router.get(
    "/inventory-status",
    response_model=InventoryStatus,
    summary="Inventory health overview",
    description="Return aggregate inventory health metrics.",
)
def get_inventory_status(
    threshold: int = Query(default=10, ge=0, description="Low-stock threshold"),
    db: Session = Depends(get_db),
) -> InventoryStatus:
    """Retrieve aggregate inventory status.

    Args:
        threshold: Stock level below which products are considered low-stock.
        db:        SQLAlchemy session.

    Returns:
        ``InventoryStatus`` with total, low-stock, out-of-stock, and in-stock counts.
    """
    try:
        return AnalyticsService.get_inventory_status(db, threshold=threshold)
    except Exception as exc:
        logger.error("Unexpected error fetching inventory status: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching inventory status.",
        )


@router.get(
    "/store-performance",
    response_model=List[StorePerformance],
    summary="Per-store performance metrics",
    description="Return revenue and order-count metrics for each store.",
)
def get_store_performance(db: Session = Depends(get_db)) -> List[StorePerformance]:
    """Retrieve performance metrics per store.

    Args:
        db: SQLAlchemy session.

    Returns:
        List of ``StorePerformance`` entries.
    """
    try:
        return AnalyticsService.get_store_performance(db)
    except Exception as exc:
        logger.error("Unexpected error fetching store performance: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching store performance.",
        )


@router.get(
    "/product-profitability",
    response_model=List[ProductProfitability],
    summary="Product profitability analysis",
    description="Return product-level profitability breakdown (revenue, cost, profit, margin).",
)
def get_product_profitability(
    limit: int = Query(default=20, ge=1, le=200, description="Number of products to return"),
    db: Session = Depends(get_db),
) -> List[ProductProfitability]:
    """Retrieve product profitability analysis.

    Products are sorted by descending profit.

    Args:
        limit: Maximum number of products to return.
        db:    SQLAlchemy session.

    Returns:
        List of ``ProductProfitability`` entries.
    """
    try:
        return AnalyticsService.get_product_profitability(db, limit=limit)
    except Exception as exc:
        logger.error("Unexpected error fetching product profitability: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching product profitability.",
        )


@router.get(
    "/payment-methods",
    response_model=List[PaymentMethodStats],
    summary="Payment method usage statistics",
    description="Return usage counts, totals, and percentages grouped by payment method.",
)
def get_payment_method_stats(db: Session = Depends(get_db)) -> List[PaymentMethodStats]:
    """Retrieve payment method usage statistics.

    Args:
        db: SQLAlchemy session.

    Returns:
        List of ``PaymentMethodStats`` entries.
    """
    try:
        return AnalyticsService.get_payment_method_stats(db)
    except Exception as exc:
        logger.error("Unexpected error fetching payment method stats: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching payment method statistics.",
        )


@router.get(
    "/delivery-performance",
    response_model=DeliveryPerformance,
    summary="Delivery performance metrics",
    description="Return aggregate shipment delivery performance metrics.",
)
def get_delivery_performance(db: Session = Depends(get_db)) -> DeliveryPerformance:
    """Retrieve aggregate delivery performance metrics.

    Includes total shipments, on-time delivery count, average delivery
    days, and on-time rate.

    Args:
        db: SQLAlchemy session.

    Returns:
        ``DeliveryPerformance`` with aggregate metrics.
    """
    try:
        return AnalyticsService.get_delivery_performance(db)
    except Exception as exc:
        logger.error("Unexpected error fetching delivery performance: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching delivery performance.",
        )
