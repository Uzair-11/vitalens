from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.schemas.appointment_schema import (
    AppointmentCreate, AppointmentResponse, AppointmentCancelRequest, AppointmentRescheduleRequest
)
from app.services.appointment_service import (
    book_appointment, list_user_appointments, cancel_appointment, reschedule_appointment
)

router = APIRouter()

@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@router.post("/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    appt_in: AppointmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Books an appointment slot with a doctor."""
    return await book_appointment(db, current_user.id, appt_in)

@router.get("", response_model=List[AppointmentResponse], include_in_schema=False)
@router.get("/", response_model=List[AppointmentResponse])

async def get_appointments(
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lists user appointments (filtered optionally by upcoming, completed, or cancelled)."""
    return await list_user_appointments(db, current_user.id, status_filter)

@router.patch("/{appointment_id}/cancel", response_model=AppointmentResponse)
async def cancel_user_appointment(
    appointment_id: str,
    cancel_in: AppointmentCancelRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancels a scheduled appointment."""
    return await cancel_appointment(db, current_user.id, appointment_id, cancel_in.cancellation_reason)

@router.patch("/{appointment_id}/reschedule", response_model=AppointmentResponse)
async def reschedule_user_appointment(
    appointment_id: str,
    reschedule_in: AppointmentRescheduleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reschedules an appointment to a new date and time slot."""
    return await reschedule_appointment(db, current_user.id, appointment_id, reschedule_in.new_date, reschedule_in.new_time)
