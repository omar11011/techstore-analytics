"""
Database configuration module for TechStore Analytics.

Provides SQLAlchemy engine, session factory, declarative base,
and FastAPI dependency for database session management.
"""

import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from typing import Generator

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Database URL
# ---------------------------------------------------------------------------
# Load from environment variable with a sensible fallback for local
# development.  The default uses psycopg2 as the synchronous driver.
# ---------------------------------------------------------------------------

DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql://techstore:techstore@localhost:5432/techstore",
)

# Ensure we use the psycopg2 driver explicitly if a postgres:// scheme is
# provided (e.g. by platforms like Heroku).
# Only normalize PostgreSQL URLs – ignore SQLite or other schemes.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
elif DATABASE_URL.startswith("postgresql://") and "+" not in DATABASE_URL.split("://")[1][:20]:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
# pool_pre_ping – validates connections before checkout so stale connections
#                 in the pool are automatically recycled.
# pool_size     – number of connections to keep in the pool.
# max_overflow  – additional connections allowed beyond pool_size.
# echo          – set to True for SQL statement logging (debug only).
# ---------------------------------------------------------------------------

# SQLite does not support pool_size / max_overflow; adjust kwargs accordingly.
_engine_kwargs: dict = {"echo": False}
if DATABASE_URL.startswith("postgresql"):
    _engine_kwargs.update(pool_pre_ping=True, pool_size=10, max_overflow=20)
else:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **_engine_kwargs)

logger.info("Database engine created for: %s", DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else DATABASE_URL)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# ---------------------------------------------------------------------------
# Declarative base
# ---------------------------------------------------------------------------

Base = declarative_base()


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

def get_db() -> Generator[Session, None, None]:
    """Yield a database session for use as a FastAPI dependency.

    The session is automatically closed when the request finishes.  If an
    exception occurs the transaction is rolled back before the session is
    closed.

    Yields:
        Session: An active SQLAlchemy database session.
    """
    db: Session = SessionLocal()
    try:
        yield db
    except Exception as exc:
        logger.error("Database session error: %s", exc)
        db.rollback()
        raise
    finally:
        db.close()
