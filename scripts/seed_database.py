#!/usr/bin/env python3
"""
TechStore Analytics — Database Seeder
======================================

Generates realistic demo data and inserts it into the PostgreSQL database
using SQLAlchemy ORM models.

Usage:
    python scripts/seed_database.py [options]

Examples:
    python scripts/seed_database.py                        # defaults
    python scripts/seed_database.py --orders 5000          # fewer orders
    python scripts/seed_database.py --seed 42              # reproducible run
    python scripts/seed_database.py --categories 5 --products 200

Data generated (in order):
    1. Categories   – 8 tech product categories (Spanish descriptions)
    2. Suppliers    – 50 supplier companies
    3. Products     – 500 products with realistic pricing per category
    4. Stores       – 10 physical store locations
    5. Customers    – 1 000 customers (Latin American & international mix)
    6. Inventory    – one record per product-store combination
    7. Orders       – 10 000 orders spanning last 12 months
    8. Order Items  – 1-5 items per order
    9. Payments     – one per order
   10. Shipments    – one per order with status based on order age
"""

from __future__ import annotations

import argparse
import logging
import random
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from faker import Faker

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so that `app.*` imports work when
# the script is executed directly from the scripts/ directory.
# ---------------------------------------------------------------------------
import os
import pathlib

_PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

os.chdir(_PROJECT_ROOT)

from app.database.config import SessionLocal, engine, Base
from app.models.models import (
    Category,
    Customer,
    Inventory,
    Order,
    OrderItem,
    Payment,
    Product,
    Shipment,
    Store,
    Supplier,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("seeder")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CATEGORY_DEFINITIONS: list[dict[str, str]] = [
    {
        "name": "Laptops",
        "description": "Portátiles de alto rendimiento para trabajo, gaming y uso diario. Incluye modelos ultrabook, convertibles y estaciones de trabajo.",
    },
    {
        "name": "Smartphones",
        "description": "Teléfonos inteligentes de última generación con las mejores cámaras, pantallas y procesadores del mercado.",
    },
    {
        "name": "Monitors",
        "description": "Monitores y pantallas de alta resolución para diseño gráfico, gaming y productividad profesional.",
    },
    {
        "name": "Graphics Cards",
        "description": "Tarjetas gráficas dedicadas para gaming, renderizado 3D, inteligencia artificial y cálculo paralelo.",
    },
    {
        "name": "Processors",
        "description": "Procesadores de escritorio y servidor de última generación para maximizar el rendimiento de tu equipo.",
    },
    {
        "name": "SSDs",
        "description": "Unidades de estado sólido NVMe y SATA para almacenamiento ultrarrápido y confiable.",
    },
    {
        "name": "RAM",
        "description": "Módulos de memoria RAM DDR4 y DDR5 de alta velocidad para mejorar el rendimiento de tu sistema.",
    },
    {
        "name": "Accessories",
        "description": "Accesorios y periféricos esenciales: teclados, ratones, auriculares, cables, fundas y más.",
    },
]

# Price ranges per category: (min_price, max_price)
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

# SKU prefix per category
CATEGORY_SKU_PREFIX: dict[str, str] = {
    "Laptops": "LAP",
    "Smartphones": "PHN",
    "Monitors": "MON",
    "Graphics Cards": "GPU",
    "Processors": "CPU",
    "SSDs": "SSD",
    "RAM": "RAM",
    "Accessories": "ACC",
}

# Realistic product name prefixes/suffixes per category
PRODUCT_NAME_PARTS: dict[str, dict[str, list[str]]] = {
    "Laptops": {
        "brands": ["TechPro", "UltraBook", "PowerEdge", "SlimForce", "NovaPad", "HyperBook", "ZenithPro", "AirLite"],
        "models": ["Pro 15", "Ultra 14", "Gaming X", "Studio 16", "EliteBook", "Air Slim", "Max Performance", "Creator Edition", "Business Pro", "Workstation Z"],
    },
    "Smartphones": {
        "brands": ["GalaxyMax", "iNova", "PixelForce", "OnePower", "RedNova", "ZenPhone", "MotoEdge", "XperiaPro"],
        "models": ["S24", "15 Pro", "8 Ultra", "12 Plus", "Note X", "Ultra Max", "FE Edition", "Pro Max", "Mini SE", "Elite Z"],
    },
    "Monitors": {
        "brands": ["ViewMax", "UltraDisplay", "ProScreen", "ColorEdge", "GameView", "ClearSight", "SharpPro", "PixelPerfect"],
        "models": ["27\" 4K", "32\" QHD", "34\" Ultrawide", "24\" Full HD", "27\" 144Hz", "32\" 4K HDR", "38\" Curved", "27\" OLED", "49\" Super Ultra", "24\" Gaming"],
    },
    "Graphics Cards": {
        "brands": ["GeForceMax", "RadeonPro", "ArcForce", "TitanX", "QuadroView", "NvidiaMax", "RadeonX", "IrisPro"],
        "models": ["RTX 4070", "RTX 4080", "RTX 4090", "RX 7800 XT", "RX 7900 XTX", "RTX 4060 Ti", "RX 7600", "A770", "RTX 4070 Ti Super", "Pro W7900"],
    },
    "Processors": {
        "brands": ["CoreMax", "RyzenForce", "XeonPro", "EpicCore", "ThreadRip", "PentiumX", "CoreUltra", "RyzenPro"],
        "models": ["i7-14700K", "i9-14900K", "i5-14600K", "Ryzen 7 7800X3D", "Ryzen 9 7950X", "Ryzen 5 7600X", "i3-14100", "Ryzen 9 7900X", "i7-13700K", "Xeon W-3400"],
    },
    "SSDs": {
        "brands": ["SpeedDrive", "FlashMax", "QuickStore", "NVMePro", "TurboSSD", "UltraFlash", "RapidDisk", "FastByte"],
        "models": ["1TB NVMe", "2TB NVMe", "500GB SATA", "1TB SATA", "4TB NVMe", "250GB NVMe", "2TB SATA", "500GB NVMe", "8TB Enterprise", "1TB Portable"],
    },
    "RAM": {
        "brands": ["MemoryPro", "SpeedRAM", "VengeanceX", "FuryMax", "TidalForce", "RipJaw", "CorsairX", "KingFast"],
        "models": ["16GB DDR5 5600", "32GB DDR5 6000", "16GB DDR4 3600", "64GB DDR5 5600", "32GB DDR4 3200", "8GB DDR4 3200", "128GB DDR5 ECC", "32GB DDR5 6400", "16GB DDR5 5200", "64GB DDR4 3600"],
    },
    "Accessories": {
        "brands": ["TechGear", "ProAcc", "EssentialX", "GearMax", "ConnectPro", "SmartAcc", "QuickPlug", "ByteGear"],
        "models": ["Mechanical Keyboard RGB", "Wireless Mouse", "USB-C Hub 7-in-1", "Webcam 4K", "Headset 7.1", "Mouse Pad XL", "Cable Management Kit", "Laptop Stand", "HDMI Cable 2m", "USB Flash Drive 64GB"],
    },
}

# Store locations
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

# Payment methods with realistic weight distribution
PAYMENT_METHODS: list[str] = ["credit_card", "debit_card", "paypal", "bank_transfer", "cash"]
PAYMENT_METHOD_WEIGHTS: list[float] = [0.35, 0.25, 0.20, 0.12, 0.08]

# Order statuses with weights
ORDER_STATUSES: list[str] = ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"]
ORDER_STATUS_WEIGHTS: list[float] = [0.05, 0.05, 0.05, 0.10, 0.70, 0.05]

# Shipment statuses
SHIPMENT_STATUSES: list[str] = ["pending", "processing", "shipped", "delivered", "returned"]
SHIPMENT_STATUS_WEIGHTS_OLD: list[float] = [0.02, 0.02, 0.03, 0.90, 0.03]
SHIPMENT_STATUS_WEIGHTS_RECENT: list[float] = [0.25, 0.20, 0.35, 0.15, 0.05]

# Carriers for shipments
CARRIERS: list[str] = ["DHL Express", "FedEx", "UPS", "Estafeta", "Correos de México", "Redpack", "Amazon Logistics", "Servientrega"]

# Countries mix for customers (Latin American + international)
CUSTOMER_COUNTRIES: list[tuple[str, float]] = [
    ("Mexico", 0.35),
    ("Colombia", 0.12),
    ("Argentina", 0.10),
    ("Chile", 0.08),
    ("Peru", 0.07),
    ("Brazil", 0.06),
    ("Spain", 0.06),
    ("United States", 0.06),
    ("Ecuador", 0.03),
    ("Venezuela", 0.02),
    ("Costa Rica", 0.02),
    ("Uruguay", 0.02),
    ("Canada", 0.01),
]

# Cities per country for customer distribution
CUSTOMER_CITIES: dict[str, list[str]] = {
    "Mexico": ["Ciudad de México", "Guadalajara", "Monterrey", "Puebla", "Tijuana", "Cancún", "Mérida", "León", "Querétaro", "Chihuahua"],
    "Colombia": ["Bogotá", "Medellín", "Cali", "Barranquilla", "Cartagena", "Bucaramanga"],
    "Argentina": ["Buenos Aires", "Córdoba", "Rosario", "Mendoza", "La Plata", "Mar del Plata"],
    "Chile": ["Santiago", "Valparaíso", "Concepción", "La Serena", "Antofagasta"],
    "Peru": ["Lima", "Arequipa", "Cusco", "Trujillo", "Chiclayo"],
    "Brazil": ["São Paulo", "Rio de Janeiro", "Brasília", "Salvador", "Curitiba"],
    "Spain": ["Madrid", "Barcelona", "Valencia", "Sevilla", "Bilbao", "Málaga"],
    "United States": ["Miami", "Los Angeles", "New York", "Houston", "Chicago", "San Francisco"],
    "Ecuador": ["Quito", "Guayaquil", "Cuenca"],
    "Venezuela": ["Caracas", "Maracaibo", "Valencia"],
    "Costa Rica": ["San José", "Heredia", "Alajuela"],
    "Uruguay": ["Montevideo", "Punta del Este", "Salto"],
    "Canada": ["Toronto", "Vancouver", "Montreal"],
}

# Supplier countries with weights
SUPPLIER_COUNTRIES: list[tuple[str, float]] = [
    ("China", 0.30),
    ("United States", 0.20),
    ("Taiwan", 0.15),
    ("South Korea", 0.10),
    ("Japan", 0.08),
    ("Germany", 0.05),
    ("Mexico", 0.05),
    ("Vietnam", 0.04),
    ("Malaysia", 0.03),
]

# Supplier company name components
SUPPLIER_PREFIXES: list[str] = [
    "ShenZhen", "Global", "Pacific", "Asia", "Elite", "Prime", "Quantum", "Digital",
    "Micro", "Nano", "Cyber", "Mega", "Tech", "Smart", "Pro", "Advanced",
    "Silicon", "Future", "Nova", "Apex", "Core", "Vertex", "Zenith", "Alpha",
]
SUPPLIER_SUFFIXES: list[str] = [
    "Technologies", "Electronics", "Components", "Solutions", "Systems",
    "Industries", "Trading", "Manufacturing", "Supply", "Parts",
    "Hardware", "Semiconductors", "Tech", "Devices", "Innovations",
    "International", "Group", "Corp", "Labs", "Works",
]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def weighted_choice(options: list[str], weights: list[float]) -> str:
    """Pick one option according to the given weight distribution."""
    return random.choices(options, weights=weights, k=1)[0]


def weighted_country_choice(country_list: list[tuple[str, float]]) -> str:
    """Pick a country according to weight distribution."""
    countries, weights = zip(*country_list)
    return weighted_choice(list(countries), list(weights))


def random_price_for_category(category_name: str) -> Decimal:
    """Generate a realistic price for the given product category."""
    min_p, max_p = CATEGORY_PRICE_RANGES[category_name]
    price = random.uniform(min_p, max_p)
    # Round to nearest 0.99 or 0.49 for realism
    base = int(price)
    cents = random.choices([0.99, 0.49, 0.95, 0.00], weights=[0.50, 0.25, 0.15, 0.10], k=1)[0]
    final_price = float(base) + cents
    # Clamp
    final_price = max(min_p, min(max_p, final_price))
    return Decimal(str(round(final_price, 2)))


def random_cost_for_price(price: Decimal) -> Decimal:
    """Generate a cost that is 60-80% of the selling price."""
    margin_pct = random.uniform(0.60, 0.80)
    cost = float(price) * margin_pct
    return Decimal(str(round(cost, 2)))


def generate_tracking_number(fake: Faker) -> str:
    """Generate a realistic tracking number."""
    carrier_prefixes = ["1Z", "JD", "FDX", "DHL", "EST", "RPK", "AMZ", "SRV"]
    prefix = random.choice(carrier_prefixes)
    number = fake.numerify("###############")
    return f"{prefix}{number}"


def order_status_from_age(age_days: int) -> str:
    """Determine order status based on order age — older orders are more likely delivered."""
    if age_days > 180:
        return weighted_choice(ORDER_STATUSES, [0.01, 0.01, 0.01, 0.02, 0.93, 0.02])
    elif age_days > 90:
        return weighted_choice(ORDER_STATUSES, [0.02, 0.03, 0.05, 0.15, 0.70, 0.05])
    elif age_days > 30:
        return weighted_choice(ORDER_STATUSES, [0.05, 0.10, 0.10, 0.30, 0.40, 0.05])
    elif age_days > 14:
        return weighted_choice(ORDER_STATUSES, [0.10, 0.15, 0.20, 0.30, 0.20, 0.05])
    else:
        return weighted_choice(ORDER_STATUSES, [0.25, 0.25, 0.20, 0.15, 0.10, 0.05])


def shipment_status_from_order_status(order_status: str, age_days: int) -> str:
    """Determine shipment status based on order status and age."""
    if order_status == "cancelled":
        return weighted_choice(["pending", "returned"], [0.70, 0.30])
    if order_status == "delivered":
        return "delivered"
    if age_days > 60:
        return weighted_choice(SHIPMENT_STATUSES, SHIPMENT_STATUS_WEIGHTS_OLD)
    else:
        return weighted_choice(SHIPMENT_STATUSES, SHIPMENT_STATUS_WEIGHTS_RECENT)


# ---------------------------------------------------------------------------
# Data generation functions
# ---------------------------------------------------------------------------

def clear_existing_data(session: SessionLocal) -> None:
    """Delete all rows from every table in reverse dependency order."""
    logger.info("Clearing existing data...")
    try:
        # Delete in reverse dependency order
        table_delete_order = [
            Shipment,
            Payment,
            OrderItem,
            Order,
            Inventory,
            Product,
            Customer,
            Store,
            Supplier,
            Category,
        ]
        for model in table_delete_order:
            count = session.query(model).delete()
            logger.info("  Cleared %s: %d rows deleted", model.__tablename__, count)
        session.commit()
        logger.info("Existing data cleared successfully.")
    except Exception as exc:
        session.rollback()
        logger.error("Failed to clear existing data: %s", exc)
        raise


def seed_categories(session: SessionLocal, count: int = 8) -> list[Category]:
    """Insert product categories."""
    logger.info("Seeding %d categories...", count)
    categories: list[Category] = []
    for cat_def in CATEGORY_DEFINITIONS[:count]:
        cat = Category(
            name=cat_def["name"],
            description=cat_def["description"],
        )
        session.add(cat)
        categories.append(cat)
    session.flush()
    logger.info("  Created %d categories.", len(categories))
    return categories


def seed_suppliers(session: SessionLocal, fake: Faker, count: int = 50) -> list[Supplier]:
    """Insert suppliers with realistic company information."""
    logger.info("Seeding %d suppliers...", count)
    suppliers: list[Supplier] = []
    used_emails: set[str] = set()
    used_names: set[str] = set()

    for i in range(count):
        # Generate unique company name
        while True:
            prefix = random.choice(SUPPLIER_PREFIXES)
            suffix = random.choice(SUPPLIER_SUFFIXES)
            company_name = f"{prefix} {suffix}"
            if company_name not in used_names:
                used_names.add(company_name)
                break

        # Generate unique email
        while True:
            domain = company_name.lower().replace(" ", "").replace(",", "")[:12]
            email = f"contact@{domain}{i}.com"
            if email not in used_emails:
                used_emails.add(email)
                break

        country = weighted_country_choice(SUPPLIER_COUNTRIES)

        supplier = Supplier(
            company_name=company_name,
            contact_name=fake.name(),
            email=email,
            phone=fake.phone_number()[:50],
            country=country,
        )
        session.add(supplier)
        suppliers.append(supplier)

        if (i + 1) % 500 == 0:
            session.flush()
            logger.info("  Flushed %d / %d suppliers", i + 1, count)

    session.flush()
    logger.info("  Created %d suppliers.", len(suppliers))
    return suppliers


def seed_products(
    session: SessionLocal,
    fake: Faker,
    categories: list[Category],
    suppliers: list[Supplier],
    count: int = 500,
) -> list[Product]:
    """Insert products with realistic names, SKUs, and pricing."""
    logger.info("Seeding %d products...", count)
    products: list[Product] = []
    used_skus: set[str] = set()

    # Build a lookup for category definitions
    cat_map: dict[str, Category] = {c.name: c for c in categories}

    # Distribute products across categories with weights
    # Laptops and Smartphones get more products
    category_weights: dict[str, float] = {
        "Laptops": 0.12,
        "Smartphones": 0.12,
        "Monitors": 0.10,
        "Graphics Cards": 0.10,
        "Processors": 0.10,
        "SSDs": 0.12,
        "RAM": 0.12,
        "Accessories": 0.22,
    }

    cat_names = list(category_weights.keys())
    cat_weights_list = [category_weights[c] for c in cat_names]

    for i in range(count):
        cat_name = weighted_choice(cat_names, cat_weights_list)
        category = cat_map.get(cat_name, categories[0])
        parts = PRODUCT_NAME_PARTS.get(cat_name, PRODUCT_NAME_PARTS["Accessories"])

        # Generate product name
        brand = random.choice(parts["brands"])
        model = random.choice(parts["models"])
        product_name = f"{brand} {model}"

        # Generate unique SKU
        prefix = CATEGORY_SKU_PREFIX.get(cat_name, "GEN")
        while True:
            sku = f"{prefix}-{fake.numerify('#####')}"
            if sku not in used_skus:
                used_skus.add(sku)
                break

        price = random_price_for_category(cat_name)
        cost = random_cost_for_price(price)

        # Pick a random supplier
        supplier = random.choice(suppliers)

        product = Product(
            name=product_name,
            description=f"High-quality {cat_name.lower()} product: {product_name}",
            sku=sku,
            price=price,
            cost=cost,
            category_id=category.id,
            supplier_id=supplier.id,
        )
        session.add(product)
        products.append(product)

        if (i + 1) % 500 == 0:
            session.flush()
            logger.info("  Flushed %d / %d products", i + 1, count)

    session.flush()
    logger.info("  Created %d products.", len(products))
    return products


def seed_stores(session: SessionLocal, count: int = 10) -> list[Store]:
    """Insert store locations."""
    logger.info("Seeding %d stores...", count)
    stores: list[Store] = []

    for store_def in STORE_LOCATIONS[:count]:
        store = Store(
            name=store_def["name"],
            city=store_def["city"],
            country=store_def["country"],
        )
        session.add(store)
        stores.append(store)

    session.flush()
    logger.info("  Created %d stores.", len(stores))
    return stores


def seed_customers(session: SessionLocal, fake: Faker, count: int = 1000) -> list[Customer]:
    """Insert customers with Latin American and international distribution."""
    logger.info("Seeding %d customers...", count)
    customers: list[Customer] = []
    used_emails: set[str] = set()

    for i in range(count):
        country = weighted_country_choice(CUSTOMER_COUNTRIES)
        city_list = CUSTOMER_CITIES.get(country, ["Unknown"])
        city = random.choice(city_list)

        # Generate unique email
        while True:
            email = fake.unique.email()
            if email not in used_emails:
                used_emails.add(email)
                break

        customer = Customer(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            email=email,
            phone=fake.phone_number()[:50],
            city=city,
            country=country,
        )
        session.add(customer)
        customers.append(customer)

        if (i + 1) % 500 == 0:
            session.flush()
            logger.info("  Flushed %d / %d customers", i + 1, count)

    session.flush()
    logger.info("  Created %d customers.", len(customers))
    return customers


def seed_inventory(
    session: SessionLocal,
    products: list[Product],
    stores: list[Store],
    batch_size: int = 500,
) -> list[Inventory]:
    """Insert one inventory record per product-store combination."""
    total = len(products) * len(stores)
    logger.info("Seeding inventory records (%d products x %d stores = %d)...", len(products), len(stores), total)
    inventory_records: list[Inventory] = []
    count = 0

    for product in products:
        for store in stores:
            stock = random.randint(0, 200)
            inv = Inventory(
                store_id=store.id,
                product_id=product.id,
                stock_quantity=stock,
            )
            session.add(inv)
            inventory_records.append(inv)
            count += 1

            if count % batch_size == 0:
                session.flush()
                logger.info("  Flushed %d / %d inventory records", count, total)

    session.flush()
    logger.info("  Created %d inventory records.", count)
    return inventory_records


def seed_orders(
    session: SessionLocal,
    fake: Faker,
    customers: list[Customer],
    stores: list[Store],
    products: list[Product],
    count: int = 10000,
    batch_size: int = 500,
) -> tuple[list[Order], list[OrderItem], list[Payment], list[Shipment]]:
    """Insert orders with items, payments, and shipments."""
    logger.info("Seeding %d orders (with items, payments, shipments)...", count)

    now = datetime.now(timezone.utc)
    twelve_months_ago = now - timedelta(days=365)

    all_orders: list[Order] = []
    all_order_items: list[OrderItem] = []
    all_payments: list[Payment] = []
    all_shipments: list[Shipment] = []

    # Build a price lookup for products
    product_prices: dict[int, Decimal] = {p.id: p.price for p in products}

    # Pre-compute order dates with weighted distribution (more recent orders)
    order_dates: list[datetime] = []
    for _ in range(count):
        # Exponential distribution favouring recent dates
        days_ago = int(random.expovariate(1 / 120))  # mean ~120 days ago
        days_ago = min(days_ago, 364)
        order_date = now - timedelta(days=days_ago)
        # Add random time of day
        order_date = order_date.replace(
            hour=random.randint(6, 23),
            minute=random.randint(0, 59),
            second=random.randint(0, 59),
        )
        order_dates.append(order_date)

    # Sort dates chronologically for realism
    order_dates.sort()

    for i, order_date in enumerate(order_dates):
        customer = random.choice(customers)
        store = random.choice(stores)
        age_days = (now - order_date).days
        order_status = order_status_from_age(age_days)

        # Determine number of items (1-5, weighted)
        num_items = random.choices([1, 2, 3, 4, 5], weights=[0.30, 0.30, 0.20, 0.12, 0.08], k=1)[0]

        # Pick random products for items
        selected_products = random.sample(products, min(num_items, len(products)))
        total_amount = Decimal("0.00")

        order = Order(
            customer_id=customer.id,
            store_id=store.id,
            order_date=order_date,
            total_amount=Decimal("0.00"),  # will be updated after items
            status=order_status,
        )
        session.add(order)
        session.flush()  # need order.id for items

        # Create order items
        for prod in selected_products:
            quantity = random.choices([1, 2, 3, 4, 5], weights=[0.45, 0.25, 0.15, 0.10, 0.05], k=1)[0]
            unit_price = product_prices[prod.id]
            discount_pct = Decimal(str(round(random.choices(
                [0, 5, 10, 15],
                weights=[0.50, 0.25, 0.15, 0.10],
                k=1,
            )[0], 2)))
            line_total = quantity * unit_price * (1 - discount_pct / 100)
            total_amount += line_total

            oi = OrderItem(
                order_id=order.id,
                product_id=prod.id,
                quantity=quantity,
                unit_price=unit_price,
                discount=discount_pct,
            )
            session.add(oi)
            all_order_items.append(oi)

        # Update order total
        order.total_amount = total_amount

        # Create payment
        payment_method = weighted_choice(PAYMENT_METHODS, PAYMENT_METHOD_WEIGHTS)
        if order_status == "cancelled":
            payment_status = weighted_choice(["pending", "failed", "refunded"], [0.30, 0.30, 0.40])
        elif order_status == "delivered":
            payment_status = weighted_choice(["completed", "completed", "completed", "pending"], [0.92, 0.02, 0.03, 0.03])
        else:
            payment_status = weighted_choice(["completed", "pending", "failed"], [0.70, 0.20, 0.10])

        payment_date = order_date + timedelta(minutes=random.randint(0, 30))
        payment = Payment(
            order_id=order.id,
            payment_method=payment_method,
            payment_status=payment_status,
            payment_date=payment_date,
            amount=total_amount,
        )
        session.add(payment)
        all_payments.append(payment)

        # Create shipment
        ship_status = shipment_status_from_order_status(order_status, age_days)
        tracking = generate_tracking_number(fake) if ship_status != "pending" else None

        shipped_date = None
        delivery_date = None
        if ship_status in ("shipped", "delivered", "returned"):
            shipped_date = order_date + timedelta(days=random.randint(1, 3))
        if ship_status == "delivered":
            delivery_date = order_date + timedelta(days=random.randint(3, 10))

        shipment = Shipment(
            order_id=order.id,
            shipment_status=ship_status,
            tracking_number=tracking,
            shipped_date=shipped_date,
            delivery_date=delivery_date,
        )
        session.add(shipment)
        all_shipments.append(shipment)

        all_orders.append(order)

        if (i + 1) % batch_size == 0:
            session.commit()
            logger.info("  Committed %d / %d orders (with items/payments/shipments)", i + 1, count)

    session.commit()
    logger.info(
        "  Created %d orders, %d order items, %d payments, %d shipments.",
        len(all_orders),
        len(all_order_items),
        len(all_payments),
        len(all_shipments),
    )
    return all_orders, all_order_items, all_payments, all_shipments


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed the TechStore Analytics database with realistic demo data.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    parser.add_argument("--categories", type=int, default=8, help="Number of categories to create.")
    parser.add_argument("--suppliers", type=int, default=50, help="Number of suppliers to create.")
    parser.add_argument("--products", type=int, default=500, help="Number of products to create.")
    parser.add_argument("--stores", type=int, default=10, help="Number of stores to create.")
    parser.add_argument("--customers", type=int, default=1000, help="Number of customers to create.")
    parser.add_argument("--orders", type=int, default=10000, help="Number of orders to create.")
    parser.add_argument("--batch-size", type=int, default=500, help="Commit every N records.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Set random seeds for reproducibility
    random.seed(args.seed)
    fake = Faker()
    Faker.seed(args.seed)

    logger.info("=" * 60)
    logger.info("TechStore Analytics — Database Seeder")
    logger.info("=" * 60)
    logger.info("Configuration:")
    logger.info("  Seed:        %d", args.seed)
    logger.info("  Categories:  %d", args.categories)
    logger.info("  Suppliers:   %d", args.suppliers)
    logger.info("  Products:    %d", args.products)
    logger.info("  Stores:      %d", args.stores)
    logger.info("  Customers:   %d", args.customers)
    logger.info("  Orders:      %d", args.orders)
    logger.info("  Batch size:  %d", args.batch_size)
    logger.info("=" * 60)

    start_time = datetime.now()

    session = SessionLocal()
    try:
        # 0. Clear existing data
        clear_existing_data(session)

        # 1. Categories
        categories = seed_categories(session, args.categories)
        session.commit()

        # 2. Suppliers
        suppliers = seed_suppliers(session, fake, args.suppliers)
        session.commit()

        # 3. Products
        products = seed_products(session, fake, categories, suppliers, args.products)
        session.commit()

        # 4. Stores
        stores = seed_stores(session, args.stores)
        session.commit()

        # 5. Customers
        customers = seed_customers(session, fake, args.customers)
        session.commit()

        # 6. Inventory
        inventory = seed_inventory(session, products, stores, args.batch_size)
        session.commit()

        # 7-10. Orders (with items, payments, shipments)
        orders, order_items, payments, shipments = seed_orders(
            session, fake, customers, stores, products, args.orders, args.batch_size,
        )

        elapsed = datetime.now() - start_time

        # Summary
        logger.info("=" * 60)
        logger.info("SEEDING COMPLETE — Summary")
        logger.info("=" * 60)
        logger.info("  Categories:     %d", len(categories))
        logger.info("  Suppliers:      %d", len(suppliers))
        logger.info("  Products:       %d", len(products))
        logger.info("  Stores:         %d", len(stores))
        logger.info("  Customers:      %d", len(customers))
        logger.info("  Inventory:      %d", len(inventory))
        logger.info("  Orders:         %d", len(orders))
        logger.info("  Order Items:    %d", len(order_items))
        logger.info("  Payments:       %d", len(payments))
        logger.info("  Shipments:      %d", len(shipments))
        logger.info("  Total records:  %d",
                    len(categories) + len(suppliers) + len(products) + len(stores)
                    + len(customers) + len(inventory) + len(orders)
                    + len(order_items) + len(payments) + len(shipments))
        logger.info("  Elapsed time:   %s", elapsed)
        logger.info("=" * 60)

    except Exception as exc:
        session.rollback()
        logger.error("Seeding failed: %s", exc, exc_info=True)
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
