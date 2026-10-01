from typing import List, Optional
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from app.models.doctor import Doctor
from app.models.specialty import MedicalSpecialty
from app.models.doctor_availability import DoctorAvailability

async def get_all_specialties(db: AsyncSession) -> List[MedicalSpecialty]:
    query = select(MedicalSpecialty).order_by(MedicalSpecialty.name.asc())
    result = await db.execute(query)
    return result.scalars().all()

async def search_doctors(
    db: AsyncSession,
    specialty_id: Optional[str] = None,
    city: Optional[str] = None,
    max_fee: Optional[float] = None,
    min_rating: Optional[float] = None,
    sort_by: str = "rating_desc"
) -> List[dict]:
    query = select(Doctor).options(selectinload(Doctor.specialty))
    
    if specialty_id:
        query = query.where(Doctor.specialty_id == specialty_id)
    if city:
        query = query.where(Doctor.city.ilike(f"%{city}%"))
    if max_fee:
        query = query.where(Doctor.consultation_fee <= max_fee)
    if min_rating:
        query = query.where(Doctor.rating >= min_rating)
        
    if sort_by == "fee_asc":
        query = query.order_by(Doctor.consultation_fee.asc())
    elif sort_by == "experience_desc":
        query = query.order_by(Doctor.experience_years.desc())
    else:  # rating_desc
        query = query.order_by(Doctor.rating.desc())
        
    result = await db.execute(query)
    doctors = result.scalars().all()
    
    response = []
    for doc in doctors:
        response.append({
            "id": doc.id,
            "specialty_id": doc.specialty_id,
            "specialty_name": doc.specialty.name if doc.specialty else "General",
            "full_name": doc.full_name,
            "qualification": doc.qualification,
            "experience_years": doc.experience_years,
            "clinic_name": doc.clinic_name,
            "address": doc.address,
            "city": doc.city,
            "consultation_fee": float(doc.consultation_fee),
            "rating": doc.rating,
            "review_count": doc.review_count,
            "profile_photo_url": doc.profile_photo_url,
            "languages": doc.languages or ["English"]
        })
    return response

async def get_doctor_detail(db: AsyncSession, doctor_id: str) -> dict:
    query = select(Doctor).where(Doctor.id == doctor_id).options(
        selectinload(Doctor.specialty),
        selectinload(Doctor.availability_slots)
    )
    result = await db.execute(query)
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found.")
        
    unbooked_slots = [s for s in doc.availability_slots if not s.is_booked and s.available_date >= date.today()]
    next_slot = f"{unbooked_slots[0].available_date} at {unbooked_slots[0].start_time.strftime('%I:%M %p')}" if unbooked_slots else "Contact Clinic"
    
    return {
        "id": doc.id,
        "specialty_id": doc.specialty_id,
        "specialty_name": doc.specialty.name if doc.specialty else "General",
        "full_name": doc.full_name,
        "qualification": doc.qualification,
        "experience_years": doc.experience_years,
        "clinic_name": doc.clinic_name,
        "address": doc.address,
        "city": doc.city,
        "consultation_fee": float(doc.consultation_fee),
        "rating": doc.rating,
        "review_count": doc.review_count,
        "profile_photo_url": doc.profile_photo_url,
        "languages": doc.languages or ["English"],
        "bio": doc.bio,
        "available_slots_count": len(unbooked_slots),
        "next_available_slot": next_slot
    }

async def get_doctor_availability(
    db: AsyncSession,
    doctor_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[DoctorAvailability]:
    query = select(DoctorAvailability).where(
        DoctorAvailability.doctor_id == doctor_id,
        DoctorAvailability.is_booked == False
    )
    if start_date:
        query = query.where(DoctorAvailability.available_date >= start_date)
    else:
        query = query.where(DoctorAvailability.available_date >= date.today())
    if end_date:
        query = query.where(DoctorAvailability.available_date <= end_date)
        
    query = query.order_by(DoctorAvailability.available_date.asc(), DoctorAvailability.start_time.asc())
    result = await db.execute(query)
    return result.scalars().all()
