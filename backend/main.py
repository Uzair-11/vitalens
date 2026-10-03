import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import engine, Base, get_db
from app.core.errors import http_exception_handler, validation_exception_handler, unhandled_exception_handler
from app.core.logging_config import setup_structured_logging, RequestIdMiddleware
from app.core.storage import storage_adapter
from app.core.tracker import error_tracker
from app.api.v1.api_router import api_router
from app.data.seed_data import seed_database
from app.core.mongodb import init_mongo, close_mongo, check_mongo_health
import app.models

setup_structured_logging(log_level="INFO")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-reseeding on startup is DISABLED to prevent repopulating wiped/production data.
    # To re-seed baseline demo data manually, run: python -m app.data.seed_data
    # Or uncomment the line below:
    # await seed_database()
    if settings.MONGODB_URL:
        await init_mongo()
    print(f">> {settings.PROJECT_NAME} initialized and ready [Env: {settings.ENVIRONMENT}].")
    yield
    await close_mongo()
    await engine.dispose()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Production-grade API and Applied AI/ML engine for VitaLens AI Health Report & Doctor Recommendation System",
    lifespan=lifespan
)

# Correlation ID Middleware
app.add_middleware(RequestIdMiddleware)

# Exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Configure CORS
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"^https?://.*" if settings.ENVIRONMENT == "development" else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static File Directory for uploaded medical reports
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Mount API V1 router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["System Health"])
async def health_check():
    """Basic liveness health probe."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }

@app.get("/health/ready", tags=["System Health"])
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Multi-subsystem readiness probe (database connectivity + object storage accessibility)."""
    checks = {}
    
    # 1. Database Connectivity Probe
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "connected"
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)}"

    # 2. Storage Adapter Readiness Probe
    try:
        storage_healthy = await storage_adapter.check_ready()
        checks["storage"] = "ready" if storage_healthy else "unreachable"
    except Exception as e:
        checks["storage"] = f"unhealthy: {str(e)}"

    # 3. MongoDB Atlas Probe (if configured)
    if settings.MONGODB_URL and "<PASSWORD>" not in settings.MONGODB_URL:
        mongo_check = await check_mongo_health()
        checks["mongodb"] = mongo_check.get("status", "unknown")

    # Determine overall status
    is_ready = checks.get("database") == "connected" and checks.get("storage") == "ready"
    if not is_ready:
        raise HTTPException(
            status_code=503,
            detail={"status": "not_ready", "checks": checks, "environment": settings.ENVIRONMENT}
        )

    return {
        "status": "ready",
        "checks": checks,
        "environment": settings.ENVIRONMENT
    }

if settings.ENVIRONMENT.lower() != "production":
    @app.get("/debug/trigger-error", tags=["System Diagnostics"], include_in_schema=False)
    async def trigger_test_error():
        """Deliberate unhandled exception trigger for testing error tracking (disabled in production)."""
        raise RuntimeError("Deliberate test exception for verifying VitaLens error tracking and request correlation.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
