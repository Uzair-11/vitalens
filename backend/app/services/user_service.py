from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.models.consent import Consent
from app.schemas.user_schema import UserRegister, UserProfileUpdate
from app.core.security import (
    get_password_hash, verify_password, async_verify_password, async_get_password_hash,
    create_access_token, create_refresh_token, hash_token, decode_access_token
)
from app.core.config import settings

async def register_user(db: AsyncSession, user_in: UserRegister) -> User:
    """Registers a new PATIENT user account with default privacy consents."""
    # Check existing email
    query = select(User).where(User.email == user_in.email)
    result = await db.execute(query)
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    # Public registration is strictly restricted to PATIENT role
    hashed_pwd = await async_get_password_hash(user_in.password)
    user = User(
        email=user_in.email,
        hashed_password=hashed_pwd,
        role="PATIENT",
        full_name=user_in.full_name,
        phone=user_in.phone,
        date_of_birth=user_in.date_of_birth,
        biological_sex=user_in.biological_sex,
        blood_group=user_in.blood_group,
        emergency_contact=user_in.emergency_contact
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Seed baseline DPDP consents
    for c_type in ["REPORT_ANALYSIS", "AI_PROCESSING", "DOCTOR_DATA_ACCESS", "NOTIFICATIONS", "MARKETING"]:
        consent = Consent(
            user_id=user.id,
            consent_type=c_type,
            granted=True
        )
        db.add(consent)
    await db.commit()

    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> dict:
    """Authenticates user and issues access + refresh tokens."""
    query = select(User).where(User.email == email)
    result = await db.execute(query)
    user = result.scalars().first()

    if not user or not await async_verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password credentials."
        )

    if not getattr(user, "is_active", True) or getattr(user, "is_deleted", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated or suspended."
        )

    # Create access token and refresh token
    token_payload = {"sub": user.id, "email": user.email, "role": user.role}
    access_token = create_access_token(token_payload)
    refresh_token = create_refresh_token(token_payload)

    # Save hashed refresh token in DB
    now = datetime.now(timezone.utc)
    token_rec = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(token_rec)
    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        "user_id": user.id,
        "role": user.role
    }

async def refresh_user_token(db: AsyncSession, refresh_token: str) -> dict:
    """Validates refresh token against database and generates a fresh access token."""
    token_h = hash_token(refresh_token)
    now = datetime.now(timezone.utc)
    
    # Query token
    q = select(RefreshToken).where(
        RefreshToken.token_hash == token_h,
        RefreshToken.revoked_at == None,
        RefreshToken.expires_at > now
    )
    res = await db.execute(q)
    token_rec = res.scalars().first()
    
    if not token_rec:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or revoked refresh token."
        )

    user_q = select(User).where(User.id == token_rec.user_id)
    user_res = await db.execute(user_q)
    user = user_res.scalars().first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive or deleted."
        )

    new_access_token = create_access_token({"sub": user.id, "email": user.email, "role": user.role})
    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "expires_in_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES
    }

async def revoke_user_refresh_token(db: AsyncSession, refresh_token: str) -> bool:
    """Revokes a refresh token on logout."""
    token_h = hash_token(refresh_token)
    q = select(RefreshToken).where(RefreshToken.token_hash == token_h)
    res = await db.execute(q)
    token_rec = res.scalars().first()
    if token_rec:
        token_rec.revoked_at = datetime.now(timezone.utc)
        await db.commit()
        return True
    return False

async def get_user_profile(db: AsyncSession, user_id: str) -> User:
    """Retrieves user profile by ID."""
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user

async def update_user_profile(db: AsyncSession, user_id: str, update_data: UserProfileUpdate) -> User:
    """Updates user profile attributes."""
    user = await get_user_profile(db, user_id)
    
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
        
    await db.commit()
    await db.refresh(user)
    return user

async def reset_user_password(db: AsyncSession, email: str, new_password: str) -> bool:
    """Resets password for the user with matching email address."""
    query = select(User).where(User.email == email.strip().lower())
    result = await db.execute(query)
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this email address."
        )
    user.hashed_password = await async_get_password_hash(new_password)
    await db.commit()
    return True
