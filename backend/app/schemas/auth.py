"""
Authentication schemas.
"""
import re
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class LoginRequest(BaseModel):
    """Login request schema. Accepts email or phone (+7XXXXXXXXXX) as login identifier."""

    login: str = Field(..., description="Email or phone number (+7XXXXXXXXXX)")
    password: str = Field(..., min_length=6, description="User password")

    @model_validator(mode='before')
    @classmethod
    def handle_email_compat(cls, data):
        """Backward compatibility: map {email, password} → {login, password}."""
        if isinstance(data, dict) and 'email' in data and 'login' not in data:
            data['login'] = data['email']
        return data

    @property
    def is_phone(self) -> bool:
        """Check if login is a phone number."""
        return self.login.startswith('+')


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
    phone: Optional[str] = None

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


# Phone number regex: Kazakhstan format +7XXXXXXXXXX (11 digits)
_KZ_PHONE_RE = re.compile(r"^\+7\d{10}$")


class PhoneRegisterRequest(BaseModel):
    """Phone registration request schema."""

    phone: str = Field(..., description="Phone number in +7XXXXXXXXXX format")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, min_length=6, description="Optional password (for future use)")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not _KZ_PHONE_RE.match(v):
            raise ValueError("Phone must be in +7XXXXXXXXXX format")
        return v


class PhoneLoginRequest(BaseModel):
    """Phone login request schema."""

    phone: str = Field(..., description="Phone number in +7XXXXXXXXXX format")
    password: Optional[str] = Field(None, description="Optional password (for future use)")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not _KZ_PHONE_RE.match(v):
            raise ValueError("Phone must be in +7XXXXXXXXXX format")
        return v


class ChangePasswordRequest(BaseModel):
    """Change password request schema."""

    current_password: str = Field(..., min_length=1, description="Current password")
    new_password: str = Field(..., min_length=8, description="New password (min 8 characters)")


class ChangePasswordResponse(BaseModel):
    """Change password response schema."""

    message: str = "Password changed successfully"


class PhoneAuthResponse(BaseModel):
    """Phone auth response (register/login)."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
    requires_onboarding: bool = Field(
        False,
        description="True if user needs to complete onboarding (enter invitation code)"
    )
