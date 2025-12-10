"""
Service layer for Donor app
Contains business logic for donor management and donations
"""
from typing import Optional, Dict
from django.contrib.auth.models import User, Group
from .repositories import DonorRepository, BloodDonateRepository
from .models import Donor
from blood.constants import UserGroup
from blood.exceptions import DonorNotFoundError
from django.core.cache import cache


class DonorService:
    """Service for managing donors"""
    
    @staticmethod
    def get_all_donors():
        """Get all donors"""
        return DonorRepository.get_all()
    
    @staticmethod
    def get_donor_by_id(donor_id: int) -> Optional[Donor]:
        """Get donor by ID"""
        donor = DonorRepository.get_by_id(donor_id)
        if not donor:
            raise DonorNotFoundError(donor_id=donor_id)
        return donor
    
    @staticmethod
    def get_donor_by_user(user: User) -> Optional[Donor]:
        """Get donor by user object"""
        donor = DonorRepository.get_by_user(user)
        if not donor:
            raise DonorNotFoundError(user_id=user.id)
        return donor
    
    @staticmethod
    def get_donor_by_user_id(user_id: int) -> Optional[Donor]:
        """Get donor by user ID"""
        donor = DonorRepository.get_by_user_id(user_id)
        if not donor:
            raise DonorNotFoundError(user_id=user_id)
        return donor
    
    @staticmethod
    def create_donor(user: User, bloodgroup: str, address: str, 
                    mobile: str, profile_pic=None) -> Donor:
        """Create a new donor and assign to DONOR group"""
        # Create donor
        donor = DonorRepository.create_donor(
            user=user,
            bloodgroup=bloodgroup,
            address=address,
            mobile=mobile,
            profile_pic=profile_pic
        )
        
        # Add user to DONOR group
        donor_group, created = Group.objects.get_or_create(name=UserGroup.DONOR)
        donor_group.user_set.add(user)
        
        donor_group.user_set.add(user)
        
        cache.delete("donor_total_count")
        return donor
    
    @staticmethod
    def update_donor(donor_id: int, user_data: Dict = None, donor_data: Dict = None) -> Donor:
        """
        Update donor and associated user information
        user_data: dict with user fields (first_name, last_name, etc.)
        donor_data: dict with donor fields (bloodgroup, address, mobile, etc.)
        """
        donor = DonorService.get_donor_by_id(donor_id)
        
        # Update user information
        if user_data:
            user = donor.user
            for key, value in user_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            # Handle password separately
            if 'password' in user_data:
                user.set_password(user_data['password'])
            user.save()
        
        # Update donor information
        if donor_data:
            DonorRepository.update_donor(donor_id, **donor_data)
        
        return DonorRepository.get_by_id(donor_id)
    
    @staticmethod
    def delete_donor(donor_id: int) -> bool:
        """Delete a donor and associated user"""
        donor = DonorService.get_donor_by_id(donor_id)
        user = donor.user
        
        # Delete donor (will cascade)
        DonorRepository.delete_donor(donor_id)
        
        # Delete user
        user.delete()
        
        # Delete user
        user.delete()
        
        cache.delete("donor_total_count")
        return True
    
    @staticmethod
    def get_total_donors_count() -> int:
        """Get total count of donors"""
        return DonorRepository.count_all()


class DonationService:
    """Service for managing blood donations by donors"""
    
    @staticmethod
    def create_donation(donor: Donor, disease: str, age: int, 
                       bloodgroup: str, unit: int):
        """Create a new blood donation"""
        return BloodDonateRepository.create_donation(
            donor=donor,
            disease=disease,
            age=age,
            bloodgroup=bloodgroup,
            unit=unit
        )
    
    @staticmethod
    def get_donation_history(donor):
        """Get donation history for a donor"""
        return BloodDonateRepository.get_by_donor(donor)
