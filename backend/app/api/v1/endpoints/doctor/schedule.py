import uuid
from datetime import date, time, timedelta, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from app.core.database import get_db
from app.core.rbac import require_role
from app.models.user import User
from app.models.doctor import Doctor
from app.models.doctor_schedule import DoctorWorkingHours, DoctorScheduleBlock
from app.models.doctor_availability import DoctorAvailability
from app.models.appointment import Appointment
from app.schemas.doctor_portal_schema import (
    DoctorScheduleOverviewResponse, SetWorkingHoursRequest,
    DoctorWorkingHoursResponse, ScheduleBlockCreateRequest, ScheduleBlockResponse
)

router = APIRouter()

async def get_doctor_for_user(db: AsyncSession, user_id: str) -> Doctor:
    """Helper to resolve Doctor record from user_id."""
    doc_q = select(Doctor).where(Doctor.user_id == user_id)
    doc_res = await db.execute(doc_q)
    doctor = doc_res.scalars().first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found for authenticated user."
        )
    return doctor

def parse_time_str(time_str: str) -> time:
    """Parses '09:00' or '09:00:00' into datetime.time."""
    parts = [int(p) for p in time_str.split(":")]
    return time(hour=parts[0], minute=parts[1], second=parts[2] if len(parts) > 2 else 0)

async def sync_doctor_slots_from_working_hours(db: AsyncSession, doctor_id: str, days_ahead: int = 14):
    """
    Synchronizes concrete DoctorAvailability slots based on recurring working hours and active schedule blocks,
    without overwriting or deleting any booked appointments.
    """
    # 1. Fetch active working hours
    wh_q = select(DoctorWorkingHours).where(
        DoctorWorkingHours.doctor_id == doctor_id,
        DoctorWorkingHours.is_active == True
    )
    wh_rows = (await db.execute(wh_q)).scalars().all()
    wh_by_day = {wh.day_of_week: wh for wh in wh_rows}

    # 2. Fetch active schedule blocks
    today = date.today()
    max_date = today + timedelta(days=days_ahead)
    blocks_q = select(DoctorScheduleBlock).where(
        DoctorScheduleBlock.doctor_id == doctor_id,
        DoctorScheduleBlock.block_date >= today,
        DoctorScheduleBlock.block_date <= max_date
    )
    blocks = (await db.execute(blocks_q)).scalars().all()
    block_dates = {b.block_date for b in blocks if not b.start_time and not b.end_time}
    partial_blocks = [b for b in blocks if b.start_time and b.end_time]

    # 3. Fetch existing unbooked slots and booked slots
    existing_slots_q = select(DoctorAvailability).where(
        DoctorAvailability.doctor_id == doctor_id,
        DoctorAvailability.available_date >= today,
        DoctorAvailability.available_date <= max_date
    )
    existing_slots = (await db.execute(existing_slots_q)).scalars().all()
    existing_slot_map = {(s.available_date, s.start_time): s for s in existing_slots}

    # 4. Generate slots for each day
    for day_offset in range(1, days_ahead + 1):
        slot_date = today + timedelta(days=day_offset)
        iso_weekday = slot_date.weekday()  # 0=Monday .. 6=Sunday

        # If day is blocked completely, remove unbooked slots
        if slot_date in block_dates:
            for s in list(existing_slot_map.values()):
                if s.available_date == slot_date and not s.is_booked:
                    await db.delete(s)
            continue

        wh = wh_by_day.get(iso_weekday)
        if not wh:
            # Doctor does not work on this day; remove unbooked slots if any
            for (d, t), s in list(existing_slot_map.items()):
                if d == slot_date and not s.is_booked:
                    await db.delete(s)
            continue

        # Iterate in increments of slot_duration_minutes from start_time to end_time
        curr_dt = datetime.combine(slot_date, wh.start_time)
        end_dt = datetime.combine(slot_date, wh.end_time)
        step = timedelta(minutes=wh.slot_duration_minutes)

        while curr_dt + step <= end_dt:
            s_time = curr_dt.time()
            e_time = (curr_dt + step).time()

            # Check if this specific interval is covered by a partial block
            is_blocked = False
            for pb in partial_blocks:
                if pb.block_date == slot_date:
                    if pb.start_time <= s_time < pb.end_time:
                        is_blocked = True
                        break

            key = (slot_date, s_time)
            if is_blocked:
                if key in existing_slot_map and not existing_slot_map[key].is_booked:
                    await db.delete(existing_slot_map[key])
            else:
                if key not in existing_slot_map:
                    new_slot = DoctorAvailability(
                        doctor_id=doctor_id,
                        available_date=slot_date,
                        start_time=s_time,
                        end_time=e_time,
                        slot_duration_minutes=wh.slot_duration_minutes,
                        is_booked=False
                    )
                    db.add(new_slot)

            curr_dt += step

    await db.commit()

@router.get("/schedule", response_model=DoctorScheduleOverviewResponse)
@router.get("/schedule/", response_model=DoctorScheduleOverviewResponse, include_in_schema=False)
async def get_doctor_schedule(
    current_user: User = Depends(require_role("DOCTOR", "SUPER_ADMIN")),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves doctor's recurring weekly working hours, blocks, and active unbooked slot count."""
    doctor = await get_doctor_for_user(db, current_user.id)

    # 1. Fetch recurring hours
    wh_q = select(DoctorWorkingHours).where(DoctorWorkingHours.doctor_id == doctor.id).order_by(DoctorWorkingHours.day_of_week.asc())
    wh_rows = (await db.execute(wh_q)).scalars().all()

    # 2. Fetch future blocks
    today = date.today()
    blocks_q = select(DoctorScheduleBlock).where(
        DoctorScheduleBlock.doctor_id == doctor.id,
        DoctorScheduleBlock.block_date >= today
    ).order_by(DoctorScheduleBlock.block_date.asc())
    blocks = (await db.execute(blocks_q)).scalars().all()

    # 3. Fetch count of active unbooked slots
    slots_q = select(DoctorAvailability).where(
        DoctorAvailability.doctor_id == doctor.id,
        DoctorAvailability.available_date >= today,
        DoctorAvailability.is_booked == False
    )
    unbooked_slots = (await db.execute(slots_q)).scalars().all()

    return DoctorScheduleOverviewResponse(
        doctor_id=doctor.id,
        recurring_hours=wh_rows,
        schedule_blocks=blocks,
        active_available_slots_count=len(unbooked_slots)
    )

@router.post("/schedule", response_model=DoctorScheduleOverviewResponse)
@router.post("/schedule/", response_model=DoctorScheduleOverviewResponse, include_in_schema=False)

async def set_doctor_working_hours(
    wh_in: SetWorkingHoursRequest,
    current_user: User = Depends(require_role("DOCTOR", "SUPER_ADMIN")),
    db: AsyncSession = Depends(get_db)
):
    """Sets/updates doctor's recurring weekly working hours and recalculates available slots."""
    doctor = await get_doctor_for_user(db, current_user.id)

    # 1. Delete existing working hours
    await db.execute(delete(DoctorWorkingHours).where(DoctorWorkingHours.doctor_id == doctor.id))

    # 2. Insert new working hours
    for item in wh_in.working_hours:
        s_time = parse_time_str(item.start_time)
        e_time = parse_time_str(item.end_time)
        wh = DoctorWorkingHours(
            doctor_id=doctor.id,
            day_of_week=item.day_of_week,
            start_time=s_time,
            end_time=e_time,
            slot_duration_minutes=item.slot_duration_minutes,
            is_active=item.is_active
        )
        db.add(wh)
    await db.commit()

    # 3. Synchronize concrete availability slots for upcoming window
    await sync_doctor_slots_from_working_hours(db, doctor.id, days_ahead=14)

    return await get_doctor_schedule(current_user=current_user, db=db)

@router.post("/schedule/block", response_model=ScheduleBlockResponse, status_code=status.HTTP_201_CREATED)
async def add_schedule_block(
    block_in: ScheduleBlockCreateRequest,
    current_user: User = Depends(require_role("DOCTOR", "SUPER_ADMIN")),
    db: AsyncSession = Depends(get_db)
):
    """Adds a one-off blackout date or time block (e.g. vacation, conference, emergency leave)."""
    doctor = await get_doctor_for_user(db, current_user.id)

    s_time = parse_time_str(block_in.start_time) if block_in.start_time else None
    e_time = parse_time_str(block_in.end_time) if block_in.end_time else None

    block = DoctorScheduleBlock(
        doctor_id=doctor.id,
        block_date=block_in.block_date,
        start_time=s_time,
        end_time=e_time,
        reason=block_in.reason
    )
    db.add(block)
    await db.commit()
    await db.refresh(block)

    # Synchronize availability slots to remove blocked slots
    await sync_doctor_slots_from_working_hours(db, doctor.id, days_ahead=14)

    return block

@router.delete("/schedule/block/{block_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_schedule_block(
    block_id: str,
    current_user: User = Depends(require_role("DOCTOR", "SUPER_ADMIN")),
    db: AsyncSession = Depends(get_db)
):
    """Removes a schedule block and re-enables availability."""
    doctor = await get_doctor_for_user(db, current_user.id)

    block_q = select(DoctorScheduleBlock).where(
        DoctorScheduleBlock.id == block_id,
        DoctorScheduleBlock.doctor_id == doctor.id
    )
    block = (await db.execute(block_q)).scalars().first()
    if not block:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule block not found.")

    await db.delete(block)
    await db.commit()

    # Re-sync availability slots
    await sync_doctor_slots_from_working_hours(db, doctor.id, days_ahead=14)
