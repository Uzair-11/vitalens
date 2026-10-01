from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.rbac import get_current_user_obj
from app.core.audit import record_audit_log
from app.core.payment import payment_gateway
from app.core.notifications import notification_service
from app.models.user import User
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.schemas.payment_schema import (
    PaymentInitiateResponse, PaymentVerifyRequest, PaymentVerifyResponse
)

router = APIRouter()

@router.post("/{appointment_id}/payment/initiate", response_model=PaymentInitiateResponse)
async def initiate_appointment_payment(
    appointment_id: str,
    current_user: User = Depends(get_current_user_obj),
    db: AsyncSession = Depends(get_db)
):
    """
    Creates a Razorpay sandbox payment order for the appointment consultation fee.
    """
    query = select(Appointment).where(Appointment.id == appointment_id).options(
        selectinload(Appointment.doctor)
    )
    result = await db.execute(query)
    appointment = result.scalars().first()

    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.")

    if appointment.user_id != current_user.id and current_user.role not in ["ADMIN", "SUPER_ADMIN"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to initiate payment for this appointment.")

    if appointment.payment_status == "PAID":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This appointment is already paid.")

    doctor = appointment.doctor
    fee_inr = float(doctor.consultation_fee) if doctor and doctor.consultation_fee else 800.0
    doctor_name = doctor.full_name if doctor else "Doctor"

    receipt_id = f"rcpt_{appointment.id[:8]}"
    order = await payment_gateway.create_order(
        amount_inr=fee_inr,
        receipt=receipt_id,
        notes={"appointment_id": appointment.id, "user_id": current_user.id}
    )

    appointment.payment_order_id = order["order_id"]
    appointment.payment_amount = str(fee_inr)
    appointment.payment_status = "PENDING"
    await db.commit()

    await record_audit_log(
        db,
        action="PAYMENT_INITIATED",
        resource_type="Appointment",
        resource_id=appointment.id,
        actor_user_id=current_user.id,
        metadata={"order_id": order["order_id"], "amount": fee_inr}
    )

    return {
        "appointment_id": appointment.id,
        "order_id": order["order_id"],
        "amount_paise": order["amount"],
        "amount_inr": fee_inr,
        "currency": "INR",
        "key_id": order["key_id"],
        "doctor_name": doctor_name,
        "doctor_fee": fee_inr,
        "notes": order.get("notes", {})
    }

@router.post("/{appointment_id}/payment/verify", response_model=PaymentVerifyResponse)
async def verify_appointment_payment(
    appointment_id: str,
    payload: PaymentVerifyRequest,
    current_user: User = Depends(get_current_user_obj),
    db: AsyncSession = Depends(get_db)
):
    """
    Performs server-side HMAC-SHA256 signature verification of the Razorpay callback.
    Transitions appointment to CONFIRMED and payment_status to PAID upon valid verification.
    """
    query = select(Appointment).where(Appointment.id == appointment_id).options(
        selectinload(Appointment.doctor),
        selectinload(Appointment.user)
    )
    result = await db.execute(query)
    appointment = result.scalars().first()

    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.")

    if appointment.user_id != current_user.id and current_user.role not in ["ADMIN", "SUPER_ADMIN"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to verify payment for this appointment.")

    if appointment.payment_order_id and appointment.payment_order_id != payload.razorpay_order_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order ID mismatch.")

    # Cryptographic HMAC-SHA256 verification
    is_valid = payment_gateway.verify_payment_signature(
        order_id=payload.razorpay_order_id,
        payment_id=payload.razorpay_payment_id,
        signature=payload.razorpay_signature
    )

    if not is_valid:
        appointment.payment_status = "FAILED"
        await db.commit()
        await record_audit_log(
            db,
            action="PAYMENT_FAILED",
            resource_type="Appointment",
            resource_id=appointment.id,
            actor_user_id=current_user.id,
            metadata={
                "order_id": payload.razorpay_order_id,
                "payment_id": payload.razorpay_payment_id,
                "reason": "Invalid or tampered HMAC signature"
            }
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment verification failed: invalid or tampered payment signature."
        )

    # Success path
    appointment.payment_status = "PAID"
    appointment.payment_id = payload.razorpay_payment_id
    appointment.status = "CONFIRMED"
    await db.commit()

    await record_audit_log(
        db,
        action="PAYMENT_SUCCESS",
        resource_type="Appointment",
        resource_id=appointment.id,
        actor_user_id=current_user.id,
        metadata={
            "order_id": payload.razorpay_order_id,
            "payment_id": payload.razorpay_payment_id,
            "amount": appointment.payment_amount
        }
    )

    # Trigger appointment confirmed notification (consent-gated)
    doctor_name = appointment.doctor.full_name if appointment.doctor else "Doctor"
    await notification_service.notify_appointment_confirmed(
        db=db,
        appointment=appointment,
        user=current_user,
        doctor_name=doctor_name
    )

    return {
        "status": "PAID",
        "appointment_id": appointment.id,
        "payment_id": payload.razorpay_payment_id,
        "appointment_status": appointment.status,
        "message": "Payment verified and appointment successfully confirmed."
    }
