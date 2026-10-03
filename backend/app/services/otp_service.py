import logging
import secrets
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from app.models.user import User
from app.models.email_otp import EmailOTP
from app.core.security import async_get_password_hash
from app.core.notifications import NotificationService

logger = logging.getLogger("vitalens.otp")
notification_service = NotificationService()

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

async def generate_and_send_email_otp(
    db: AsyncSession,
    email: str,
    purpose: str = "EMAIL_VERIFICATION"
) -> dict:
    """
    Generates a secure 6-digit OTP for email verification or password reset,
    saves it to the database, and dispatches it via email.
    """
    clean_email = email.strip().lower()

    # Verify user exists
    user_q = select(User).where(User.email == clean_email)
    user_res = await db.execute(user_q)
    user = user_res.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this email address."
        )

    if purpose == "EMAIL_VERIFICATION" and user.email_verified:
        return {
            "status": "ALREADY_VERIFIED",
            "message": "Your email address is already verified.",
            "email": clean_email,
            "email_verified": True
        }

    # Invalidate any existing unused OTPs for this email and purpose
    existing_otps_q = select(EmailOTP).where(
        EmailOTP.email == clean_email,
        EmailOTP.purpose == purpose,
        EmailOTP.is_used == False
    )
    existing_res = await db.execute(existing_otps_q)
    for old_otp in existing_res.scalars().all():
        old_otp.is_used = True

    # Generate 6-digit cryptographic OTP
    otp_code = f"{secrets.randbelow(900000) + 100000}"
    expires_at = utc_now() + timedelta(minutes=10)

    otp_record = EmailOTP(
        email=clean_email,
        otp_code=otp_code,
        purpose=purpose,
        attempts=0,
        is_used=False,
        expires_at=expires_at,
        created_at=utc_now()
    )
    db.add(otp_record)
    await db.commit()

    # Formulate email subject, plain text, and HTML template
    clean_name = user.full_name or "Patient"
    if purpose == "PASSWORD_RESET":
        subject = "VitaLens - Password Reset Verification Code"
        action_label = "Password reset code"
        heading = "Reset Your Password"
        description = (
            "We received a request to reset your VitaLens account password. "
            "Please use the 6-digit verification code below to authorize this password change."
        )
    else:
        subject = "VitaLens - Verify Your Email Address"
        action_label = "Profile verification code"
        heading = "Verify Your Account Email"
        description = (
            "Welcome to VitaLens Health! To complete your profile verification and access full AI clinical report comprehension, "
            "please enter the 6-digit verification code below."
        )

    text_body = (
        f"Hello {clean_name},\n\n"
        f"{description}\n\n"
        f"Your verification code is: {otp_code}\n\n"
        f"This code will expire in 10 minutes.\n\n"
        f"Security Notice: If you did not request this, please disregard this email. Never share your OTP.\n\n"
        f"Best regards,\nVitaLens Health Team"
    )

    html_body = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{subject}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b;">
  <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f8fafc; padding: 32px 12px;">
    <tr>
      <td align="center">
        <table width="100%" max-width="540" border="0" cellspacing="0" cellpadding="0" style="max-width: 540px; background-color: #ffffff; border-radius: 18px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 14px rgba(15, 92, 94, 0.06);">
          <!-- Header Banner -->
          <tr>
            <td style="background-color: #0F5C5E; padding: 26px 30px; text-align: center;">
              <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 800; letter-spacing: -0.4px;">VitaLens Health</h1>
              <p style="margin: 4px 0 0 0; color: #99F6E4; font-size: 13px; font-weight: 500;">Clinical Diagnostic Intelligence & Care Platform</p>
            </td>
          </tr>
          <!-- Body Content -->
          <tr>
            <td style="padding: 32px 28px;">
              <h2 style="margin: 0 0 14px 0; color: #0f172a; font-size: 20px; font-weight: 800;">{heading}</h2>
              <p style="margin: 0 0 14px 0; font-size: 15px; line-height: 24px; color: #334155;">Hello <strong>{clean_name}</strong>,</p>
              <p style="margin: 0 0 20px 0; font-size: 15px; line-height: 24px; color: #334155;">{description}</p>
              
              <!-- OTP Display Box -->
              <div style="background-color: #f0fdfa; border: 2px dashed #0F5C5E; border-radius: 14px; padding: 22px 16px; text-align: center; margin: 24px 0;">
                <div style="font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 1.5px; color: #0F5C5E; margin-bottom: 8px;">6-Digit Verification Code</div>
                <div style="font-size: 38px; font-weight: 900; letter-spacing: 10px; color: #0F5C5E; font-family: 'Courier New', Courier, monospace; margin-left: 10px;">{otp_code}</div>
                <div style="font-size: 12px; color: #64748b; margin-top: 10px; font-weight: 500;">Valid for <strong>10 minutes</strong> only</div>
              </div>

              <!-- Security Callout -->
              <div style="background-color: #fef2f2; border-left: 4px solid #ef4444; border-radius: 6px; padding: 12px 14px; margin: 22px 0;">
                <p style="margin: 0; font-size: 12.5px; color: #991b1b; line-height: 18px;">
                  <strong>Security Advisory:</strong> If you did not initiate this request, no action is needed. VitaLens will never ask for your verification code by phone, chat, or email.
                </p>
              </div>

              <p style="margin: 22px 0 0 0; font-size: 14px; color: #64748b; line-height: 20px;">
                Warm regards,<br>
                <strong style="color: #0F5C5E;">VitaLens Patient Safety & Security</strong>
              </p>
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="background-color: #f8fafc; border-top: 1px solid #f1f5f9; padding: 18px 28px; text-align: center;">
              <p style="margin: 0; font-size: 12px; color: #94a3b8; line-height: 18px;">
                © 2026 VitaLens Healthcare Technologies. All rights reserved.<br>
                HIPAA & DPDP Compliant Secure Healthcare Network.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    # Dispatch email (HTML + Plaintext) via active Notification Provider
    try:
        await notification_service.provider.send_email(
            to_email=clean_email,
            subject=subject,
            body=text_body,
            html_content=html_body
        )
    except Exception as e:
        logger.error(f"Failed to dispatch email to {clean_email}: {e}")

    logger.info(f"[EMAIL OTP DISPATCHED] To: {clean_email} | Purpose: {purpose} | OTP: {otp_code}")

    return {
        "status": "SUCCESS",
        "message": f"{action_label} sent to {clean_email}.",
        "email": clean_email,
        "expires_in_minutes": 10,
        "dev_otp": otp_code  # Retained for development inspection
    }

async def verify_email_otp(
    db: AsyncSession,
    email: str,
    otp: str,
    purpose: str = "EMAIL_VERIFICATION"
) -> bool:
    """
    Validates a submitted OTP against active records in the database.
    If purpose is EMAIL_VERIFICATION, marks user as email_verified and is_verified.
    """
    clean_email = email.strip().lower()
    submitted_otp = otp.strip()

    now = utc_now()

    # Fetch active OTP record
    q = (
        select(EmailOTP)
        .where(
            EmailOTP.email == clean_email,
            EmailOTP.purpose == purpose,
            EmailOTP.is_used == False
        )
        .order_by(EmailOTP.created_at.desc())
    )
    res = await db.execute(q)
    otp_record = res.scalars().first()

    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active OTP found. Please request a new verification code."
        )

    if otp_record.expires_at < now:
        otp_record.is_used = True
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The verification code has expired. Please request a new one."
        )

    if otp_record.attempts >= 5:
        otp_record.is_used = True
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many invalid attempts. This OTP has been invalidated. Please request a new code."
        )

    if otp_record.otp_code != submitted_otp:
        otp_record.attempts += 1
        await db.commit()
        remaining = 5 - otp_record.attempts
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid verification code. {remaining} attempt(s) remaining."
        )

    # Valid OTP: mark as used
    otp_record.is_used = True

    # If email verification, activate user's verified status
    if purpose == "EMAIL_VERIFICATION":
        user_q = select(User).where(User.email == clean_email)
        user_res = await db.execute(user_q)
        user = user_res.scalars().first()
        if user:
            user.email_verified = True
            user.is_verified = True
            user.verified_at = now
            user.updated_at = now

    await db.commit()
    return True

async def reset_password_with_otp(
    db: AsyncSession,
    email: str,
    otp: str,
    new_password: str
) -> bool:
    """
    Verifies the PASSWORD_RESET OTP and updates the user's password.
    """
    clean_email = email.strip().lower()

    if len(new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 6 characters long."
        )

    # 1. Verify OTP
    await verify_email_otp(db, clean_email, otp, purpose="PASSWORD_RESET")

    # 2. Find and update user
    user_q = select(User).where(User.email == clean_email)
    user_res = await db.execute(user_q)
    user = user_res.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account not found."
        )

    user.hashed_password = await async_get_password_hash(new_password)
    user.updated_at = utc_now()
    await db.commit()

    logger.info(f"[PASSWORD RESET SUCCESS] User {clean_email} successfully reset their password via OTP.")
    return True
