"""
SQLAlchemy declarative base + shared metadata.
All ORM models must inherit from `Base`.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for all BlockBT ORM models."""

    pass
