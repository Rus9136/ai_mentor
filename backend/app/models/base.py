"""
Base model classes and mixins.
"""
from datetime import datetime
from typing import Any
from sqlalchemy import Column, Integer, DateTime, Boolean, func
from sqlalchemy.orm import declarative_mixin, declared_attr

from app.core.database import Base


@declarative_mixin
class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    @declared_attr
    def created_at(cls) -> Column:
        return Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    @declared_attr
    def updated_at(cls) -> Column:
        return Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        )


@declarative_mixin
class SoftDeleteMixin:
    """Mixin for soft delete functionality."""

    @declared_attr
    def deleted_at(cls) -> Column:
        return Column(DateTime(timezone=True), nullable=True)

    @declared_attr
    def is_deleted(cls) -> Column:
        return Column(Boolean, default=False, nullable=False)


class BaseModel(Base, TimestampMixin):
    """
    Base model class with id, created_at, and updated_at fields.
    """

    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    def to_dict(self) -> dict[str, Any]:
        """Convert model instance to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class SoftDeleteModel(BaseModel, SoftDeleteMixin):
    """
    Base model with soft delete capability.
    """

    __abstract__ = True
