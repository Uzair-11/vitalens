from datetime import datetime, timezone
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.rbac import get_current_user_obj
from app.core.audit import record_audit_log
from app.core.storage import storage_adapter, get_public_file_url
from app.models.user import User
from app.models.consent import Consent
from app.models.report import MedicalReport
from app.models.appointment import Appointment
from app.models.symptom_log import SymptomLog
from app.schemas.user_schema import (
    UserRegister, UserLogin, PasswordResetRequest, TokenResponse, UserProfileResponse, UserProfileUpdate,
    RefreshTokenRequest, RefreshTokenResponse
)
from app.services.user_service import (
    register_user, authenticate_user, refresh_user_token, revoke_user_refresh_token,
    get_user_profile, update_user_profile, reset_user_password
)

router = APIRouter()

# Dependency compatibility alias
get_current_user = get_current_user_obj

@router.post("/register", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserRegister, db: AsyncSession = Depends(get_db)):
    """Registers a new PATIENT user account."""
    user = await register_user(db, user_in)
    await record_audit_log(db, action="USER_REGISTER", resource_type="User", resource_id=user.id, actor_user_id=user.id)
    return user

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """Standard JSON-based login endpoint."""
    res = await authenticate_user(db, credentials.email, credentials.password)
    await record_audit_log(db, action="USER_LOGIN", resource_type="User", resource_id=res["user_id"], actor_user_id=res["user_id"])
    return res

@router.post("/login-json", response_model=TokenResponse)
async def login_json(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """JSON-based login endpoint for mobile and web clients."""
    res = await authenticate_user(db, credentials.email, credentials.password)
    await record_audit_log(db, action="USER_LOGIN", resource_type="User", resource_id=res["user_id"], actor_user_id=res["user_id"])
    return res

@router.post("/token", response_model=TokenResponse)
async def login_oauth(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """OAuth2 Swagger docs compatible token endpoint."""
    return await authenticate_user(db, form_data.username, form_data.password)

@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(token_in: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Exchanges an unexpired refresh token for a fresh short-lived access token."""
    return await refresh_user_token(db, token_in.refresh_token)

@router.post("/logout")
async def logout(token_in: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Revokes the user's refresh token in the database."""
    revoked = await revoke_user_refresh_token(db, token_in.refresh_token)
    return {"status": "SUCCESS", "message": "Logged out and refresh token revoked successfully.", "revoked": revoked}

@router.post("/reset-password")
async def reset_password(req: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    """Allows resetting password for an existing registered account."""
    await reset_user_password(db, req.email, req.new_password)
    return {"status": "SUCCESS", "message": "Password updated successfully. You can now log in."}

@router.get("/me", response_model=UserProfileResponse)
async def read_current_user(current_user: User = Depends(get_current_user)):
    """Get profile of current authenticated user."""
    return current_user

@router.put("/me", response_model=UserProfileResponse)
async def update_current_user(
    update_in: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update profile attributes for current authenticated user."""
    user = await update_user_profile(db, current_user.id, update_in)
    await record_audit_log(db, action="UPDATE_PROFILE", resource_type="User", resource_id=user.id, actor_user_id=user.id)
    return user

@router.post("/avatar", response_model=UserProfileResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Uploads a profile picture avatar (JPEG, PNG, WebP) to Google Cloud Storage or local storage."""
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/jpg"]
    content_type = (file.content_type or "image/jpeg").lower()
    if content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image format. Allowed formats: JPEG, PNG, WebP."
        )

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile picture exceeds maximum allowed size of 5MB."
        )

    ext = "jpg"
    if "png" in content_type:
        ext = "png"
    elif "webp" in content_type:
        ext = "webp"

    timestamp = int(datetime.now(timezone.utc).timestamp())
    unique_filename = f"avatars/{current_user.id}_{timestamp}.{ext}"

    saved_path_or_url = await storage_adapter.save_file(
        file_bytes=content,
        filename=unique_filename,
        content_type=content_type
    )

    public_url = get_public_file_url(saved_path_or_url)
    current_user.avatar_url = public_url

    await db.commit()
    await db.refresh(current_user)
    await record_audit_log(
        db,
        action="UPLOAD_AVATAR",
        resource_type="User",
        resource_id=current_user.id,
        actor_user_id=current_user.id
    )

    return current_user


