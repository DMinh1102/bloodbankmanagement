"""
Repository layer for Donor app
Handles all data access operations for Donor and BloodDonate models
"""
from typing import Optional
from django.contrib.auth.models import User
from .models import Donor, BloodDonate
from blood.constants import Status


class DonorRepository:
    """Repository for Donor model operations"""
    
    @staticmethod
    def get_all():
        """Get all donors"""
        return Donor.objects.all()
    
    @staticmethod
    def get_by_id(donor_id: int) -> Optional[Donor]:
        """Get donor by ID"""
        try:
            return Donor.objects.get(id=donor_id)
        except Donor.DoesNotExist:
            return None
    
    @staticmethod
    def get_by_user_id(user_id: int) -> Optional[Donor]:
        """Get donor by user ID"""
        try:
            return Donor.objects.get(user_id=user_id)
        except Donor.DoesNotExist:
            return None
    
    @staticmethod
    def get_by_user(user: User) -> Optional[Donor]:
        """Get donor by user object"""
        return DonorRepository.get_by_user_id(user.id)
    
    @staticmethod
    def create_donor(user: User, bloodgroup: str, address: str, 
                    mobile: str, profile_pic=None) -> Donor:
        """Create a new donor"""
        donor = Donor(
            user=user,
            bloodgroup=bloodgroup,
            address=address,
            mobile=mobile,
            profile_pic=profile_pic
        )
        donor.save()
        return donor
    
    @staticmethod
    def update_donor(donor_id: int, **kwargs) -> Optional[Donor]:
        """Update donor information"""
        donor = DonorRepository.get_by_id(donor_id)
        if donor:
            for key, value in kwargs.items():
                if hasattr(donor, key):
                    setattr(donor, key, value)
            donor.save()
        return donor
    
    @staticmethod
    def delete_donor(donor_id: int) -> bool:
        """Delete a donor"""
        donor = DonorRepository.get_by_id(donor_id)
        if donor:
            donor.delete()
            return True
        return False
    
    @staticmethod
    def count_all() -> int:
        """Count all donors"""
        return Donor.objects.count()


class BloodDonateRepository:
    """Repository for BloodDonate model operations"""
    
    @staticmethod
    def get_all():
        """Get all blood donations"""
        return BloodDonate.objects.all()
    
    @staticmethod
    def get_by_id(donation_id: int) -> Optional[BloodDonate]:
        """Get blood donation by ID"""
        try:
            return BloodDonate.objects.get(id=donation_id)
        except BloodDonate.DoesNotExist:
            return None
    
    @staticmethod
    def get_by_donor(donor):
        """Get all donations by a specific donor"""
        return BloodDonate.objects.filter(donor=donor)
    
    @staticmethod
    def get_by_status(status: str):
        """Get donations by status"""
        return BloodDonate.objects.filter(status=status)
    
    @staticmethod
    def get_pending_donations():
        """Get all pending donations"""
        return BloodDonateRepository.get_by_status(Status.PENDING)
    
    @staticmethod
    def get_approved_donations():
        """Get all approved donations"""
        return BloodDonateRepository.get_by_status(Status.APPROVED)
    
    @staticmethod
    def create_donation(donor: Donor, disease: str, age: int, 
                       bloodgroup: str, unit: int) -> BloodDonate:
        """Create a new blood donation"""
        donation = BloodDonate(
            donor=donor,
            disease=disease,
            age=age,
            bloodgroup=bloodgroup,
            unit=unit,
            status=Status.PENDING
        )
        donation.save()
        return donation
    
    @staticmethod
    def update_status(donation_id: int, status: str) -> Optional[BloodDonate]:
        """Update the status of a blood donation"""
        donation = BloodDonateRepository.get_by_id(donation_id)
        if donation:
            donation.status = status
            donation.save()
        return donation
