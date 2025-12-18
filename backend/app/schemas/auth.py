"""
Authentication schemas.
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password")


class TokenResponse(BaseModel):
    """Token response schema."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""

    refresh_token: str = Field(..., description="JWT refresh token")


class UserResponse(BaseModel):
    """User response schema."""

    id: int
    email: str
    role: str
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    school_id: Optional[int] = None
    is_active: bool
    is_verified: bool
    avatar_url: Optional[str] = None
    auth_provider: Optional[str] = None

    class Config:
        from_attributes = True

    @property
    def full_name(self) -> str:
        """Get full name."""
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return " ".join(parts)


class TokenPayload(BaseModel):
    """Token payload schema for internal use."""

    sub: int  # user_id
    email: str
    role: str
    school_id: Optional[int] = None
    exp: int
    type: str  # "access" or "refresh"
