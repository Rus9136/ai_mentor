"""
Main FastAPI application.
"""

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

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

    # Start scheduler for periodic tasks (weekly tournaments)
    from app.core.scheduler import setup_scheduler, shutdown_scheduler
    setup_scheduler()

    yield

    # Shutdown
    print("Shutting down AI Mentor API...")
    shutdown_scheduler()
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


@app.get("/health/ready", tags=["health"])
async def health_ready():
    """Deep health check — verifies all dependencies."""
    import time
    import shutil
    from app.core.database import AsyncSessionLocal
    from sqlalchemy import text as sa_text

    checks = {}
    overall = "healthy"

    # 1. Database check
    try:
        t0 = time.monotonic()
        async with AsyncSessionLocal() as session:
            result = await session.execute(sa_text("SELECT 1"))
            result.scalar()
        latency = round((time.monotonic() - t0) * 1000, 1)
        checks["database"] = {"status": "up", "latency_ms": latency}
    except Exception as e:
        checks["database"] = {"status": "down", "error": str(e)[:200]}
        overall = "unhealthy"

    # 2. Database pool stats
    try:
        pool = engine.pool  # type: ignore[union-attr]
        checks["db_pool"] = {
            "status": "up",
            "size": getattr(pool, "size", lambda: "?")(),
            "checked_in": getattr(pool, "checkedin", lambda: "?")(),
            "checked_out": getattr(pool, "checkedout", lambda: "?")(),
            "overflow": getattr(pool, "overflow", lambda: "?")(),
        }
    except Exception:
        checks["db_pool"] = {"status": "unknown"}

    # 3. Disk space
    try:
        usage = shutil.disk_usage("/")
        free_gb = round(usage.free / (1024 ** 3), 1)
        total_gb = round(usage.total / (1024 ** 3), 1)
        used_pct = round((usage.used / usage.total) * 100, 1)
        disk_status = "warning" if used_pct > 85 else "ok"
        if used_pct > 95:
            disk_status = "critical"
            overall = "unhealthy"
        checks["disk"] = {
            "status": disk_status,
            "free_gb": free_gb,
            "total_gb": total_gb,
            "used_pct": used_pct,
        }
    except Exception as e:
        checks["disk"] = {"status": "unknown", "error": str(e)[:200]}

    # 4. LLM provider (config check, no API call)
    provider = settings.LLM_PROVIDER
    api_key_set = False
    if provider == "dashscope":
        api_key_set = bool(settings.DASHSCOPE_API_KEY)
    elif provider == "cerebras":
        api_key_set = bool(settings.CEREBRAS_API_KEY)
    elif provider == "openrouter":
        api_key_set = bool(settings.OPENROUTER_API_KEY)
    elif provider == "openai":
        api_key_set = bool(settings.OPENAI_API_KEY)
    checks["llm"] = {
        "status": "configured" if api_key_set else "no_api_key",
        "provider": provider,
    }
    if not api_key_set:
        overall = "degraded"

    # 5. Uploads directory
    uploads_path = Path(settings.UPLOAD_DIR)
    checks["uploads"] = {
        "status": "ok" if uploads_path.exists() and uploads_path.is_dir() else "missing",
    }

    status_code = 200 if overall == "healthy" else (200 if overall == "degraded" else 503)
    return JSONResponse(
        status_code=status_code,
        content={
            "status": overall,
            "version": settings.VERSION,
            "checks": checks,
        },
    )


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
from app.api.v1 import teachers_exercises, teachers_grades, teachers_lesson_plans
from app.api.v1 import teacher_join_requests
from app.api.v1 import teacher_chat
from app.api.v1 import teachers_usage
from app.api.v1 import teachers_gamification
from app.api.v1 import app_version
from app.api.v1 import shared_files, file_browser
from app.api.v1 import teachers_quiz, students_quiz, ws_quiz
from app.api.v1 import teachers_quiz_analytics
from app.api.v1 import teachers_quiz_reports
from app.api.v1 import teachers_tests
from app.api.v1 import teachers_presentations
from app.api.v1 import auth_phone
from app.api.v1 import auth_teacher

app.include_router(
    auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Authentication"]
)

app.include_router(
    auth_oauth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Authentication - OAuth"]
)

app.include_router(
    auth_phone.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Authentication - Phone"]
)

app.include_router(
    auth_teacher.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Authentication - Teacher"]
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
    teachers_grades.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["Teachers - Grades"],
)

app.include_router(
    teachers_lesson_plans.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["Teachers - Lesson Plans"],
)

app.include_router(
    teachers_presentations.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["Teachers - Presentations"],
)

app.include_router(
    teacher_join_requests.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["Teachers - Join Requests"],
)

app.include_router(
    teacher_chat.router,
    prefix=f"{settings.API_V1_PREFIX}/teachers/chat",
    tags=["Teachers - AI Chat"],
)

app.include_router(
    teachers_usage.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["Teachers - Usage"],
)

app.include_router(
    teachers_gamification.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["Teachers - Gamification"],
)

app.include_router(
    app_version.router,
    prefix="/api",
    tags=["App Version"],
)

app.include_router(
    shared_files.router,
    prefix=f"{settings.API_V1_PREFIX}/shared-files",
    tags=["Shared Files"],
)

app.include_router(
    file_browser.router,
    prefix="/files",
    tags=["File Browser"],
)

app.include_router(
    teachers_quiz.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["Teachers - Quiz Battle"],
)

app.include_router(
    teachers_quiz_analytics.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["Teachers - Quiz Analytics"],
)

app.include_router(
    teachers_quiz_reports.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["Teachers - Quiz Reports"],
)

app.include_router(
    teachers_tests.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["Teachers - Tests"],
)

app.include_router(
    students_quiz.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["Students - Quiz Battle"],
)

app.include_router(
    ws_quiz.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["Quiz Battle - WebSocket"],
)
