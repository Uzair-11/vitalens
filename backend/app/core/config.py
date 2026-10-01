import os
import sys
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Union, Optional
from pydantic import field_validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "VitaLens AI Health Report & Doctor Recommendation API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"  # development / production / testing
    
    # Security & JWT
    SECRET_KEY: str = "dev_secret_key_change_in_production_vitalens_2026_jwt_token_key_9921"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # Database: Default to local credential-less SQLite dev path only.
    # Production environments MUST supply DATABASE_URL via environment variables.
    DATABASE_URL: str = "sqlite+aiosqlite:///./health_app.db"
    TEST_DATABASE_URL: Optional[str] = "postgresql+asyncpg://postgres:admin@localhost:5432/vitalens_test_db"

    # MongoDB Atlas Connection
    MONGODB_URL: Optional[str] = None
    MONGODB_DB_NAME: str = "vitalens_db"

    
    # Uploads & Storage
    UPLOAD_DIR: str = os.path.join(os.getcwd(), "uploads")
    MAX_UPLOAD_SIZE_MB: int = 10
    STORAGE_PROVIDER: str = "local"  # local / s3 / gcs / imagekit
    GCS_BUCKET_NAME: str = "vitalens-health-storage"
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    IMAGEKIT_PRIVATE_KEY: Optional[str] = None
    IMAGEKIT_URL_ENDPOINT: Optional[str] = None
    PUBLIC_BASE_URL: str = "http://localhost:8000"
    
    # CORS (Accepts list or comma-separated string)
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:8081",
        "http://localhost:19006",
        "http://localhost:3000",
        "http://127.0.0.1:8081",
        "http://localhost:8000"
    ]
    

    # Feature Flags
    ENABLE_PAYMENTS: bool = False
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""

    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="allow")

settings = Settings()

# Enforce strict production safeguards
if settings.ENVIRONMENT.lower() == "production":
    if not settings.SECRET_KEY or "dev_secret_key" in settings.SECRET_KEY:
        raise RuntimeError("FATAL: SECRET_KEY must be securely configured when running in production environment!")
    if "sqlite" in settings.DATABASE_URL.lower():
        raise RuntimeError("FATAL: DATABASE_URL must be explicitly configured with a PostgreSQL connection string in production!")

# Ensure uploads directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
