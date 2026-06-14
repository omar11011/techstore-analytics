#!/usr/bin/env python3
"""
TechStore Analytics — Demo CSV Generator
==========================================

Exports aggregated data to CSV files for demo / dashboard mode.

Strategy:
    1. Attempt to connect to PostgreSQL and read real data via SQLAlchemy.
    2. If the connection fails (or the tables are empty), fall back to
       generating synthetic demo data directly with Faker.

Output directory: <project_root>/data/demo/

CSV files produced:
    - customers.csv
    - products.csv
    - categories.csv
    - stores.csv
    - orders.csv
    - order_items.csv
    - monthly_sales.csv
    - category_sales.csv
    - top_products.csv
    - top_customers.csv
    - inventory_status.csv
    - store_performance.csv

Usage:
    python scripts/generate_demo_csv.py [options]

Examples:
    python scripts/generate_demo_csv.py
    python scripts/generate_demo_csv.py --synthetic          # skip DB, go synthetic
    python scripts/generate_demo_csv.py --seed 99            # reproducible synthetic data
"""

from __future__ import annotations

import argparse
import csv
import logging
import os
import pathlib
import random
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional

from faker import Faker

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
os.chdir(_PROJECT_ROOT)

OUTPUT_DIR = _PROJECT_ROOT / "data" / "demo"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("csv_generator")

# ---------------------------------------------------------------------------
# Constants for synthetic generation (mirrored from seed_database.py)
# ---------------------------------------------------------------------------

CATEGORY_DEFS: list[dict[str, str]] = [
    {"name": "Laptops", "description": "Portátiles de alto rendimiento para trabajo, gaming y uso diario."},
    {"name": "Smartphones", "description": "Teléfonos inteligentes de última generación."},
    {"name": "Monitors", "description": "Monitores y pantallas de alta resolución."},
    {"name": "Graphics Cards", "description": "Tarjetas gráficas dedicadas para gaming y renderizado."},
    {"name": "Processors", "description": "Procesadores de escritorio y servidor."},
    {"name": "SSDs", "description": "Unidades de estado sólido NVMe y SATA."},
    {"name": "RAM", "description": "Módulos de memoria RAM DDR4 y DDR5."},
    {"name": "Accessories", "description": "Accesorios y periféricos esenciales."},
]

CATEGORY_PRICE_RANGES: dict[str, tuple[float, float]] = {
    "Laptops": (500.0, 3000.0),
    "Smartphones": (200.0, 1500.0),
    "Monitors": (200.0, 2000.0),
    "Graphics Cards": (300.0, 2000.0),
    "Processors": (100.0, 800.0),
    "SSDs": (50.0, 500.0),
    "RAM": (30.0, 300.0),
    "Accessories": (10.0, 200.0),
}

SKU_PREFIXES: dict[str, str] = {
    "Laptops": "LAP", "Smartphones": "PHN", "Monitors": "MON",
    "Graphics Cards": "GPU", "Processors": "CPU", "SSDs": "SSD",
    "RAM": "RAM", "Accessories": "ACC",
}

PRODUCT_NAME_PARTS: dict[str, dict[str, list[str]]] = {
    "Laptops": {
        "brands": ["TechPro", "UltraBook", "PowerEdge", "SlimForce", "NovaPad"],
        "models": ["Pro 15", "Ultra 14", "Gaming X", "Studio 16", "EliteBook"],
    },
    "Smartphones": {
        "brands": ["GalaxyMax", "iNova", "PixelForce", "OnePower", "RedNova"],
        "models": ["S24", "15 Pro", "8 Ultra", "12 Plus", "Note X"],
    },
    "Monitors": {
        "brands": ["ViewMax", "UltraDisplay", "ProScreen", "ColorEdge", "GameView"],
        "models": ["27\" 4K", "32\" QHD", "34\" Ultrawide", "24\" Full HD", "27\" 144Hz"],
    },
    "Graphics Cards": {
        "brands": ["GeForceMax", "RadeonPro", "ArcForce", "TitanX", "QuadroView"],
        "models": ["RTX 4070", "RTX 4080", "RTX 4090", "RX 7800 XT", "RX 7900 XTX"],
    },
    "Processors": {
        "brands": ["CoreMax", "RyzenForce", "XeonPro", "EpicCore", "ThreadRip"],
        "models": ["i7-14700K", "i9-14900K", "i5-14600K", "Ryzen 7 7800X3D", "Ryzen 9 7950X"],
    },
    "SSDs": {
        "brands": ["SpeedDrive", "FlashMax", "QuickStore", "NVMePro", "TurboSSD"],
        "models": ["1TB NVMe", "2TB NVMe", "500GB SATA", "1TB SATA", "4TB NVMe"],
    },
    "RAM": {
        "brands": ["MemoryPro", "SpeedRAM", "VengeanceX", "FuryMax", "TidalForce"],
        "models": ["16GB DDR5 5600", "32GB DDR5 6000", "16GB DDR4 3600", "64GB DDR5 5600", "32GB DDR4 3200"],
    },
    "Accessories": {
        "brands": ["TechGear", "ProAcc", "EssentialX", "GearMax", "ConnectPro"],
        "models": ["Mechanical Keyboard RGB", "Wireless Mouse", "USB-C Hub 7-in-1", "Webcam 4K", "Headset 7.1"],
    },
}

STORE_LOCATIONS: list[dict[str, str]] = [
    {"name": "TechStore CDMX Centro", "city": "Ciudad de México", "country": "Mexico"},
    {"name": "TechStore Guadalajara", "city": "Guadalajara", "country": "Mexico"},
    {"name": "TechStore Monterrey", "city": "Monterrey", "country": "Mexico"},
    {"name": "TechStore Bogotá", "city": "Bogotá", "country": "Colombia"},
    {"name": "TechStore Santiago", "city": "Santiago", "country": "Chile"},
    {"name": "TechStore Lima", "city": "Lima", "country": "Peru"},
    {"name": "TechStore Buenos Aires", "city": "Buenos Aires", "country": "Argentina"},
    {"name": "TechStore Madrid", "city": "Madrid", "country": "Spain"},
    {"name": "TechStore Miami", "city": "Miami", "country": "United States"},
    {"name": "TechStore São Paulo", "city": "São Paulo", "country": "Brazil"},
]

CUSTOMER_COUNTRIES: list[tuple[str, float]] = [
    ("Mexico", 0.35), ("Colombia", 0.12), ("Argentina", 0.10),
    ("Chile", 0.08), ("Peru", 0.07), ("Brazil", 0.06),
    ("Spain", 0.06), ("United States", 0.06), ("Ecuador", 0.03),
    ("Venezuela", 0.02), ("Costa Rica", 0.02), ("Uruguay", 0.02), ("Canada", 0.01),
]

CUSTOMER_CITIES: dict[str, list[str]] = {
    "Mexico": ["Ciudad de México", "Guadalajara", "Monterrey", "Puebla", "Tijuana"],
    "Colombia": ["Bogotá", "Medellín", "Cali", "Barranquilla", "Cartagena"],
    "Argentina": ["Buenos Aires", "Córdoba", "Rosario", "Mendoza", "La Plata"],
    "Chile": ["Santiago", "Valparaíso", "Concepción", "La Serena"],
    "Peru": ["Lima", "Arequipa", "Cusco", "Trujillo"],
    "Brazil": ["São Paulo", "Rio de Janeiro", "Brasília", "Salvador"],
    "Spain": ["Madrid", "Barcelona", "Valencia", "Sevilla"],
    "United States": ["Miami", "Los Angeles", "New York", "Houston"],
    "Ecuador": ["Quito", "Guayaquil", "Cuenca"],
    "Venezuela": ["Caracas", "Maracaibo", "Valencia"],
    "Costa Rica": ["San José", "Heredia", "Alajuela"],
    "Uruguay": ["Montevideo", "Punta del Este", "Salto"],
    "Canada": ["Toronto", "Vancouver", "Montreal"],
}

PAYMENT_METHODS = ["credit_card", "debit_card", "paypal", "bank_transfer", "cash"]
PAYMENT_WEIGHTS = [0.35, 0.25, 0.20, 0.12, 0.08]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def weighted_choice(options: list, weights: list[float]) -> Any:
    return random.choices(options, weights=weights, k=1)[0]


def weighted_country_choice(country_list: list[tuple[str, float]]) -> str:
    countries, weights = zip(*country_list)
    return weighted_choice(list(countries), list(weights))


def random_price_for_category(cat_name: str) -> float:
    min_p, max_p = CATEGORY_PRICE_RANGES.get(cat_name, (10.0, 500.0))
    base = random.uniform(min_p, max_p)
    cents = random.choices([0.99, 0.49, 0.95, 0.00], weights=[0.50, 0.25, 0.15, 0.10], k=1)[0]
    return max(min_p, min(max_p, int(base) + cents))


def random_cost_for_price(price: float) -> float:
    margin = random.uniform(0.60, 0.80)
    return round(price * margin, 2)


def write_csv(filepath: pathlib.Path, rows: list[dict], fieldnames: list[str]) -> int:
    """Write rows to CSV and return the file size in bytes."""
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return filepath.stat().st_size


# ---------------------------------------------------------------------------
# Database-read path
# ---------------------------------------------------------------------------

def read_from_database() -> Optional[dict[str, list[dict]]]:
    """Try to read data from PostgreSQL; return None on failure."""
    try:
        from sqlalchemy import text
        from app.database.config import SessionLocal

        logger.info("Attempting PostgreSQL connection...")
        session = SessionLocal()
        # Quick connectivity check
        session.execute(text("SELECT 1"))

        # Check if tables have data
        from app.models.models import Category, Customer, Order, OrderItem, Product, Store, Inventory
        cat_count = session.query(Category).count()
        if cat_count == 0:
            logger.info("Database tables are empty — falling back to synthetic generation.")
            session.close()
            return None

        logger.info("Connected! Reading data from database...")

        data: dict[str, list[dict]] = {}

        # Categories
        data["categories"] = [
            {"id": c.id, "name": c.name, "description": c.description or ""}
            for c in session.query(Category).all()
        ]

        # Products
        data["products"] = [
            {
                "id": p.id,
                "name": p.name,
                "sku": p.sku,
                "price": float(p.price),
                "cost": float(p.cost),
                "category_id": p.category_id,
                "category_name": p.category.name if p.category else "",
                "supplier_id": p.supplier_id,
            }
            for p in session.query(Product).all()
        ]

        # Stores
        data["stores"] = [
            {"id": s.id, "name": s.name, "city": s.city or "", "country": s.country or ""}
            for s in session.query(Store).all()
        ]

        # Customers
        data["customers"] = [
            {
                "id": c.id,
                "first_name": c.first_name,
                "last_name": c.last_name,
                "email": c.email,
                "city": c.city or "",
                "country": c.country or "",
                "created_at": str(c.created_at),
            }
            for c in session.query(Customer).all()
        ]

        # Orders
        data["orders"] = [
            {
                "id": o.id,
                "customer_id": o.customer_id,
                "store_id": o.store_id,
                "order_date": str(o.order_date),
                "total_amount": float(o.total_amount) if o.total_amount else 0.0,
                "status": o.status or "pending",
            }
            for o in session.query(Order).all()
        ]

        # Order items
        data["order_items"] = [
            {
                "id": oi.id,
                "order_id": oi.order_id,
                "product_id": oi.product_id,
                "quantity": oi.quantity,
                "unit_price": float(oi.unit_price),
                "discount": float(oi.discount) if oi.discount else 0.0,
            }
            for oi in session.query(OrderItem).all()
        ]

        # Inventory
        data["inventory"] = []
        for inv in session.query(Inventory).all():
            prod = inv.product
            store = inv.store
            qty = inv.stock_quantity or 0
            if qty == 0:
                status = "out_of_stock"
            elif qty <= 10:
                status = "low_stock"
            elif qty <= 50:
                status = "in_stock"
            else:
                status = "overstocked"
            data["inventory"].append({
                "product_name": prod.name if prod else "",
                "store_name": store.name if store else "",
                "stock_quantity": qty,
                "status": status,
            })

        session.close()
        logger.info("Data read from database successfully.")
        return data

    except Exception as exc:
        logger.warning("Database connection failed: %s", exc)
        logger.info("Falling back to synthetic data generation.")
        return None


# ---------------------------------------------------------------------------
# Synthetic generation path
# ---------------------------------------------------------------------------

def generate_synthetic_data(
    fake: Faker,
    num_categories: int = 8,
    num_suppliers: int = 50,
    num_products: int = 500,
    num_stores: int = 10,
    num_customers: int = 1000,
    num_orders: int = 10000,
) -> dict[str, list[dict]]:
    """Generate complete synthetic data using Faker (no database needed)."""
    logger.info("Generating synthetic demo data...")

    # --- Categories ---
    categories: list[dict] = []
    for i, cat_def in enumerate(CATEGORY_DEFS[:num_categories], start=1):
        categories.append({
            "id": i,
            "name": cat_def["name"],
            "description": cat_def["description"],
        })
    cat_id_by_name = {c["name"]: c["id"] for c in categories}

    # --- Suppliers ---
    suppliers: list[dict] = []
    supplier_prefixes = [
        "ShenZhen", "Global", "Pacific", "Asia", "Elite", "Prime", "Quantum", "Digital",
        "Micro", "Nano", "Cyber", "Mega", "Tech", "Smart", "Pro", "Advanced",
    ]
    supplier_suffixes = [
        "Technologies", "Electronics", "Components", "Solutions", "Systems",
        "Industries", "Trading", "Manufacturing", "Supply", "Parts",
    ]
    for i in range(1, num_suppliers + 1):
        prefix = random.choice(supplier_prefixes)
        suffix = random.choice(supplier_suffixes)
        suppliers.append({
            "id": i,
            "company_name": f"{prefix} {suffix}",
        })

    # --- Products ---
    products: list[dict] = []
    cat_weights = [0.12, 0.12, 0.10, 0.10, 0.10, 0.12, 0.12, 0.22]
    cat_names = [c["name"] for c in categories]
    used_skus: set[str] = set()

    for i in range(1, num_products + 1):
        cat_name = weighted_choice(cat_names, cat_weights)
        cat_id = cat_id_by_name[cat_name]
        parts = PRODUCT_NAME_PARTS.get(cat_name, PRODUCT_NAME_PARTS["Accessories"])
        brand = random.choice(parts["brands"])
        model = random.choice(parts["models"])
        product_name = f"{brand} {model}"
        prefix = SKU_PREFIXES.get(cat_name, "GEN")
        while True:
            sku = f"{prefix}-{fake.numerify('#####')}"
            if sku not in used_skus:
                used_skus.add(sku)
                break
        price = random_price_for_category(cat_name)
        cost = random_cost_for_price(price)
        supplier_id = random.randint(1, num_suppliers)

        products.append({
            "id": i,
            "name": product_name,
            "sku": sku,
            "price": round(price, 2),
            "cost": cost,
            "category_id": cat_id,
            "category_name": cat_name,
            "supplier_id": supplier_id,
        })

    # --- Stores ---
    stores: list[dict] = []
    for i, store_def in enumerate(STORE_LOCATIONS[:num_stores], start=1):
        stores.append({
            "id": i,
            "name": store_def["name"],
            "city": store_def["city"],
            "country": store_def["country"],
        })

    # --- Customers ---
    customers: list[dict] = []
    for i in range(1, num_customers + 1):
        country = weighted_country_choice(CUSTOMER_COUNTRIES)
        city_list = CUSTOMER_CITIES.get(country, ["Unknown"])
        city = random.choice(city_list)
        customers.append({
            "id": i,
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.unique.email(),
            "city": city,
            "country": country,
            "created_at": str(fake.date_time_between(start_date="-2y", end_date="now", tzinfo=timezone.utc)),
        })

    # --- Orders + Order Items ---
    now = datetime.now(timezone.utc)
    orders: list[dict] = []
    order_items: list[dict] = []
    item_id = 1

    # Product price lookup
    product_prices = {p["id"]: p["price"] for p in products}

    for i in range(1, num_orders + 1):
        days_ago = min(int(random.expovariate(1 / 120)), 364)
        order_date = now - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))
        customer_id = random.randint(1, num_customers)
        store_id = random.randint(1, num_stores)

        # Order status based on age
        if days_ago > 180:
            status = random.choices(
                ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"],
                [0.01, 0.01, 0.01, 0.02, 0.93, 0.02], k=1
            )[0]
        elif days_ago > 30:
            status = random.choices(
                ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"],
                [0.05, 0.10, 0.10, 0.30, 0.40, 0.05], k=1
            )[0]
        else:
            status = random.choices(
                ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"],
                [0.25, 0.25, 0.20, 0.15, 0.10, 0.05], k=1
            )[0]

        # Items
        num_items = random.choices([1, 2, 3, 4, 5], weights=[0.30, 0.30, 0.20, 0.12, 0.08], k=1)[0]
        selected_products = random.sample(products, min(num_items, len(products)))
        total = 0.0

        for prod in selected_products:
            qty = random.choices([1, 2, 3, 4, 5], weights=[0.45, 0.25, 0.15, 0.10, 0.05], k=1)[0]
            unit_price = prod["price"]
            discount = random.choices([0, 5, 10, 15], weights=[0.50, 0.25, 0.15, 0.10], k=1)[0]
            line_total = qty * unit_price * (1 - discount / 100)
            total += line_total

            order_items.append({
                "id": item_id,
                "order_id": i,
                "product_id": prod["id"],
                "quantity": qty,
                "unit_price": round(unit_price, 2),
                "discount": discount,
            })
            item_id += 1

        orders.append({
            "id": i,
            "customer_id": customer_id,
            "store_id": store_id,
            "order_date": str(order_date),
            "total_amount": round(total, 2),
            "status": status,
        })

    # --- Inventory ---
    inventory: list[dict] = []
    for prod in products:
        for store in stores:
            qty = random.randint(0, 200)
            if qty == 0:
                inv_status = "out_of_stock"
            elif qty <= 10:
                inv_status = "low_stock"
            elif qty <= 50:
                inv_status = "in_stock"
            else:
                inv_status = "overstocked"
            inventory.append({
                "product_name": prod["name"],
                "store_name": store["name"],
                "stock_quantity": qty,
                "status": inv_status,
            })

    logger.info("Synthetic data generated: %d categories, %d products, %d customers, %d orders, %d items",
                len(categories), len(products), len(customers), len(orders), len(order_items))

    return {
        "categories": categories,
        "products": products,
        "stores": stores,
        "customers": customers,
        "orders": orders,
        "order_items": order_items,
        "inventory": inventory,
    }


# ---------------------------------------------------------------------------
# Aggregation helpers
# ---------------------------------------------------------------------------

def compute_monthly_sales(orders: list[dict], order_items: list[dict]) -> list[dict]:
    """Aggregate monthly sales from orders."""
    from collections import defaultdict

    monthly: dict[tuple[int, int], dict] = defaultdict(lambda: {"total_sales": 0.0, "num_orders": 0})

    for o in orders:
        try:
            dt = datetime.fromisoformat(o["order_date"])
        except (ValueError, TypeError):
            continue
        if o.get("status") == "cancelled":
            continue
        key = (dt.year, dt.month)
        monthly[key]["total_sales"] += o.get("total_amount", 0.0)
        monthly[key]["num_orders"] += 1

    rows: list[dict] = []
    for (year, month), vals in sorted(monthly.items()):
        avg_ticket = round(vals["total_sales"] / vals["num_orders"], 2) if vals["num_orders"] else 0.0
        rows.append({
            "year": year,
            "month": month,
            "total_sales": round(vals["total_sales"], 2),
            "num_orders": vals["num_orders"],
            "avg_ticket": avg_ticket,
        })
    return rows


def compute_category_sales(products: list[dict], order_items: list[dict]) -> list[dict]:
    """Aggregate sales by product category."""
    from collections import defaultdict

    # Build product_id -> category_name lookup
    pid_to_cat: dict[int, str] = {p["id"]: p["category_name"] for p in products}

    cat_sales: dict[str, dict] = defaultdict(lambda: {"total_sales": 0.0, "num_products": set()})

    for oi in order_items:
        cat_name = pid_to_cat.get(oi["product_id"], "Unknown")
        line_total = oi["quantity"] * oi["unit_price"] * (1 - oi.get("discount", 0) / 100)
        cat_sales[cat_name]["total_sales"] += line_total
        cat_sales[cat_name]["num_products"].add(oi["product_id"])

    rows: list[dict] = []
    for cat_name, vals in sorted(cat_sales.items(), key=lambda x: x[1]["total_sales"], reverse=True):
        rows.append({
            "category_name": cat_name,
            "total_sales": round(vals["total_sales"], 2),
            "num_products": len(vals["num_products"]),
        })
    return rows


def compute_top_products(products: list[dict], order_items: list[dict], top_n: int = 20) -> list[dict]:
    """Compute top products by revenue."""
    from collections import defaultdict

    pid_to_name: dict[int, tuple[str, str]] = {
        p["id"]: (p["name"], p["category_name"]) for p in products
    }

    prod_stats: dict[int, dict] = defaultdict(lambda: {"units_sold": 0, "revenue": 0.0})

    for oi in order_items:
        pid = oi["product_id"]
        prod_stats[pid]["units_sold"] += oi["quantity"]
        line_total = oi["quantity"] * oi["unit_price"] * (1 - oi.get("discount", 0) / 100)
        prod_stats[pid]["revenue"] += line_total

    sorted_prods = sorted(prod_stats.items(), key=lambda x: x[1]["revenue"], reverse=True)[:top_n]

    rows: list[dict] = []
    for pid, stats in sorted_prods:
        name, cat = pid_to_name.get(pid, ("Unknown", "Unknown"))
        rows.append({
            "product_name": name,
            "category": cat,
            "units_sold": stats["units_sold"],
            "revenue": round(stats["revenue"], 2),
        })
    return rows


def compute_top_customers(customers: list[dict], orders: list[dict], top_n: int = 20) -> list[dict]:
    """Compute top customers by total spend."""
    from collections import defaultdict

    cid_to_name: dict[int, str] = {
        c["id"]: f"{c['first_name']} {c['last_name']}" for c in customers
    }

    cust_stats: dict[int, dict] = defaultdict(lambda: {"total_spent": 0.0, "num_orders": 0})

    for o in orders:
        if o.get("status") == "cancelled":
            continue
        cid = o["customer_id"]
        cust_stats[cid]["total_spent"] += o.get("total_amount", 0.0)
        cust_stats[cid]["num_orders"] += 1

    sorted_custs = sorted(cust_stats.items(), key=lambda x: x[1]["total_spent"], reverse=True)[:top_n]

    rows: list[dict] = []
    for cid, stats in sorted_custs:
        name = cid_to_name.get(cid, f"Customer {cid}")
        rows.append({
            "customer_name": name,
            "total_spent": round(stats["total_spent"], 2),
            "num_orders": stats["num_orders"],
        })
    return rows


def compute_store_performance(stores: list[dict], orders: list[dict]) -> list[dict]:
    """Aggregate store performance metrics."""
    from collections import defaultdict

    sid_to_info: dict[int, tuple[str, str]] = {
        s["id"]: (s["name"], s["city"]) for s in stores
    }

    store_stats: dict[int, dict] = defaultdict(lambda: {"total_sales": 0.0, "num_orders": 0})

    for o in orders:
        if o.get("status") == "cancelled":
            continue
        sid = o.get("store_id")
        if sid is None:
            continue
        store_stats[sid]["total_sales"] += o.get("total_amount", 0.0)
        store_stats[sid]["num_orders"] += 1

    rows: list[dict] = []
    for sid, stats in sorted(store_stats.items(), key=lambda x: x[1]["total_sales"], reverse=True):
        name, city = sid_to_info.get(sid, ("Unknown Store", "Unknown"))
        rows.append({
            "store_name": name,
            "city": city,
            "total_sales": round(stats["total_sales"], 2),
            "num_orders": stats["num_orders"],
        })
    return rows


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate demo CSV files for TechStore Analytics.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for synthetic data.")
    parser.add_argument("--synthetic", action="store_true", help="Skip DB and generate synthetic data only.")
    parser.add_argument("--orders", type=int, default=10000, help="Number of orders (synthetic mode).")
    parser.add_argument("--products", type=int, default=500, help="Number of products (synthetic mode).")
    parser.add_argument("--customers", type=int, default=1000, help="Number of customers (synthetic mode).")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    random.seed(args.seed)
    fake = Faker()
    Faker.seed(args.seed)

    logger.info("=" * 60)
    logger.info("TechStore Analytics — Demo CSV Generator")
    logger.info("=" * 60)

    start_time = datetime.now()

    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    logger.info("Output directory: %s", OUTPUT_DIR)

    # Step 1: Get data — either from DB or synthetic
    if args.synthetic:
        logger.info("Synthetic mode requested — skipping database.")
        data = None
    else:
        data = read_from_database()

    if data is None:
        data = generate_synthetic_data(
            fake,
            num_products=args.products,
            num_customers=args.customers,
            num_orders=args.orders,
        )

    # Step 2: Compute aggregations
    logger.info("Computing aggregations...")
    monthly_sales = compute_monthly_sales(data["orders"], data["order_items"])
    category_sales = compute_category_sales(data["products"], data["order_items"])
    top_products = compute_top_products(data["products"], data["order_items"])
    top_customers = compute_top_customers(data["customers"], data["orders"])
    store_performance = compute_store_performance(data["stores"], data["orders"])

    # Step 3: Write CSV files
    logger.info("Writing CSV files...")
    csv_specs: list[tuple[str, list[str], list[dict]]] = [
        ("customers.csv", ["id", "first_name", "last_name", "email", "city", "country", "created_at"], data["customers"]),
        ("products.csv", ["id", "name", "sku", "price", "cost", "category_id", "category_name", "supplier_id"], data["products"]),
        ("categories.csv", ["id", "name", "description"], data["categories"]),
        ("stores.csv", ["id", "name", "city", "country"], data["stores"]),
        ("orders.csv", ["id", "customer_id", "store_id", "order_date", "total_amount", "status"], data["orders"]),
        ("order_items.csv", ["id", "order_id", "product_id", "quantity", "unit_price", "discount"], data["order_items"]),
        ("monthly_sales.csv", ["year", "month", "total_sales", "num_orders", "avg_ticket"], monthly_sales),
        ("category_sales.csv", ["category_name", "total_sales", "num_products"], category_sales),
        ("top_products.csv", ["product_name", "category", "units_sold", "revenue"], top_products),
        ("top_customers.csv", ["customer_name", "total_spent", "num_orders"], top_customers),
        ("inventory_status.csv", ["product_name", "store_name", "stock_quantity", "status"], data["inventory"]),
        ("store_performance.csv", ["store_name", "city", "total_sales", "num_orders"], store_performance),
    ]

    elapsed = datetime.now() - start_time

    logger.info("-" * 60)
    logger.info("CSV files written:")
    total_size = 0
    for filename, fieldnames, rows in csv_specs:
        filepath = OUTPUT_DIR / filename
        size = write_csv(filepath, rows, fieldnames)
        total_size += size
        if size < 1024:
            size_str = f"{size} B"
        elif size < 1024 * 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size / (1024 * 1024):.1f} MB"
        logger.info("  %-25s  %5d rows  %s", filename, len(rows), size_str)

    logger.info("-" * 60)
    logger.info("Total: %d files, %.1f KB", len(csv_specs), total_size / 1024)
    logger.info("Elapsed: %s", elapsed)
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
