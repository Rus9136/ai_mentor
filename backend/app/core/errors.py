"""
Standardized error codes and API error handling.

This module provides:
- ErrorCode enum with categorized error codes
- ERROR_MESSAGES dict with default English messages
- APIError exception class for structured error responses
- Convenience factory functions for common errors
"""

from enum import Enum
from typing import Optional, Dict, Any
from fastapi import HTTPException, status


class ErrorCode(str, Enum):
    """
    Centralized error codes catalog.

    Format: CATEGORY_NUMBER
    Categories:
        - AUTH: Authentication errors (401)
        - ACCESS: Authorization/permission errors (403)
        - VAL: Validation errors (400/422)
        - RES: Resource errors (404/409)
        - SVC: Service/internal errors (500/503)
        - RATE: Rate limiting (429)
    """

    # === AUTH (401) - Authentication ===
    AUTH_001 = "AUTH_001"  # Invalid credentials
    AUTH_002 = "AUTH_002"  # Token expired
    AUTH_003 = "AUTH_003"  # Invalid/malformed token
    AUTH_004 = "AUTH_004"  # Token type mismatch (access vs refresh)
    AUTH_005 = "AUTH_005"  # User not found (from token)
    AUTH_006 = "AUTH_006"  # Google OAuth error
    AUTH_007 = "AUTH_007"  # Invalid refresh token

    # === ACCESS (403) - Authorization ===
    ACCESS_001 = "ACCESS_001"  # Insufficient permissions (generic)
    ACCESS_002 = "ACCESS_002"  # Role not allowed for this action
    ACCESS_003 = "ACCESS_003"  # Resource belongs to another school
    ACCESS_004 = "ACCESS_004"  # User account is inactive
    ACCESS_005 = "ACCESS_005"  # Not resource owner
    ACCESS_006 = "ACCESS_006"  # Homework not assigned to student

    # === VALIDATION (400/422) ===
    VAL_001 = "VAL_001"  # Invalid input format (generic)
    VAL_002 = "VAL_002"  # Missing required field
    VAL_003 = "VAL_003"  # Invalid invitation code
    VAL_004 = "VAL_004"  # Invitation code expired
    VAL_005 = "VAL_005"  # Invitation code usage limit reached
    VAL_006 = "VAL_006"  # User already has school
    VAL_007 = "VAL_007"  # Invalid question type
    VAL_008 = "VAL_008"  # Cannot modify after publishing
    VAL_009 = "VAL_009"  # Late submission not allowed
    VAL_010 = "VAL_010"  # No attempts remaining

    # === RESOURCE (404/409) ===
    RES_001 = "RES_001"  # Generic resource not found
    RES_002 = "RES_002"  # Resource already exists (conflict)
    RES_003 = "RES_003"  # Textbook not found
    RES_004 = "RES_004"  # Chapter not found
    RES_005 = "RES_005"  # Paragraph not found
    RES_006 = "RES_006"  # Student not found
    RES_007 = "RES_007"  # Teacher not found
    RES_008 = "RES_008"  # Homework not found
    RES_009 = "RES_009"  # Task not found
    RES_010 = "RES_010"  # Submission not found
    RES_011 = "RES_011"  # Test not found
    RES_012 = "RES_012"  # Question not found
    RES_013 = "RES_013"  # User not found
    RES_014 = "RES_014"  # School not found
    RES_015 = "RES_015"  # Class not found

    # === SERVICE (500/503) ===
    SVC_001 = "SVC_001"  # Internal server error (generic)
    SVC_002 = "SVC_002"  # LLM service unavailable
    SVC_003 = "SVC_003"  # Embedding service error
    SVC_004 = "SVC_004"  # Google OAuth not configured
    SVC_005 = "SVC_005"  # AI generation failed
    SVC_006 = "SVC_006"  # Database error

    # === RATE (429) ===
    RATE_001 = "RATE_001"  # Rate limit exceeded


# Default English messages for each error code
ERROR_MESSAGES: Dict[ErrorCode, str] = {
    # AUTH
    ErrorCode.AUTH_001: "Incorrect email or password",
    ErrorCode.AUTH_002: "Token has expired",
    ErrorCode.AUTH_003: "Could not validate credentials",
    ErrorCode.AUTH_004: "Invalid token type",
    ErrorCode.AUTH_005: "User not found",
    ErrorCode.AUTH_006: "Google authentication failed",
    ErrorCode.AUTH_007: "Invalid refresh token",

    # ACCESS
    ErrorCode.ACCESS_001: "You don't have permission to perform this action",
    ErrorCode.ACCESS_002: "Your role is not allowed for this operation",
    ErrorCode.ACCESS_003: "Access denied to this resource",
    ErrorCode.ACCESS_004: "User account is inactive",
    ErrorCode.ACCESS_005: "You can only access your own resources",
    ErrorCode.ACCESS_006: "Homework not assigned to you",

    # VALIDATION
    ErrorCode.VAL_001: "Invalid input format",
    ErrorCode.VAL_002: "Missing required field",
    ErrorCode.VAL_003: "Invalid invitation code",
    ErrorCode.VAL_004: "Invitation code has expired",
    ErrorCode.VAL_005: "Invitation code usage limit reached",
    ErrorCode.VAL_006: "User already belongs to a school",
    ErrorCode.VAL_007: "Invalid question type",
    ErrorCode.VAL_008: "Cannot modify after publishing",
    ErrorCode.VAL_009: "Late submission is not allowed",
    ErrorCode.VAL_010: "No attempts remaining",

    # RESOURCE
    ErrorCode.RES_001: "Resource not found",
    ErrorCode.RES_002: "Resource already exists",
    ErrorCode.RES_003: "Textbook not found",
    ErrorCode.RES_004: "Chapter not found",
    ErrorCode.RES_005: "Paragraph not found",
    ErrorCode.RES_006: "Student record not found",
    ErrorCode.RES_007: "Teacher record not found",
    ErrorCode.RES_008: "Homework not found",
    ErrorCode.RES_009: "Task not found",
    ErrorCode.RES_010: "Submission not found",
    ErrorCode.RES_011: "Test not found",
    ErrorCode.RES_012: "Question not found",
    ErrorCode.RES_013: "User not found",
    ErrorCode.RES_014: "School not found",
    ErrorCode.RES_015: "Class not found",

    # SERVICE
    ErrorCode.SVC_001: "Internal server error",
    ErrorCode.SVC_002: "AI service is temporarily unavailable",
    ErrorCode.SVC_003: "Embedding service error",
    ErrorCode.SVC_004: "Google OAuth is not configured",
    ErrorCode.SVC_005: "AI question generation failed",
    ErrorCode.SVC_006: "Database error",

    # RATE
    ErrorCode.RATE_001: "Too many requests. Please try again later",
}


# Map error code category to HTTP status code
_CATEGORY_STATUS_MAP: Dict[str, int] = {
    "AUTH": status.HTTP_401_UNAUTHORIZED,
    "ACCESS": status.HTTP_403_FORBIDDEN,
    "VAL": status.HTTP_400_BAD_REQUEST,
    "RES": status.HTTP_404_NOT_FOUND,
    "SVC": status.HTTP_500_INTERNAL_SERVER_ERROR,
    "RATE": status.HTTP_429_TOO_MANY_REQUESTS,
}


class APIError(HTTPException):
    """
    Structured API error that produces ErrorResponse format.

    Extends FastAPI's HTTPException with:
    - Automatic status code detection from error code category
    - Structured detail dict with code, message, and optional context
    - Backward compatibility (detail field contains message string)

    Usage:
        # Simple usage with default message
        raise APIError(ErrorCode.AUTH_001)

        # Custom message
        raise APIError(ErrorCode.RES_001, message="Student 123 not found")

        # With metadata
        raise APIError(ErrorCode.RES_001, meta={"resource_id": 123, "resource_type": "Student"})

        # For validation errors with field
        raise APIError(ErrorCode.VAL_001, message="Invalid email format", field="email")

        # Override status code (rarely needed)
        raise APIError(ErrorCode.RES_002, status_code=409)  # Conflict
    """

    def __init__(
        self,
        code: ErrorCode,
        message: Optional[str] = None,
        status_code: Optional[int] = None,
        field: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        self.error_code = code
        self.error_message = message or ERROR_MESSAGES.get(code, "Unknown error")
        self.field = field
        self.meta = meta

        # Auto-detect status code from error code category
        if status_code is None:
            status_code = self._get_status_from_code(code)

        # Special case: RES_002 (already exists) should be 409 Conflict
        if code == ErrorCode.RES_002 and status_code == status.HTTP_404_NOT_FOUND:
            status_code = status.HTTP_409_CONFLICT

        # Build structured detail dict
        detail: Dict[str, Any] = {
            "code": code.value,
            "message": self.error_message,
            "detail": self.error_message,  # Backward compatibility
        }
        if field:
            detail["field"] = field
        if meta:
            detail["meta"] = meta

        # Add WWW-Authenticate header for 401 errors
        if status_code == status.HTTP_401_UNAUTHORIZED:
            headers = headers or {}
            headers.setdefault("WWW-Authenticate", "Bearer")

        super().__init__(status_code=status_code, detail=detail, headers=headers)

    @staticmethod
    def _get_status_from_code(code: ErrorCode) -> int:
        """Map error code category to HTTP status."""
        category = code.value.split("_")[0]
        return _CATEGORY_STATUS_MAP.get(category, status.HTTP_400_BAD_REQUEST)


# ============================================================================
# Convenience factory functions
# ============================================================================

def auth_error(
    code: ErrorCode = ErrorCode.AUTH_001,
    message: Optional[str] = None,
    **kwargs
) -> APIError:
    """Create authentication error (401)."""
    return APIError(code, message=message, **kwargs)


def access_denied(
    code: ErrorCode = ErrorCode.ACCESS_001,
    message: Optional[str] = None,
    **kwargs
) -> APIError:
    """Create access denied error (403)."""
    return APIError(code, message=message, **kwargs)


def not_found(
    resource: str,
    resource_id: Optional[int] = None,
    code: ErrorCode = ErrorCode.RES_001,
) -> APIError:
    """
    Create resource not found error (404).

    Usage:
        raise not_found("Student", 123)
        raise not_found("Homework")
    """
    message = f"{resource} not found"
    meta = None
    if resource_id is not None:
        meta = {"resource_type": resource, "resource_id": resource_id}
    return APIError(code, message=message, meta=meta)


def validation_error(
    message: str,
    field: Optional[str] = None,
    code: ErrorCode = ErrorCode.VAL_001,
) -> APIError:
    """Create validation error (400)."""
    return APIError(code, message=message, field=field)


def conflict(
    message: str,
    code: ErrorCode = ErrorCode.RES_002,
) -> APIError:
    """Create conflict error (409)."""
    return APIError(code, message=message, status_code=status.HTTP_409_CONFLICT)


def service_unavailable(
    message: Optional[str] = None,
    code: ErrorCode = ErrorCode.SVC_002,
) -> APIError:
    """Create service unavailable error (503)."""
    return APIError(
        code,
        message=message,
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE
    )
