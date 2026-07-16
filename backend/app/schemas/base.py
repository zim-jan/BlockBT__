from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse[T](BaseModel):
    """Standardized API response wrapper."""

    success: bool
    data: T | None = None
    error: str | None = None
