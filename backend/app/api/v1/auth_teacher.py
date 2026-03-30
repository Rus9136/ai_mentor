"""
Teacher self-registration endpoints.

Provides public endpoints for teacher registration using a school code.
No authentication required — teachers register themselves and get immediate access.
"""
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
)
from app.core.rate_limiter import limiter, AUTH_RATE_LIMIT
from app.core.errors import APIError, ErrorCode
from app.models.user import User, UserRole, AuthProvider
from app.models.teacher import Teacher
from app.models.teacher_subject import TeacherSubject
from app.repositories.user_repo import UserRepository
from app.repositories.teacher_repo import TeacherRepository
from app.repositories.school_repo import SchoolRepository
from app.repositories.goso_repo import GosoRepository
from app.schemas.auth import (
    TeacherRegisterRequest,
    TeacherRegisterResponse,
    UserResponse,
)
from app.schemas.goso import SubjectListResponse


router = APIRouter()


@router.get("/teacher/subjects", response_model=List[SubjectListResponse])
async def get_subjects_for_registration(
    db: AsyncSession = Depends(get_db),
):
    """
    Get all active GOSO subjects (public, no auth required).

    Used by the teacher registration form to populate subject selection.
    """
    goso_repo = GosoRepository(db)
    subjects = await goso_repo.get_all_subjects(is_active=True)
    return subjects


@router.post("/teacher/register", response_model=TeacherRegisterResponse)
@limiter.limit(AUTH_RATE_LIMIT)
async def register_teacher(
    request: Request,
    data: TeacherRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new teacher using a school code.

    Creates User (role=TEACHER) + Teacher + TeacherSubject records.
    Returns JWT tokens for immediate login.
    """
    school_repo = SchoolRepository(db)
    user_repo = UserRepository(db)
    teacher_repo = TeacherRepository(db)
    goso_repo = GosoRepository(db)

    # 1. Validate school code
    school = await school_repo.get_by_code(data.school_code.strip())
    if not school or not school.is_active:
        raise APIError(ErrorCode.VAL_011, message="Invalid school code")

    # 2. Validate subject IDs
    resolved_subjects = []
    for sid in data.subject_ids:
        subj = await goso_repo.get_subject_by_id(sid)
        if not subj:
            raise APIError(
                ErrorCode.VAL_001,
                message=f"Subject with ID {sid} not found",
            )
        resolved_subjects.append(subj)

    # 3. Check email uniqueness
    email = data.email
    if email:
        existing = await user_repo.get_by_email(email)
        if existing:
            raise APIError(
                ErrorCode.RES_002,
                message="User with this email already exists",
            )
    else:
        email = f"phone_{data.phone}@phone.local"
        existing = await user_repo.get_by_email(email)
        if existing:
            raise APIError(
                ErrorCode.RES_002,
                message="User with this phone already exists",
            )

    # 4. Check phone uniqueness
    if data.phone:
        existing_phone = await user_repo.get_by_phone(data.phone)
        if existing_phone:
            raise APIError(
                ErrorCode.RES_002,
                message="User with this phone already exists",
            )

    # 5. Determine auth provider
    auth_provider = AuthProvider.PHONE if not data.email and data.phone else AuthProvider.LOCAL

    # 5.5. Set RLS context — public endpoint has no JWT, so TenancyMiddleware
    # doesn't set tenant. We must set it manually for INSERT to pass RLS policies.
    await db.execute(
        text("SELECT set_config('app.current_tenant_id', :tid, false)"),
        {"tid": str(school.id)},
    )

    # 6. Create User
    user = User(
        email=email,
        password_hash=get_password_hash(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        middle_name=data.middle_name,
        phone=data.phone,
        role=UserRole.TEACHER,
        school_id=school.id,
        is_active=True,
        auth_provider=auth_provider,
    )
    user = await user_repo.create(user)

    # 7. Generate teacher_code
    year = datetime.now().year % 100
    count = await teacher_repo.count_by_school(school.id)
    teacher_code = f"TCHR{year:02d}{count + 1:04d}"

    # 8. Create Teacher
    first_subject = resolved_subjects[0]
    teacher = Teacher(
        school_id=school.id,
        user_id=user.id,
        teacher_code=teacher_code,
        subject_id=first_subject.id,
        subject=first_subject.name_ru,
    )
    teacher = await teacher_repo.create(teacher)

    # 9. Create TeacherSubject records
    for subj in resolved_subjects:
        ts = TeacherSubject(teacher_id=teacher.id, subject_id=subj.id)
        db.add(ts)
    await db.commit()

    # 10. Generate tokens
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value,
        "school_id": user.school_id,
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return TeacherRegisterResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )
