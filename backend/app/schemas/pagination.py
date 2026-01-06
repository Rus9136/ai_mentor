"""
Generic pagination schemas and utilities.

Usage:
    from app.schemas.pagination import PaginatedResponse, PaginationParams
    from app.api.dependencies import get_pagination_params

    @router.get("", response_model=PaginatedResponse[StudentListResponse])
    async def list_students(
        pagination: PaginationParams = Depends(get_pagination_params),
        ...
    ):
        students, total = await repo.get_all_paginated(
            school_id, page=pagination.page, page_size=pagination.page_size
        )
        return PaginatedResponse.create(students, total, pagination.page, pagination.page_size)
"""

from typing import TypeVar, Generic, List
from math import ceil
from pydantic import BaseModel, Field, ConfigDict

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Query parameters for pagination."""

    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        """Convert page/page_size to offset for DB queries."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Alias for page_size for DB queries."""
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response wrapper.

    Example response:
    {
        "items": [...],
        "total": 150,
        "page": 1,
        "page_size": 20,
        "total_pages": 8
    }
    """

    model_config = ConfigDict(from_attributes=True)

    items: List[T] = Field(..., description="List of items for current page")
    total: int = Field(..., ge=0, description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")

    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        """
        Factory method to create response with calculated total_pages.

        Args:
            items: List of items for current page
            total: Total count of all items
            page: Current page number (1-indexed)
            page_size: Number of items per page

        Returns:
            PaginatedResponse instance with calculated total_pages
        """
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=ceil(total / page_size) if page_size > 0 else 0,
        )

    @classmethod
    def empty(cls, page: int = 1, page_size: int = 20) -> "PaginatedResponse[T]":
        """Create an empty paginated response."""
        return cls(
            items=[],
            total=0,
            page=page,
            page_size=page_size,
            total_pages=0,
        )
