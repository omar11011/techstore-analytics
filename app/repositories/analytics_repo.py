"""
Analytics repository with comprehensive dashboard and reporting queries.

Provides high-level analytical methods that span multiple models and
aggregate data for dashboards, reports, and business intelligence.
All queries use SQLAlchemy ORM (no raw SQL) with proper joins,
aggregations, and grouping.
"""

from typing import Dict, Any, List, Optional

from sqlalchemy import func, extract, case, literal_column
from sqlalchemy.orm import Session

from app.models.models import (
    Customer,
    Product,
    Category,
    Order,
    OrderItem,
    Payment,
    Shipment,
    Store,
    Inventory,
)
import logging

logger = logging.getLogger(__name__)


class AnalyticsRepository:
    """Repository for cross-cutting analytics queries.

    Unlike the model-specific repositories, this class does not extend
    ``BaseRepository`` because its queries span multiple tables and
    return aggregated result dictionaries rather than ORM instances.

    Parameters
    ----------
    db : Session
        An active SQLAlchemy database session.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    # ==================================================================
    # Dashboard summary
    # ==================================================================

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Return high-level KPIs for the main dashboard.

        Computes total sales, total orders, total customers, total
        products, average ticket size, and gross margin across all
        non-cancelled orders.

        Returns
        -------
        Dict[str, Any]
            Keys:
            - ``total_sales``     (Decimal or 0)
            - ``total_orders``    (int)
            - ``total_customers`` (int)
            - ``total_products``  (int)
            - ``avg_ticket``      (Decimal or None)
            - ``gross_margin``    (Decimal)  — percentage of profit
              over revenue.
        """
        logger.debug("Fetching dashboard summary")

        # --- total sales & orders (non-cancelled) ---
        sales_row = (
            self.db.query(
                func.coalesce(func.sum(Order.total_amount), 0).label(
                    "total_sales"
                ),
                func.count(Order.id).label("total_orders"),
            )
            .filter(Order.status != "cancelled")
            .one()
        )

        # --- total customers ---
        total_customers: int = self.db.query(func.count(Customer.id)).scalar() or 0

        # --- total products ---
        total_products: int = self.db.query(func.count(Product.id)).scalar() or 0

        # --- average ticket ---
        avg_ticket = (
            sales_row.total_sales / sales_row.total_orders
            if sales_row.total_orders > 0
            else None
        )

        # --- gross margin: (revenue - cost) / revenue ---
        margin_row = (
            self.db.query(
                func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0).label(
                    "total_revenue"
                ),
                func.coalesce(
                    func.sum(OrderItem.quantity * Product.cost), 0
                ).label("total_cost"),
            )
            .join(Order, OrderItem.order_id == Order.id)
            .join(Product, OrderItem.product_id == Product.id)
            .filter(Order.status != "cancelled")
            .one()
        )

        gross_margin = (
            (
                (margin_row.total_revenue - margin_row.total_cost)
                / margin_row.total_revenue
                * 100
            )
            if margin_row.total_revenue and margin_row.total_revenue > 0
            else 0
        )

        return {
            "total_sales": sales_row.total_sales,
            "total_orders": sales_row.total_orders,
            "total_customers": total_customers,
            "total_products": total_products,
            "avg_ticket": avg_ticket,
            "gross_margin": round(float(gross_margin), 2),
        }

    # ==================================================================
    # Top products
    # ==================================================================

    def get_top_products(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Return the top-selling products by revenue.

        Parameters
        ----------
        limit : int
            Maximum number of products to return.

        Returns
        -------
        List[Dict[str, Any]]
            Each dict contains:
            - ``product_id``    (int)
            - ``product_name``  (str)
            - ``category_name`` (str or None)
            - ``units_sold``    (int)
            - ``total_revenue`` (Decimal)
        """
        logger.debug("Fetching top %d products by revenue", limit)
        results = (
            self.db.query(
                Product.id.label("product_id"),
                Product.name.label("product_name"),
                Category.name.label("category_name"),
                func.sum(OrderItem.quantity).label("units_sold"),
                func.sum(
                    OrderItem.quantity * OrderItem.unit_price
                    * (1 - func.coalesce(OrderItem.discount, 0) / 100)
                ).label("total_revenue"),
            )
            .join(OrderItem, Product.id == OrderItem.product_id)
            .join(Order, OrderItem.order_id == Order.id)
            .join(Category, Product.category_id == Category.id, isouter=True)
            .filter(Order.status != "cancelled")
            .group_by(
                Product.id,
                Product.name,
                Category.name,
            )
            .order_by(
                func.sum(
                    OrderItem.quantity * OrderItem.unit_price
                    * (1 - func.coalesce(OrderItem.discount, 0) / 100)
                ).desc()
            )
            .limit(limit)
            .all()
        )

        return [
            {
                "product_id": row.product_id,
                "product_name": row.product_name,
                "category_name": row.category_name,
                "units_sold": row.units_sold,
                "total_revenue": row.total_revenue,
            }
            for row in results
        ]

    # ==================================================================
    # Top customers
    # ==================================================================

    def get_top_customers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Return the highest-spending customers.

        Parameters
        ----------
        limit : int
            Maximum number of customers to return.

        Returns
        -------
        List[Dict[str, Any]]
            Each dict contains:
            - ``customer_id``  (int)
            - ``first_name``   (str)
            - ``last_name``    (str)
            - ``total_spent``  (Decimal)
            - ``num_orders``   (int)
            - ``avg_ticket``   (Decimal or None)
        """
        logger.debug("Fetching top %d customers by spending", limit)
        results = (
            self.db.query(
                Customer.id.label("customer_id"),
                Customer.first_name,
                Customer.last_name,
                func.sum(Order.total_amount).label("total_spent"),
                func.count(Order.id).label("num_orders"),
                (
                    func.sum(Order.total_amount)
                    / func.nullif(func.count(Order.id), 0)
                ).label("avg_ticket"),
            )
            .join(Order, Customer.id == Order.customer_id)
            .filter(Order.status != "cancelled")
            .group_by(
                Customer.id,
                Customer.first_name,
                Customer.last_name,
            )
            .order_by(func.sum(Order.total_amount).desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "customer_id": row.customer_id,
                "first_name": row.first_name,
                "last_name": row.last_name,
                "total_spent": row.total_spent,
                "num_orders": row.num_orders,
                "avg_ticket": row.avg_ticket,
            }
            for row in results
        ]

    # ==================================================================
    # Monthly sales
    # ==================================================================

    def get_monthly_sales(self) -> List[Dict[str, Any]]:
        """Aggregate sales by year and month.

        Excludes cancelled orders.

        Returns
        -------
        List[Dict[str, Any]]
            Each dict contains:
            - ``year``           (int)
            - ``month``          (int)
            - ``total_sales``    (Decimal)
            - ``num_orders``     (int)
            - ``avg_ticket``     (Decimal or None)
            - ``num_customers``  (int)
        """
        logger.debug("Fetching monthly sales")
        results = (
            self.db.query(
                extract("year", Order.order_date).label("year"),
                extract("month", Order.order_date).label("month"),
                func.sum(Order.total_amount).label("total_sales"),
                func.count(Order.id).label("num_orders"),
                (
                    func.sum(Order.total_amount)
                    / func.nullif(func.count(Order.id), 0)
                ).label("avg_ticket"),
                func.count(Order.customer_id.distinct()).label(
                    "num_customers"
                ),
            )
            .filter(Order.status != "cancelled")
            .group_by(
                extract("year", Order.order_date),
                extract("month", Order.order_date),
            )
            .order_by(
                extract("year", Order.order_date),
                extract("month", Order.order_date),
            )
            .all()
        )

        return [
            {
                "year": int(row.year) if row.year else None,
                "month": int(row.month) if row.month else None,
                "total_sales": row.total_sales,
                "num_orders": row.num_orders,
                "avg_ticket": row.avg_ticket,
                "num_customers": row.num_customers,
            }
            for row in results
        ]

    # ==================================================================
    # Category sales
    # ==================================================================

    def get_category_sales(self) -> List[Dict[str, Any]]:
        """Aggregate sales performance by product category.

        Excludes cancelled orders.

        Returns
        -------
        List[Dict[str, Any]]
            Each dict contains:
            - ``category_id``    (int)
            - ``category_name``  (str)
            - ``total_sales``    (Decimal)
            - ``num_products``   (int)
            - ``avg_price``      (Decimal)
        """
        logger.debug("Fetching category sales")
        results = (
            self.db.query(
                Category.id.label("category_id"),
                Category.name.label("category_name"),
                func.sum(
                    OrderItem.quantity * OrderItem.unit_price
                    * (1 - func.coalesce(OrderItem.discount, 0) / 100)
                ).label("total_sales"),
                func.count(Product.id.distinct()).label("num_products"),
                func.avg(Product.price).label("avg_price"),
            )
            .join(Product, Category.id == Product.category_id)
            .join(OrderItem, Product.id == OrderItem.product_id)
            .join(Order, OrderItem.order_id == Order.id)
            .filter(Order.status != "cancelled")
            .group_by(
                Category.id,
                Category.name,
            )
            .order_by(
                func.sum(
                    OrderItem.quantity * OrderItem.unit_price
                    * (1 - func.coalesce(OrderItem.discount, 0) / 100)
                ).desc()
            )
            .all()
        )

        return [
            {
                "category_id": row.category_id,
                "category_name": row.category_name,
                "total_sales": row.total_sales,
                "num_products": row.num_products,
                "avg_price": row.avg_price,
            }
            for row in results
        ]

    # ==================================================================
    # Inventory status
    # ==================================================================

    def get_inventory_status(self) -> Dict[str, Any]:
        """Classify inventory items by stock level.

        Returns items classified as ``"out_of_stock"`` (stock = 0),
        ``"low_stock"`` (stock <= 10 but > 0), or ``"ok"`` (stock > 10),
        along with detailed listings for the at-risk items.

        Returns
        -------
        Dict[str, Any]
            Keys:
            - ``out_of_stock_count`` (int)
            - ``low_stock_count``    (int)
            - ``ok_count``           (int)
            - ``out_of_stock_items`` (list of dicts)
            - ``low_stock_items``    (list of dicts)
        """
        logger.debug("Fetching inventory status")

        # Aggregate counts using CASE expressions
        status_counts = (
            self.db.query(
                func.sum(
                    case(
                        (Inventory.stock_quantity == 0, 1),
                        else_=0,
                    )
                ).label("out_of_stock_count"),
                func.sum(
                    case(
                        (
                            (Inventory.stock_quantity > 0)
                            & (Inventory.stock_quantity <= 10),
                            1,
                        ),
                        else_=0,
                    )
                ).label("low_stock_count"),
                func.sum(
                    case(
                        (Inventory.stock_quantity > 10, 1),
                        else_=0,
                    )
                ).label("ok_count"),
            )
            .one()
        )

        # Detail: out-of-stock items
        out_of_stock_rows = (
            self.db.query(
                Product.id.label("product_id"),
                Product.name.label("product_name"),
                Product.sku,
                Store.name.label("store_name"),
                Inventory.stock_quantity,
            )
            .join(Product, Inventory.product_id == Product.id)
            .join(Store, Inventory.store_id == Store.id)
            .filter(Inventory.stock_quantity == 0)
            .all()
        )

        # Detail: low-stock items (stock > 0 but <= 10)
        low_stock_rows = (
            self.db.query(
                Product.id.label("product_id"),
                Product.name.label("product_name"),
                Product.sku,
                Store.name.label("store_name"),
                Inventory.stock_quantity,
            )
            .join(Product, Inventory.product_id == Product.id)
            .join(Store, Inventory.store_id == Store.id)
            .filter(
                Inventory.stock_quantity > 0,
                Inventory.stock_quantity <= 10,
            )
            .all()
        )

        return {
            "out_of_stock_count": int(status_counts.out_of_stock_count or 0),
            "low_stock_count": int(status_counts.low_stock_count or 0),
            "ok_count": int(status_counts.ok_count or 0),
            "out_of_stock_items": [
                {
                    "product_id": r.product_id,
                    "product_name": r.product_name,
                    "sku": r.sku,
                    "store_name": r.store_name,
                    "stock_quantity": r.stock_quantity,
                }
                for r in out_of_stock_rows
            ],
            "low_stock_items": [
                {
                    "product_id": r.product_id,
                    "product_name": r.product_name,
                    "sku": r.sku,
                    "store_name": r.store_name,
                    "stock_quantity": r.stock_quantity,
                }
                for r in low_stock_rows
            ],
        }

    # ==================================================================
    # Store performance
    # ==================================================================

    def get_store_performance(self) -> List[Dict[str, Any]]:
        """Evaluate store-level sales performance.

        Excludes cancelled orders.

        Returns
        -------
        List[Dict[str, Any]]
            Each dict contains:
            - ``store_id``       (int)
            - ``store_name``     (str)
            - ``city``           (str or None)
            - ``country``        (str or None)
            - ``total_sales``    (Decimal)
            - ``num_orders``     (int)
            - ``num_customers``  (int)
            - ``avg_ticket``     (Decimal or None)
        """
        logger.debug("Fetching store performance")
        results = (
            self.db.query(
                Store.id.label("store_id"),
                Store.name.label("store_name"),
                Store.city,
                Store.country,
                func.sum(Order.total_amount).label("total_sales"),
                func.count(Order.id).label("num_orders"),
                func.count(Order.customer_id.distinct()).label(
                    "num_customers"
                ),
                (
                    func.sum(Order.total_amount)
                    / func.nullif(func.count(Order.id), 0)
                ).label("avg_ticket"),
            )
            .join(Order, Store.id == Order.store_id)
            .filter(Order.status != "cancelled")
            .group_by(
                Store.id,
                Store.name,
                Store.city,
                Store.country,
            )
            .order_by(func.sum(Order.total_amount).desc())
            .all()
        )

        return [
            {
                "store_id": row.store_id,
                "store_name": row.store_name,
                "city": row.city,
                "country": row.country,
                "total_sales": row.total_sales,
                "num_orders": row.num_orders,
                "num_customers": row.num_customers,
                "avg_ticket": row.avg_ticket,
            }
            for row in results
        ]

    # ==================================================================
    # Product profitability
    # ==================================================================

    def get_product_profitability(self) -> List[Dict[str, Any]]:
        """Calculate revenue, cost, profit, and margin per product.

        Joins ``order_items`` with ``products`` to compute gross
        profitability.  Excludes cancelled orders.

        Returns
        -------
        List[Dict[str, Any]]
            Each dict contains:
            - ``product_id``     (int)
            - ``product_name``   (str)
            - ``category_name``  (str or None)
            - ``total_revenue``  (Decimal)
            - ``total_cost``     (Decimal)
            - ``gross_profit``   (Decimal)
            - ``profit_margin``  (float)  — percentage
            - ``units_sold``     (int)
        """
        logger.debug("Fetching product profitability")
        results = (
            self.db.query(
                Product.id.label("product_id"),
                Product.name.label("product_name"),
                Category.name.label("category_name"),
                func.sum(
                    OrderItem.quantity * OrderItem.unit_price
                    * (1 - func.coalesce(OrderItem.discount, 0) / 100)
                ).label("total_revenue"),
                func.sum(OrderItem.quantity * Product.cost).label(
                    "total_cost"
                ),
                (
                    func.sum(
                        OrderItem.quantity * OrderItem.unit_price
                        * (1 - func.coalesce(OrderItem.discount, 0) / 100)
                    )
                    - func.sum(OrderItem.quantity * Product.cost)
                ).label("gross_profit"),
                func.sum(OrderItem.quantity).label("units_sold"),
            )
            .join(OrderItem, Product.id == OrderItem.product_id)
            .join(Order, OrderItem.order_id == Order.id)
            .join(Category, Product.category_id == Category.id, isouter=True)
            .filter(Order.status != "cancelled")
            .group_by(
                Product.id,
                Product.name,
                Category.name,
            )
            .order_by(
                (
                    func.sum(
                        OrderItem.quantity * OrderItem.unit_price
                        * (1 - func.coalesce(OrderItem.discount, 0) / 100)
                    )
                    - func.sum(OrderItem.quantity * Product.cost)
                ).desc()
            )
            .all()
        )

        profitability: List[Dict[str, Any]] = []
        for row in results:
            revenue = float(row.total_revenue or 0)
            margin = (
                round((float(row.gross_profit or 0) / revenue) * 100, 2)
                if revenue > 0
                else 0.0
            )
            profitability.append(
                {
                    "product_id": row.product_id,
                    "product_name": row.product_name,
                    "category_name": row.category_name,
                    "total_revenue": row.total_revenue,
                    "total_cost": row.total_cost,
                    "gross_profit": row.gross_profit,
                    "profit_margin": margin,
                    "units_sold": row.units_sold,
                }
            )

        return profitability

    # ==================================================================
    # Payment method stats
    # ==================================================================

    def get_payment_method_stats(self) -> List[Dict[str, Any]]:
        """Analyse payment method distribution.

        Returns the count and total amount per payment method.

        Returns
        -------
        List[Dict[str, Any]]
            Each dict contains:
            - ``payment_method`` (str)
            - ``num_payments``   (int)
            - ``total_amount``   (Decimal)
            - ``percentage``     (float)  — share of total payment count
        """
        logger.debug("Fetching payment method stats")

        # Total count for percentage calculation
        total_count: int = self.db.query(func.count(Payment.id)).scalar() or 1

        results = (
            self.db.query(
                Payment.payment_method,
                func.count(Payment.id).label("num_payments"),
                func.sum(Payment.amount).label("total_amount"),
            )
            .group_by(Payment.payment_method)
            .order_by(func.count(Payment.id).desc())
            .all()
        )

        return [
            {
                "payment_method": row.payment_method,
                "num_payments": row.num_payments,
                "total_amount": row.total_amount,
                "percentage": round(
                    (row.num_payments / total_count) * 100, 2
                ),
            }
            for row in results
        ]

    # ==================================================================
    # Delivery performance
    # ==================================================================

    def get_delivery_performance(self) -> Dict[str, Any]:
        """Calculate delivery performance metrics.

        Computes average delivery days, on-time delivery rate, and
        per-status shipment counts.

        An order is considered "on time" if ``delivery_date`` is on or
        before the estimated delivery date.  Orders without a
        ``delivery_date`` are excluded from the on-time calculation.

        Returns
        -------
        Dict[str, Any]
            Keys:
            - ``avg_delivery_days``    (float or None)
            - ``on_time_rate``         (float)  — percentage
            - ``total_shipments``      (int)
            - ``delivered_count``      (int)
            - ``shipments_by_status``  (list of dicts with
              ``status`` and ``count``)
        """
        logger.debug("Fetching delivery performance")

        # --- average delivery days (shipped_date -> delivery_date) ---
        avg_days_row = (
            self.db.query(
                func.avg(
                    func.extract(
                        "epoch",
                        Shipment.delivery_date - Shipment.shipped_date,
                    )
                    / 86400  # seconds in a day
                ).label("avg_days")
            )
            .filter(
                Shipment.delivery_date.isnot(None),
                Shipment.shipped_date.isnot(None),
            )
            .one()
        )
        avg_delivery_days = (
            round(float(avg_days_row.avg_days), 2)
            if avg_days_row.avg_days is not None
            else None
        )

        # --- on-time rate ---
        # delivered_date <= estimated_delivery (if available)
        # Since the ORM model doesn't have estimated_delivery, we compare
        # delivered orders vs total orders that have a shipped_date.
        delivered_with_ship = (
            self.db.query(func.count(Shipment.id))
            .filter(
                Shipment.delivery_date.isnot(None),
                Shipment.shipped_date.isnot(None),
            )
            .scalar()
        ) or 0

        # Count shipments that were delivered (have delivery_date)
        total_delivered = (
            self.db.query(func.count(Shipment.id))
            .filter(Shipment.delivery_date.isnot(None))
            .scalar()
        ) or 0

        # Total shipments
        total_shipments = (
            self.db.query(func.count(Shipment.id)).scalar()
        ) or 0

        # On-time: delivered within 7 days of shipping (common benchmark)
        on_time_count = (
            self.db.query(func.count(Shipment.id))
            .filter(
                Shipment.delivery_date.isnot(None),
                Shipment.shipped_date.isnot(None),
                (
                    func.extract(
                        "epoch",
                        Shipment.delivery_date - Shipment.shipped_date,
                    )
                    / 86400
                )
                <= 7,
            )
            .scalar()
        ) or 0

        on_time_rate = (
            round((on_time_count / delivered_with_ship) * 100, 2)
            if delivered_with_ship > 0
            else 0.0
        )

        # --- shipments by status ---
        status_rows = (
            self.db.query(
                Shipment.shipment_status,
                func.count(Shipment.id).label("count"),
            )
            .group_by(Shipment.shipment_status)
            .all()
        )

        return {
            "avg_delivery_days": avg_delivery_days,
            "on_time_rate": on_time_rate,
            "total_shipments": total_shipments,
            "delivered_count": total_delivered,
            "shipments_by_status": [
                {
                    "status": row.shipment_status,
                    "count": row.count,
                }
                for row in status_rows
            ],
        }
