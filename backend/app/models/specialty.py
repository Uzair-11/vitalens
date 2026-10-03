"""
Specialty models module.

MedicalSpecialty is defined in app.models.medical_specialty (Parent Table).
SpecialtyRecommendation is defined in app.models.specialty_recommendation (Child Table).

This module re-exports both models to preserve backwards compatibility across
the entire codebase.
"""
from app.models.medical_specialty import MedicalSpecialty
from app.models.specialty_recommendation import SpecialtyRecommendation

__all__ = ["MedicalSpecialty", "SpecialtyRecommendation"]
