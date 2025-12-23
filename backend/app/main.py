"""
Main FastAPI application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path

from app.core.config import settings
from app.core.database import engine
from app.middleware.tenancy import TenancyMiddleware


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

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
from app.api.v1 import paragraph_contents, invitation_codes, rag, chat, teachers

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
