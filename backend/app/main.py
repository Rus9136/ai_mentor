"""
Main FastAPI application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine


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


# Include routers
from app.api.v1 import auth, admin_global, admin_school, schools

app.include_router(
    auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Authentication"]
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
