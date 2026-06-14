"""
Base repository providing common CRUD operations for all entities.

All concrete repositories inherit from ``BaseRepository`` which implements
standard create, read, update, delete, and list operations using the
SQLAlchemy ORM.
"""

from __future__ import annotations

import logging
from typing import Any, Generic, List, Optional, Type, TypeVar

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.models import Base

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic data-access layer for a SQLAlchemy model.

    Parameters
    ----------
    model : Type[ModelType]
        The SQLAlchemy model class this repository manages.
    """

    def __init__(self, model: Type[ModelType]) -> None:
        self.model = model

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    def create(self, db: Session, **kwargs: Any) -> ModelType:
        """Insert a new row and return the persisted instance."""
        instance = self.model(**kwargs)
        db.add(instance)
        db.flush()
        logger.debug("Created %s with id=%s", self.model.__name__, instance.id)
        return instance

    # ------------------------------------------------------------------
    # READ
    # ------------------------------------------------------------------

    def get_by_id(self, db: Session, id: int) -> Optional[ModelType]:
        """Fetch a single row by primary key, or ``None``."""
        return db.query(self.model).filter(self.model.id == id).first()

    def get_all(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ModelType]:
        """Return a slice of all rows."""
        return (
            db.query(self.model)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count(self, db: Session) -> int:
        """Return the total number of rows."""
        return db.query(func.count(self.model.id)).scalar() or 0

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------

    def update(self, db: Session, id: int, **kwargs: Any) -> Optional[ModelType]:
        """Update one or more columns on the row identified by *id*."""
        instance = self.get_by_id(db, id)
        if instance is None:
            return None
        for key, value in kwargs.items():
            if value is not None:
                setattr(instance, key, value)
        db.flush()
        logger.debug("Updated %s id=%s", self.model.__name__, id)
        return instance

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------

    def delete(self, db: Session, id: int) -> bool:
        """Delete the row identified by *id*. Returns ``True`` on success."""
        instance = self.get_by_id(db, id)
        if instance is None:
            return False
        db.delete(instance)
        db.flush()
        logger.debug("Deleted %s id=%s", self.model.__name__, id)
        return True
