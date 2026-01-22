"""
OAuth authentication endpoints.

Provides Google OAuth login and student onboarding flow.
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional

from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token
from app.core.config import settings
from app.core.rate_limiter import limiter, AUTH_RATE_LIMIT, ONBOARDING_RATE_LIMIT
from app.core.errors import APIError, ErrorCode
from app.api.dependencies import get_current_user
from app.models.user import User, UserRole, AuthProvider
from app.models.student import Student
from app.repositories.user_repo import UserRepository
from app.repositories.student_repo import StudentRepository
from app.repositories.invitation_code_repo import InvitationCodeRepository
from app.services.google_auth_service import GoogleAuthService, GoogleAuthError
from app.schemas.auth import UserResponse
from app.schemas.invitation_code import (
    ValidateCodeRequest,
    ValidateCodeResponse,
    OnboardingCompleteRequest,
    OnboardingCompleteResponse,
)


router = APIRouter()


# ==========================================
# Request/Response schemas
# ==========================================

class GoogleLoginRequest(BaseModel):
    """Google OAuth login request."""
    id_token: str = Field(..., description="Google ID token from Sign-In")
    client_id: Optional[str] = Field(None, description="Override client ID for mobile apps")


class GoogleLoginResponse(BaseModel):
    """Google OAuth login response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
    requires_onboarding: bool = Field(
        False,
        description="True if user needs to complete onboarding (enter invitation code)"
    )


# ==========================================
# Google OAuth endpoints
# ==========================================

@router.post("/google", response_model=GoogleLoginResponse)
@limiter.limit(AUTH_RATE_LIMIT)
async def google_login(
    request: Request,
    data: GoogleLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate with Google OAuth.

    Flow:
    1. Verify Google ID token
    2. Check if user exists (by google_id or email)
    3. If exists: generate tokens, return user
    4. If new: create user with STUDENT role, set requires_onboarding=True

    Students must complete onboarding to bind to a school before accessing
    the main application.
    """
    # Check if Google OAuth is configured
    if not settings.GOOGLE_CLIENT_ID:
        raise APIError(ErrorCode.SVC_004)  # Google OAuth is not configured

    # Verify Google token
    try:
        google_service = GoogleAuthService(client_id=data.client_id or settings.GOOGLE_CLIENT_ID)
        google_info = await google_service.verify_token(data.id_token)
    except GoogleAuthError as e:
        raise APIError(ErrorCode.AUTH_006, message=str(e))  # Google authentication failed

    user_repo = UserRepository(db)
    student_repo = StudentRepository(db)

    # Try to find existing user by Google ID
    user = await user_repo.get_by_google_id(google_info.google_id)

    # If not found by Google ID, try by email
    if not user:
        user = await user_repo.get_by_email(google_info.email)

    # If still not found, check for soft-deleted user with same email
    # This handles the case when user deleted account and wants to re-register
    if not user:
        deleted_user = await user_repo.get_by_email_include_deleted(google_info.email)
        if deleted_user and deleted_user.is_deleted:
            # Restore the deleted user
            user = await user_repo.restore(deleted_user)
            user.google_id = google_info.google_id
            user.auth_provider = AuthProvider.GOOGLE
            if google_info.avatar_url:
                user.avatar_url = google_info.avatar_url
            await user_repo.update(user)

            # Also restore the student record if exists
            deleted_student = await student_repo.get_by_user_id_include_deleted(user.id)
            if deleted_student and deleted_student.is_deleted:
                await student_repo.restore(deleted_student)

    requires_onboarding = False

    if user:
        # Existing user - update Google ID if needed
        if not user.google_id:
            user.google_id = google_info.google_id
            user.auth_provider = AuthProvider.GOOGLE
            if google_info.avatar_url:
                user.avatar_url = google_info.avatar_url
            await user_repo.update(user)

        # Check if user is active
        if not user.is_active:
            raise APIError(ErrorCode.ACCESS_004)  # User account is inactive

        # Check if student has completed onboarding (has school_id)
        if user.role == UserRole.STUDENT and user.school_id is None:
            requires_onboarding = True
    else:
        # New user - create with STUDENT role
        user = User(
            email=google_info.email,
            google_id=google_info.google_id,
            auth_provider=AuthProvider.GOOGLE,
            first_name=google_info.first_name or "Новый",
            last_name=google_info.last_name or "Ученик",
            avatar_url=google_info.avatar_url,
            role=UserRole.STUDENT,
            school_id=None,  # Will be set during onboarding
            is_active=True,
            is_verified=google_info.email_verified,
            password_hash=None  # No password for OAuth users
        )
        user = await user_repo.create(user)
        requires_onboarding = True

    # Generate tokens
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value,
        "school_id": user.school_id,
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return GoogleLoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
        requires_onboarding=requires_onboarding
    )


# ==========================================
# Onboarding endpoints
# ==========================================

@router.post("/onboarding/validate-code", response_model=ValidateCodeResponse)
@limiter.limit(ONBOARDING_RATE_LIMIT)
async def validate_invitation_code(
    request: Request,
    data: ValidateCodeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Validate an invitation code.

    Returns information about the school and class if the code is valid.
    Does not consume the code - that happens during onboarding completion.
    """
    # Only students without school can validate codes
    if current_user.role != UserRole.STUDENT:
        raise APIError(ErrorCode.ACCESS_002, message="Only students can use invitation codes")

    if current_user.school_id is not None:
        raise APIError(ErrorCode.VAL_006)  # User already belongs to a school

    code_repo = InvitationCodeRepository(db)
    is_valid, error, invitation_code = await code_repo.validate_code(data.code)

    if not is_valid:
        return ValidateCodeResponse(
            valid=False,
            error=error
        )

    # Build response with school and class info
    school_info = {
        "id": invitation_code.school.id,
        "name": invitation_code.school.name,
        "code": invitation_code.school.code
    }

    class_info = None
    if invitation_code.school_class:
        class_info = {
            "id": invitation_code.school_class.id,
            "name": invitation_code.school_class.name,
            "grade_level": invitation_code.school_class.grade_level
        }

    return ValidateCodeResponse(
        valid=True,
        school=school_info,
        school_class=class_info,
        grade_level=invitation_code.grade_level
    )


@router.post("/onboarding/complete", response_model=OnboardingCompleteResponse)
@limiter.limit(ONBOARDING_RATE_LIMIT)
async def complete_onboarding(
    request: Request,
    data: OnboardingCompleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Complete student onboarding by binding to a school.

    Creates a Student record and updates the User with school_id.
    Consumes one use of the invitation code.
    """
    # Only students without school can complete onboarding
    if current_user.role != UserRole.STUDENT:
        raise APIError(ErrorCode.ACCESS_002, message="Only students can complete onboarding")

    if current_user.school_id is not None:
        raise APIError(ErrorCode.VAL_006)  # User already belongs to a school

    # Validate invitation code
    code_repo = InvitationCodeRepository(db)
    is_valid, error, invitation_code = await code_repo.validate_code(data.invitation_code)

    if not is_valid:
        # Map validation error to appropriate code
        if error == "Invitation code has expired":
            raise APIError(ErrorCode.VAL_004)  # Code expired
        elif error == "Invitation code has reached its usage limit":
            raise APIError(ErrorCode.VAL_005)  # Usage limit reached
        else:
            raise APIError(ErrorCode.VAL_003, message=error or "Invalid invitation code")

    # Update user profile
    user_repo = UserRepository(db)
    current_user.first_name = data.first_name
    current_user.last_name = data.last_name
    if data.middle_name:
        current_user.middle_name = data.middle_name
    current_user.school_id = invitation_code.school_id
    current_user.is_verified = True  # Mark as verified after onboarding
    await user_repo.update(current_user)

    # Create student record
    student_repo = StudentRepository(db)

    # Check if student already exists for this user
    existing_student = await student_repo.get_by_user_id(current_user.id)
    if existing_student:
        student = existing_student
        student.school_id = invitation_code.school_id
        student.grade_level = invitation_code.grade_level
        await student_repo.update(student)
    else:
        # Generate student code
        student_code = await student_repo.generate_student_code(invitation_code.school_id)

        student = Student(
            user_id=current_user.id,
            school_id=invitation_code.school_id,
            student_code=student_code,
            grade_level=invitation_code.grade_level,
            birth_date=data.birth_date
        )
        student = await student_repo.create(student)

    # Create join request instead of auto-adding to class
    # Teacher will approve/reject the request
    pending_request = None
    if invitation_code.class_id and invitation_code.school_class:
        from app.repositories.join_request_repo import JoinRequestRepository
        join_repo = JoinRequestRepository(db)

        # Check if already has a request for this class
        existing_request = await join_repo.get_by_student_and_class(
            student.id, invitation_code.class_id
        )
        if not existing_request:
            pending_request = await join_repo.create(
                student_id=student.id,
                class_id=invitation_code.class_id,
                school_id=invitation_code.school_id,
                invitation_code_id=invitation_code.id
            )

    # Note: We don't record code usage here anymore
    # Code usage is recorded when teacher approves the request

    # Generate new tokens with updated school_id
    token_data = {
        "sub": str(current_user.id),
        "email": current_user.email,
        "role": current_user.role.value,
        "school_id": current_user.school_id,
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": str(current_user.id)})

    # Build student response
    student_classes = []  # Empty - student is not in any class yet

    # Add pending request info if exists
    pending_request_info = None
    if pending_request and invitation_code.school_class:
        pending_request_info = {
            "id": pending_request.id,
            "class_id": invitation_code.class_id,
            "class_name": invitation_code.school_class.name,
            "status": "pending"
        }

    student_info = {
        "id": student.id,
        "student_code": student.student_code,
        "grade_level": student.grade_level,
        "classes": student_classes,
        "pending_request": pending_request_info
    }

    return OnboardingCompleteResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(current_user).model_dump(),
        student=student_info
    )
