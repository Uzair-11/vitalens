import os
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.consent import Consent
from app.models.user import User
from app.models.notification_log import NotificationLog

logger = logging.getLogger("vitalens.notifications")

class NotificationProvider(ABC):
    @abstractmethod
    async def send_email(self, to_email: str, subject: str, body: str) -> bool:
        pass

    @abstractmethod
    async def send_push(self, push_token: str, title: str, body: str, data: Optional[Dict[str, Any]] = None) -> bool:
        pass

class SandboxNotificationProvider(NotificationProvider):
    """
    Sandbox / Development notification provider.
    Logs email and push dispatches to structured logs and records them in the database.
    """
    async def send_email(self, to_email: str, subject: str, body: str) -> bool:
        logger.info(f"[SANDBOX EMAIL DISPATCHED] To: {to_email} | Subject: '{subject}' | Body Preview: {body[:80]}...")
        return True

    async def send_push(self, push_token: str, title: str, body: str, data: Optional[Dict[str, Any]] = None) -> bool:
        # Stubbed Expo push provider blueprint
        logger.info(f"[SANDBOX PUSH DISPATCHED] Token: {push_token} | Title: '{title}' | Body: '{body}'")
        return True

class ExpoPushNotificationProvider(NotificationProvider):
    """
    STUB / BLUEPRINT: Expo Push Notification Service.
    Requires Expo push access token or project credentials for production push delivery.
    """
    def __init__(self, expo_access_token: Optional[str] = None):
        self.expo_access_token = expo_access_token or os.getenv("EXPO_ACCESS_TOKEN")
        self.is_configured = bool(self.expo_access_token)

    async def send_email(self, to_email: str, subject: str, body: str) -> bool:
        return True

    async def send_push(self, push_token: str, title: str, body: str, data: Optional[Dict[str, Any]] = None) -> bool:
        if not self.is_configured:
            logger.warning("ExpoPushNotificationProvider: Missing EXPO_ACCESS_TOKEN. Push not dispatched.")
            return False
        # Production httpx request to https://exp.host/--/api/v2/push/send blueprint:
        # payload = {"to": push_token, "title": title, "body": body, "data": data or {}}
        return True

class NotificationService:
    def __init__(self, provider: Optional[NotificationProvider] = None):
        self.provider = provider or SandboxNotificationProvider()

    async def check_notification_consent(self, db: AsyncSession, user_id: str) -> bool:
        """
        DPDP/Consent Gate: Checks if the user has an active, granted NOTIFICATIONS consent record.
        """
        query = select(Consent).where(
            Consent.user_id == user_id,
            Consent.consent_type == "NOTIFICATIONS",
            Consent.granted == True
        )
        result = await db.execute(query)
        consent = result.scalars().first()
        return bool(consent)

    async def dispatch(
        self,
        db: AsyncSession,
        user_id: str,
        recipient_email: str,
        event_type: str,
        subject: str,
        body: str,
        notification_type: str = "EMAIL"
    ) -> NotificationLog:
        """
        Dispatches a notification gated by user consent and creates an audit log in notification_logs.
        """
        has_consent = await self.check_notification_consent(db, user_id)

        if not has_consent:
            log_entry = NotificationLog(
                user_id=user_id,
                recipient=recipient_email,
                notification_type=notification_type,
                event_type=event_type,
                subject=subject,
                body=body,
                status="SKIPPED_NO_CONSENT",
                error_message="User has not granted NOTIFICATIONS consent."
            )
            db.add(log_entry)
            await db.commit()
            logger.info(f"Notification skipped for user {user_id} (event: {event_type}): No active NOTIFICATIONS consent.")
            return log_entry

        try:
            success = await self.provider.send_email(recipient_email, subject, body)
            status = "SENT" if success else "FAILED"
            err = None if success else "Provider returned failure status"
        except Exception as e:
            status = "FAILED"
            err = str(e)

        log_entry = NotificationLog(
            user_id=user_id,
            recipient=recipient_email,
            notification_type=notification_type,
            event_type=event_type,
            subject=subject,
            body=body,
            status=status,
            error_message=err
        )
        db.add(log_entry)
        await db.commit()
        return log_entry

    async def notify_appointment_confirmed(self, db: AsyncSession, appointment, user: User, doctor_name: str):
        subject = f"Appointment Confirmed with Dr. {doctor_name}"
        body = (
            f"Dear {user.full_name or 'Patient'},\n\n"
            f"Your appointment with Dr. {doctor_name} has been confirmed for "
            f"{appointment.appointment_date} at {appointment.appointment_time}.\n\n"
            f"Thank you for choosing VitaLens Health."
        )
        return await self.dispatch(
            db=db,
            user_id=user.id,
            recipient_email=user.email,
            event_type="APPOINTMENT_CONFIRMED",
            subject=subject,
            body=body
        )

    async def notify_appointment_cancelled(self, db: AsyncSession, appointment, user: User, doctor_name: str, reason: Optional[str] = None):
        subject = f"Appointment Cancelled with Dr. {doctor_name}"
        body = (
            f"Dear {user.full_name or 'Patient'},\n\n"
            f"Your appointment with Dr. {doctor_name} on {appointment.appointment_date} "
            f"at {appointment.appointment_time} has been cancelled.\n"
            f"Reason: {reason or 'Cancelled by user/system'}.\n\n"
            f"If this was unexpected, please reschedule via the VitaLens app."
        )
        return await self.dispatch(
            db=db,
            user_id=user.id,
            recipient_email=user.email,
            event_type="APPOINTMENT_CANCELLED",
            subject=subject,
            body=body
        )

    async def notify_report_analyzed(self, db: AsyncSession, user: User, report_filename: str):
        subject = "Your Medical Lab Report Analysis is Ready"
        body = (
            f"Dear {user.full_name or 'Patient'},\n\n"
            f"Your medical report '{report_filename}' has been analyzed by VitaLens AI. "
            f"Your biomarker extractions and plain-language summary are now available in your health portal."
        )
        return await self.dispatch(
            db=db,
            user_id=user.id,
            recipient_email=user.email,
            event_type="REPORT_ANALYSIS_COMPLETE",
            subject=subject,
            body=body
        )

notification_service = NotificationService()
