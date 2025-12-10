"""
Repository layer for Patient app
Handles all data access operations for Patient model
"""
from typing import Optional
from django.contrib.auth.models import User
from .models import Patient
from django.core.cache import cache
from bloodbankmanagement import settings


class PatientRepository:
    """Repository for Patient model operations"""
    
    @staticmethod
    def get_all():
        """Get all patients"""
        return Patient.objects.all()
    
    @staticmethod
    def get_by_id(patient_id: int) -> Optional[Patient]:
        """Get patient by ID"""
        try:
            return Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return None
    
    @staticmethod
    def get_by_user_id(user_id: int) -> Optional[Patient]:
        """Get patient by user ID"""
        try:
            return Patient.objects.get(user_id=user_id)
        except Patient.DoesNotExist:
            return None
    
    @staticmethod
    def get_by_user(user: User) -> Optional[Patient]:
        """Get patient by user object"""
        return PatientRepository.get_by_user_id(user.id)
    
    @staticmethod
    def create_patient(user: User, age: int, bloodgroup: str, disease: str,
                      doctorname: str, address: str, mobile: str, 
                      profile_pic=None) -> Patient:
        """Create a new patient"""
        patient = Patient(
            user=user,
            age=age,
            bloodgroup=bloodgroup,
            disease=disease,
            doctorname=doctorname,
            address=address,
            mobile=mobile,
            profile_pic=profile_pic
        )
        patient.save()
        return patient
    
    @staticmethod
    def update_patient(patient_id: int, **kwargs) -> Optional[Patient]:
        """Update patient information"""
        patient = PatientRepository.get_by_id(patient_id)
        if patient:
            for key, value in kwargs.items():
                if hasattr(patient, key):
                    setattr(patient, key, value)
            patient.save()
        return patient
    
    @staticmethod
    def delete_patient(patient_id: int) -> bool:
        """Delete a patient"""
        patient = PatientRepository.get_by_id(patient_id)
        if patient:
            patient.delete()
            return True
        return False
    
    @staticmethod
    def count_all() -> int:
        """Count all patients with caching"""
        cache_key = "patient_total_count"
        count = cache.get(cache_key)
        
        if count is not None:
            print("Using cached total patients count")
            return count
            
        print("Fetching total patients count from database")
        count = Patient.objects.count()
        cache.set(cache_key, count, timeout=settings.CACHE_TTL)
        return count
