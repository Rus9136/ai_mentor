"""
Main FastAPI application.
"""

import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from pathlib import Path
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.database import engine
from app.core.rate_limiter import limiter
from app.core.errors import APIError, ErrorCode, ERROR_MESSAGES
from app.middleware.tenancy import TenancyMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup
    print("Starting up AI Mentor API...")
    print(
        f"Database URL: {settings.async_database_url.replace(settings.POSTGRES_PASSWORD, '***')}"
    )

    # Create uploads directory if it doesn't exist
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    print(f"Upload directory: {upload_dir.absolute()}")

    yield

    # Shutdown
    print("Shutting down AI Mentor API...")
    await engine.dispose()


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI Mentor - Adaptive Educational Platform API",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ============================================================================
# Custom Exception Handlers
# ============================================================================

@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    """
    Handle structured API errors.

    APIError already contains structured detail dict with code, message, etc.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail,
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Convert Pydantic validation errors to structured ErrorResponse format.

    Returns errors array for multiple validation failures.
    """
    errors = []
    for error in exc.errors():
        # Skip 'body' prefix in location
        loc = error.get("loc", ())
        field = ".".join(str(loc_part) for loc_part in loc[1:]) if len(loc) > 1 else str(loc[0]) if loc else "unknown"

        errors.append({
            "field": field,
            "code": "VAL_001",
            "message": error.get("msg", "Validation error"),
        })

    logger.warning(
        f"Validation error on {request.method} {request.url.path}: {errors}"
    )

    return JSONResponse(
        status_code=422,
        content={
            "code": "VAL_001",
            "message": "Validation error",
            "detail": "Validation error",
            "field": None,
            "errors": errors,
            "meta": None,
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Catch-all handler for unhandled exceptions.

    Logs the full traceback and returns a generic error response.
    """
    logger.exception("Unhandled exception", exc_info=exc)

    return JSONResponse(
        status_code=500,
        content={
            "code": ErrorCode.SVC_001.value,
            "message": ERROR_MESSAGES[ErrorCode.SVC_001],
            "detail": ERROR_MESSAGES[ErrorCode.SVC_001],
            "field": None,
            "errors": None,
            "meta": None,
        },
    )

# Configure CORS - явный список методов и заголовков для безопасности
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-CSRF-Token",
    ],
)

# Configure Tenancy Middleware for RLS (Row Level Security)
# This middleware automatically sets tenant context (school_id) from JWT token
# Must be added AFTER CORSMiddleware to ensure proper header handling
app.add_middleware(TenancyMiddleware)


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "project": settings.PROJECT_NAME,
    }


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to AI Mentor API",
        "version": settings.VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
    }


# Mount static files for uploads
upload_dir_path = Path(settings.UPLOAD_DIR)
upload_dir_path.mkdir(parents=True, exist_ok=True)
app.mount(f"/{settings.UPLOAD_DIR}", StaticFiles(directory=str(upload_dir_path)), name="uploads")

# Include routers
from app.api.v1 import auth, auth_oauth, admin_global, admin_school, schools, upload, students, goso
from app.api.v1 import paragraph_contents, invitation_codes, rag, chat, teachers, teachers_homework
from app.api.v1 import teachers_exercises
from app.api.v1 import teacher_join_requests

app.include_router(
    auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Authentication"]
)

app.include_router(
    auth_oauth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Authentication - OAuth"]
)

app.include_router(
    schools.router, prefix=f"{settings.API_V1_PREFIX}/admin", tags=["Admin - Schools"]
)

app.include_router(
    admin_global.router,
    prefix=f"{settings.API_V1_PREFIX}/admin/global",
    tags=["Admin - Global Content"],
)

app.include_router(
    admin_school.router,
    prefix=f"{settings.API_V1_PREFIX}/admin/school",
    tags=["Admin - School Content"],
)

app.include_router(
    upload.router,
    prefix=f"{settings.API_V1_PREFIX}/upload",
    tags=["Upload"],
)

app.include_router(
    students.router,
    prefix=f"{settings.API_V1_PREFIX}/students",
    tags=["Students"],
)

app.include_router(
    goso.router,
    prefix=f"{settings.API_V1_PREFIX}/goso",
    tags=["GOSO - Learning Standards"],
)

app.include_router(
    paragraph_contents.router_global,
    prefix=f"{settings.API_V1_PREFIX}/admin/global/paragraphs",
    tags=["Admin - Paragraph Content (Global)"],
)

app.include_router(
    paragraph_contents.router_school,
    prefix=f"{settings.API_V1_PREFIX}/admin/school/paragraphs",
    tags=["Admin - Paragraph Content (School)"],
)

app.include_router(
    invitation_codes.router,
    prefix=f"{settings.API_V1_PREFIX}/admin/school/invitation-codes",
    tags=["Admin - Invitation Codes"],
)

app.include_router(
    rag.router,
    prefix=f"{settings.API_V1_PREFIX}/rag",
    tags=["RAG - Personalized Explanations"],
)

app.include_router(
    chat.router,
    prefix=f"{settings.API_V1_PREFIX}/chat",
    tags=["Chat - RAG Conversations"],
)

app.include_router(
    teachers.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["Teachers - Dashboard & Analytics"],
)

app.include_router(
    teachers_homework.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["Teachers - Homework"],
)

app.include_router(
    teachers_exercises.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["Teachers - Exercises"],
)

app.include_router(
    teacher_join_requests.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["Teachers - Join Requests"],
)
