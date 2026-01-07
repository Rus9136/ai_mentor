"""
Standardized error response schemas.

Provides structured error responses with error codes for better
client-side handling and i18n support.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ValidationErrorDetail(BaseModel):
    """Individual field validation error."""

    field: str = Field(..., description="Field name that failed validation")
    code: str = Field(..., description="Error code (e.g., 'VAL_001')")
    message: str = Field(..., description="Human-readable error message")


class ErrorResponse(BaseModel):
    """
    Standardized API error response.

    Provides backward compatibility with existing `detail: string` format
    while adding structured error information for better client handling.

    Example response:
    ```json
    {
        "code": "AUTH_001",
        "message": "Incorrect email or password",
        "detail": "Incorrect email or password",
        "field": null,
        "errors": null,
        "meta": null
    }
    ```
    """

    # Primary fields (always present)
    code: str = Field(
        ...,
        description="Error code (e.g., 'AUTH_001', 'RES_001')",
        examples=["AUTH_001", "RES_001", "VAL_001"]
    )
    message: str = Field(
        ...,
        description="Human-readable error message (English)",
        examples=["Incorrect email or password", "Resource not found"]
    )

    # Backward compatibility - same as message
    detail: str = Field(
        ...,
        description="Alias for message (backward compatibility with FastAPI)"
    )

    # Optional context fields
    field: Optional[str] = Field(
        None,
        description="Field name for single-field validation errors"
    )
    errors: Optional[List[ValidationErrorDetail]] = Field(
        None,
        description="Multiple validation errors (for 422 responses)"
    )
    meta: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional context (e.g., retry_after, resource_id, resource_type)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "code": "AUTH_001",
                    "message": "Incorrect email or password",
                    "detail": "Incorrect email or password",
                    "field": None,
                    "errors": None,
                    "meta": None
                },
                {
                    "code": "RES_001",
                    "message": "Student not found",
                    "detail": "Student not found",
                    "field": None,
                    "errors": None,
                    "meta": {"resource_type": "Student", "resource_id": 123}
                },
                {
                    "code": "VAL_001",
                    "message": "Validation error",
                    "detail": "Validation error",
                    "field": None,
                    "errors": [
                        {"field": "email", "code": "VAL_001", "message": "Invalid email format"},
                        {"field": "password", "code": "VAL_002", "message": "Password too short"}
                    ],
                    "meta": None
                }
            ]
        }
    }
