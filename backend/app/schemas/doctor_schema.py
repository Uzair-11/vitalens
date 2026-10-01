from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date, time

class SpecialtyResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    icon_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class SlotResponse(BaseModel):
    id: str
    doctor_id: str
    available_date: date
    start_time: time
    end_time: time
    slot_duration_minutes: int
    is_booked: bool

    model_config = ConfigDict(from_attributes=True)

class DoctorCardResponse(BaseModel):
    id: str
    specialty_id: str
    specialty_name: Optional[str] = None
    full_name: str
    qualification: str
    experience_years: int
    clinic_name: str
    address: str
    city: str
    consultation_fee: float
    rating: float
    review_count: int
    profile_photo_url: Optional[str] = None
    languages: List[str] = []

    model_config = ConfigDict(from_attributes=True)

class DoctorDetailResponse(DoctorCardResponse):
    bio: Optional[str] = None
    available_slots_count: Optional[int] = 0
    next_available_slot: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
