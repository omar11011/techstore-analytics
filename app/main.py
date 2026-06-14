"""
TechStore Analytics API – FastAPI application entry point.

Creates the FastAPI application instance, registers all API routers
under the ``/api/v1`` prefix, configures CORS middleware, and provides
a health-check endpoint and global exception handlers.
"""

import logging
import sys
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.analytics import router as analytics_router
from app.api.categories import router as categories_router
from app.api.customers import router as customers_router
from app.api.inventory import router as inventory_router
from app.api.orders import router as orders_router
from app.api.payments import router as payments_router
from app.api.products import router as products_router
from app.api.shipments import router as shipments_router
from app.api.stores import router as stores_router
from app.api.suppliers import router as suppliers_router

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("techstore")


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    """Application lifespan handler.

    Runs on startup and shutdown of the FastAPI application.
    """
    logger.info("TechStore Analytics API starting up …")
    logger.info("API version: 1.0.0")
    logger.info("All routers registered under /api/v1")
    yield
    logger.info("TechStore Analytics API shutting down …")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="TechStore Analytics API",
    version="1.0.0",
    description=(
        "A comprehensive analytics backend for TechStore – "
        "providing CRUD operations for customers, products, categories, "
        "suppliers, stores, inventory, orders, payments, and shipments, "
        "along with rich reporting and dashboard analytics endpoints."
    ),
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# CORS middleware
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],            # Allow all HTTP methods
    allow_headers=["*"],            # Allow all headers
)


# ---------------------------------------------------------------------------
# Global exception handlers
# ---------------------------------------------------------------------------

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Handle uncaught ``ValueError`` exceptions as 400 Bad Request."""
    logger.warning("ValueError on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other uncaught exceptions as 500 Internal Server Error."""
    logger.error(
        "Unhandled exception on %s %s: %s",
        request.method,
        request.url.path,
        exc,
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected internal server error occurred."},
    )


# ---------------------------------------------------------------------------
# Request timing middleware
# ---------------------------------------------------------------------------

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add an ``X-Process-Time`` header to every response."""
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}"
    return response


# ---------------------------------------------------------------------------
# Health check endpoint
# ---------------------------------------------------------------------------

@app.get(
    "/health",
    tags=["Health"],
    summary="Health check",
    description="Returns the operational status of the API.",
)
def health_check() -> dict:
    """Return a simple health-check payload.

    Returns:
        A dict with status, service name, and version.
    """
    return {
        "status": "healthy",
        "service": "TechStore Analytics API",
        "version": "1.0.0",
    }


# ---------------------------------------------------------------------------
# Register routers under /api/v1
# ---------------------------------------------------------------------------

app.include_router(customers_router, prefix="/api/v1")
app.include_router(products_router, prefix="/api/v1")
app.include_router(categories_router, prefix="/api/v1")
app.include_router(suppliers_router, prefix="/api/v1")
app.include_router(stores_router, prefix="/api/v1")
app.include_router(inventory_router, prefix="/api/v1")
app.include_router(orders_router, prefix="/api/v1")
app.include_router(payments_router, prefix="/api/v1")
app.include_router(shipments_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
