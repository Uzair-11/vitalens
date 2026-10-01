from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.doctor_schema import SpecialtyResponse, DoctorCardResponse, DoctorDetailResponse, SlotResponse
from app.services.doctor_service import (
    get_all_specialties, search_doctors, get_doctor_detail, get_doctor_availability
)

router = APIRouter()

@router.get("/specialties", response_model=List[SpecialtyResponse])
async def list_specialties(db: AsyncSession = Depends(get_db)):
    """Lists all available medical specialties."""
    return await get_all_specialties(db)

@router.get("", response_model=List[DoctorCardResponse], include_in_schema=False)
@router.get("/", response_model=List[DoctorCardResponse])
async def find_doctors(
    specialty_id: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    max_fee: Optional[float] = Query(None),
    min_rating: Optional[float] = Query(None),
    sort_by: str = Query("rating_desc"),
    db: AsyncSession = Depends(get_db)
):
    """Searches and filters doctors by specialty, location, fee, rating, and experience."""
    return await search_doctors(db, specialty_id, city, max_fee, min_rating, sort_by)

@router.get("/{doctor_id}", response_model=DoctorDetailResponse)
async def get_doctor(doctor_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves full profile details for a specific doctor."""
    return await get_doctor_detail(db, doctor_id)

@router.get("/{doctor_id}/availability", response_model=List[SlotResponse])
async def get_slots(
    doctor_id: str,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves available appointment date and time slots for a doctor."""
    return await get_doctor_availability(db, doctor_id, start_date, end_date)
