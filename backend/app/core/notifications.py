import os
import ssl
import smtplib
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.config import settings
from app.models.consent import Consent
from app.models.user import User
from app.models.notification_log import NotificationLog

logger = logging.getLogger("vitalens.notifications")

class NotificationProvider(ABC):
    @abstractmethod
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_content: Optional[str] = None
    ) -> bool:
        pass

    @abstractmethod
    async def send_push(
        self,
        push_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        pass


class SandboxNotificationProvider(NotificationProvider):
    """
    Sandbox / Development notification provider.
    Logs email and push dispatches to structured logs.
    """
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_content: Optional[str] = None
    ) -> bool:
        logger.info(
            f"[SANDBOX EMAIL DISPATCHED] To: {to_email} | Subject: '{subject}' | Body Preview: {body[:100]}..."
        )
        return True

    async def send_push(
        self,
        push_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        logger.info(f"[SANDBOX PUSH DISPATCHED] Token: {push_token} | Title: '{title}' | Body: '{body}'")
        return True


class SMTPNotificationProvider(NotificationProvider):
    """
    Production-grade live SMTP email provider.
    Supports STARTTLS (port 587) and SSL (port 465) for Gmail, Outlook, Brevo, SendGrid, Mailgun, and AWS SES.
    Dispatches dual-format (HTML + Plaintext) emails using asynchronous background threading.
    """
    def __init__(self):
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL or settings.SMTP_USER or "noreply@vitalens.com"
        self.from_name = settings.SMTP_FROM_NAME or "VitaLens Health"
        self.use_tls = settings.SMTP_USE_TLS
        self.use_ssl = settings.SMTP_USE_SSL

    def _send_sync(
        self,
        to_email: str,
        subject: str,
        text_content: str,
        html_content: Optional[str] = None
    ) -> bool:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.from_name} <{self.from_email}>"
        msg["To"] = to_email

        # 1. Plain-text version
        part1 = MIMEText(text_content, "plain", "utf-8")
        msg.attach(part1)

        # 2. Rich HTML version
        if html_content:
            part2 = MIMEText(html_content, "html", "utf-8")
            msg.attach(part2)

        context = ssl.create_default_context()

        if self.use_ssl:
            with smtplib.SMTP_SSL(self.host, self.port, context=context, timeout=20) as server:
                if self.user and self.password:
                    server.login(self.user, self.password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(self.host, self.port, timeout=20) as server:
                if self.use_tls:
                    server.starttls(context=context)
                if self.user and self.password:
                    server.login(self.user, self.password)
                server.send_message(msg)

        logger.info(f"[LIVE SMTP EMAIL SENT] Successfully delivered email to {to_email} via {self.host}:{self.port}")
        return True

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_content: Optional[str] = None
    ) -> bool:
        if not self.host or not self.user or not self.password:
            logger.warning(
                f"[SMTP SKIPPED] Missing SMTP configuration (Host: {self.host}, User: {self.user}). "
                f"Falling back to sandbox log for {to_email}."
            )
            logger.info(f"[SANDBOX EMAIL DISPATCHED] To: {to_email} | Subject: '{subject}' | Body: {body[:100]}...")
            return True

        try:
            return await asyncio.to_thread(self._send_sync, to_email, subject, body, html_content)
        except Exception as e:
            logger.error(f"[LIVE SMTP ERROR] Failed to send email to {to_email} via {self.host}:{self.port} - {e}")
            raise e

    async def send_push(
        self,
        push_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        logger.info(f"[PUSH NOTIFICATION STUB] Token: {push_token} | Title: {title}")
        return True


def create_notification_provider() -> NotificationProvider:
    if settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD:
        logger.info(f"[NOTIFICATIONS] Initialized Live SMTP Provider using {settings.SMTP_HOST}:{settings.SMTP_PORT}")
        return SMTPNotificationProvider()
    else:
        logger.info("[NOTIFICATIONS] Initialized Sandbox Provider (Configure SMTP_HOST, SMTP_USER, SMTP_PASSWORD in .env for live inbox dispatch)")
        return SandboxNotificationProvider()


class NotificationService:
    def __init__(self, provider: Optional[NotificationProvider] = None):
        self.provider = provider or create_notification_provider()

    def reload_provider(self):
        """Reloads provider dynamically when settings/env change."""
        self.provider = create_notification_provider()

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
        html_content: Optional[str] = None,
        notification_type: str = "EMAIL"
    ) -> NotificationLog:
        """
        Dispatches a notification gated by user consent and records an audit log.
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
            success = await self.provider.send_email(recipient_email, subject, body, html_content=html_content)
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
        subject = f"Appointment Confirmed with Dr. {doctor_name} - VitaLens"
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
        subject = f"Appointment Cancelled with Dr. {doctor_name} - VitaLens"
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
        subject = "Your Medical Lab Report Analysis is Ready - VitaLens"
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
