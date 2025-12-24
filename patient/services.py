"""
Service layer for Patient app
Contains business logic for patient management
"""
from typing import Optional, Dict
from django.contrib.auth.models import User, Group
from django.db import transaction

from .repositories import PatientRepository
from .models import Patient
from blood.constants import UserGroup
from blood.exceptions import PatientNotFoundError
from django.core.cache import cache
from django.conf import settings

CACHE_TTL = getattr(settings, 'CACHE_TTL', 60 * 15)


class PatientService:
    """Service for managing patients"""
    
    @staticmethod
    def get_all_patients():
        """Get all patients"""
        key = "patient_all"
        data = cache.get(key)
        if data is None:
            data = list(PatientRepository.get_all())
            cache.set(key, data, CACHE_TTL)
        return data
    
    @staticmethod
    def get_patient_by_id(patient_id: int) -> Optional[Patient]:
        """Get patient by ID"""
        patient = PatientRepository.get_by_id(patient_id)
        if not patient:
            raise PatientNotFoundError(patient_id=patient_id)
        return patient
    
    @staticmethod
    def get_patient_by_user(user: User) -> Optional[Patient]:
        """Get patient by user object"""
        patient = PatientRepository.get_by_user(user)
        if not patient:
            raise PatientNotFoundError(user_id=user.id)
        return patient
    
    @staticmethod
    def get_patient_by_user_id(user_id: int) -> Optional[Patient]:
        """Get patient by user ID"""
        patient = PatientRepository.get_by_user_id(user_id)
        if not patient:
            raise PatientNotFoundError(user_id=user_id)
        return patient
    
    @staticmethod
    @transaction.atomic
    def create_patient(user: User, age: int, bloodgroup: str, disease: str,
                      doctorname: str, address: str, mobile: str, 
                      profile_pic=None) -> Patient:
        """Create a new patient and assign to PATIENT group"""
        # Create patient
        patient = PatientRepository.create_patient(
            user=user,
            age=age,
            bloodgroup=bloodgroup,
            disease=disease,
            doctorname=doctorname,
            address=address,
            mobile=mobile,
            profile_pic=profile_pic
        )
        
        # Add user to PATIENT group
        patient_group, created = Group.objects.get_or_create(name=UserGroup.PATIENT)
        patient_group.user_set.add(user)
        
        patient_group.user_set.add(user)
        
        cache.delete_many(["patient_total_count", "patient_all"])
        return patient
    
    @staticmethod
    @transaction.atomic
    def update_patient(patient_id: int, user_data: Dict = None, 
                      patient_data: Dict = None) -> Patient:
        """
        Update patient and associated user information
        user_data: dict with user fields (first_name, last_name, etc.)
        patient_data: dict with patient fields (age, bloodgroup, disease, etc.)
        """
        patient = PatientService.get_patient_by_id(patient_id)
        
        # Update user information
        if user_data:
            user = patient.user
            for key, value in user_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            # Handle password separately
            if 'password' in user_data:
                user.set_password(user_data['password'])
            user.save()
        
        # Update patient information
        if patient_data:
            PatientRepository.update_patient(patient_id, **patient_data)
        
        cache.delete_many(["patient_total_count", "patient_all"])
        
        return PatientRepository.get_by_id(patient_id)
    
    @staticmethod
    @transaction.atomic
    def delete_patient(patient_id: int) -> bool:
        """Delete a patient and associated user"""
        patient = PatientService.get_patient_by_id(patient_id)
        user = patient.user
        
        # Delete patient (will cascade)
        PatientRepository.delete_patient(patient_id)
        
        # Delete user
        user.delete()

        cache.delete_many(["patient_total_count", "patient_all"])
        return True
    
    @staticmethod
    def get_total_patients_count() -> int:
        """Get total count of patients"""
        key = "patient_total_count"
        data = cache.get(key)
        if data is None:
            data = PatientRepository.count_all()
            cache.set(key, data, CACHE_TTL)
        return data
