"""
Authentication schemas.
"""
import re
from typing import Optional, List
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

    @field_validator("login")
    @classmethod
    def normalize_phone_login(cls, v: str) -> str:
        """Normalize phone-like inputs (87077880094, 77077880094) to +7XXXXXXXXXX."""
        v = v.strip()
        if "@" in v:
            return v
        # If it looks like a phone number (digits, optional +, spaces, dashes, parens)
        cleaned = re.sub(r"\D", "", v)
        if len(cleaned) >= 10:
            return normalize_kz_phone(v)
        return v

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


def normalize_kz_phone(raw: str) -> str:
    """Normalize Kazakhstan phone number to +7XXXXXXXXXX format.

    Accepts: +77077880094, 87077880094, 77077880094, 7077880094,
             +7 (707) 788-00-94 (formatted with spaces/dashes/parens)
    Returns: +77077880094
    Raises ValueError if cannot normalize to valid format.
    """
    # Strip everything except digits
    digits = re.sub(r"\D", "", raw.strip())
    if len(digits) == 11 and digits.startswith("8"):
        # 87077880094 → 77077880094
        digits = "7" + digits[1:]
    if len(digits) == 11 and digits.startswith("7"):
        return "+" + digits
    if len(digits) == 10:
        # 7077880094 → +77077880094
        return "+7" + digits
    # Cannot normalize — return with + so regex validator gives clear error
    return "+" + digits


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
        v = normalize_kz_phone(v)
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
        v = normalize_kz_phone(v)
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


class TeacherRegisterRequest(BaseModel):
    """Teacher self-registration request schema."""

    school_code: str = Field(..., min_length=1, description="School code provided by admin")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, description="Phone number in +7XXXXXXXXXX format")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    subject_ids: List[int] = Field(..., min_length=1, description="At least one subject required")
    class_ids: Optional[List[int]] = Field(None, description="Optional class IDs to join")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v != "":
            v = normalize_kz_phone(v)
            if not _KZ_PHONE_RE.match(v):
                raise ValueError("Phone must be in +7XXXXXXXXXX format")
            return v
        return None

    @model_validator(mode="after")
    def check_email_or_phone(self):
        if not self.email and not self.phone:
            raise ValueError("Either email or phone must be provided")
        return self


class TeacherRegisterResponse(BaseModel):
    """Teacher registration response with tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
