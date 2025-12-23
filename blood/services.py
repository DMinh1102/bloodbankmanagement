"""
Service layer for Blood app
Contains business logic for blood stock management, requests, and donations
"""
from typing import Dict, Optional, Tuple

from django.db import transaction

from .repositories import StockRepository, BloodRequestRepository
from .constants import BloodGroup, Status
from .exceptions import InsufficientBloodStockError, BloodRequestNotFoundError
from donor.repositories import BloodDonateRepository
from django.core.cache import cache

# Import async email tasks
from blood.tasks import (
    send_blood_request_approved_email,
    send_blood_request_rejected_email,
    send_donation_approved_email,
    send_donation_rejected_email,
)


class BloodStockService:
    """Service for managing blood stock inventory"""
    
    @staticmethod
    def initialize_stock_if_needed() -> None:
        """Initialize all blood group stocks if they don't exist"""
        StockRepository.initialize_stocks()
    
    @staticmethod
    def get_all_stocks():
        """Get all stock records"""
        return StockRepository.get_all()
    
    @staticmethod
    def get_stock_by_bloodgroup(bloodgroup: str):
        """Get stock for a specific blood group"""
        return StockRepository.get_by_bloodgroup(bloodgroup)
    
    @staticmethod
    def get_all_stocks_dict() -> Dict:
        """Get all stocks as a dictionary for dashboard display"""
        return StockRepository.get_all_stocks_dict()
    
    @staticmethod
    def get_total_units() -> int:
        """Get total units of all blood in stock"""
        return StockRepository.get_total_units()
    
    @staticmethod
    def update_stock_unit(bloodgroup: str, unit: int):
        """Update stock unit for a blood group"""
        return StockRepository.update_unit(bloodgroup, unit)
    
    @staticmethod
    def add_blood_to_stock(bloodgroup: str, unit: int):
        """Add blood units to stock (for approved donations)"""
        return StockRepository.increment_unit(bloodgroup, unit)
    
    @staticmethod
    def remove_blood_from_stock(bloodgroup: str, unit: int):
        """Remove blood units from stock (for approved requests)"""
        stock = StockRepository.get_by_bloodgroup(bloodgroup)
        if stock and stock.unit >= unit:
            return StockRepository.decrement_unit(bloodgroup, unit)
        else:
            available = stock.unit if stock else 0
            raise InsufficientBloodStockError(bloodgroup, unit, available)
    
    @staticmethod
    def check_stock_availability(bloodgroup: str, unit: int) -> Tuple[bool, int]:
        """
        Check if requested units are available in stock
        Returns: (is_available, available_units)
        """
        stock = StockRepository.get_by_bloodgroup(bloodgroup)
        if stock:
            return (stock.unit >= unit, stock.unit)
        return (False, 0)


class BloodRequestService:
    """Service for managing blood requests"""
    
    @staticmethod
    def get_all_requests():
        """Get all blood requests"""
        return BloodRequestRepository.get_all()
    
    @staticmethod
    def get_pending_requests():
        """Get all pending requests"""
        return BloodRequestRepository.get_pending_requests()
    
    @staticmethod
    def get_request_history():
        """Get all non-pending requests (approved/rejected)"""
        return BloodRequestRepository.get_non_pending_requests()
    
    @staticmethod
    def get_requests_by_donor(donor):
        """Get all requests made by a donor"""
        return BloodRequestRepository.get_requests_by_donor(donor)
    
    @staticmethod
    def get_requests_by_patient(patient):
        """Get all requests made by a patient"""
        return BloodRequestRepository.get_requests_by_patient(patient)
    
    @staticmethod
    def get_request_stats_for_donor(donor) -> Dict:
        """Get request statistics for a donor"""
        requests = BloodRequestRepository.get_requests_by_donor(donor)
        return {
            'total': requests.count(),
            'pending': requests.filter(status=Status.PENDING).count(),
            'approved': requests.filter(status=Status.APPROVED).count(),
            'rejected': requests.filter(status=Status.REJECTED).count(),
        }
    
    @staticmethod
    def get_request_stats_for_patient(patient) -> Dict:
        """Get request statistics for a patient"""
        requests = BloodRequestRepository.get_requests_by_patient(patient)
        return {
            'total': requests.count(),
            'pending': requests.filter(status=Status.PENDING).count(),
            'approved': requests.filter(status=Status.APPROVED).count(),
            'rejected': requests.filter(status=Status.REJECTED).count(),
        }
    
    @staticmethod
    @transaction.atomic
    def create_request(patient_name: str, patient_age: int, reason: str,
                      bloodgroup: str, unit: int, request_by_donor=None,
                      request_by_patient=None):
        """Create a new blood request"""
        request = BloodRequestRepository.create_request(
            patient_name=patient_name,
            patient_age=patient_age,
            reason=reason,
            bloodgroup=bloodgroup,
            unit=unit,
            request_by_donor=request_by_donor,
            request_by_patient=request_by_patient
        )
        cache.delete_many(["request_total_count", "request_pending_count"])
        return request
    
    @staticmethod
    @transaction.atomic
    def approve_request(request_id: int) -> Tuple[bool, Optional[str]]:
        """
        Approve a blood request and update stock
        Returns: (success, error_message)
        """
        request = BloodRequestRepository.get_by_id(request_id)
        if not request:
            raise BloodRequestNotFoundError(request_id)
        
        # Check stock availability
        is_available, available_units = BloodStockService.check_stock_availability(
            request.bloodgroup, request.unit
        )
        
        if not is_available:
            error_msg = (
                f"Stock Does Not Have Enough Blood To Approve This Request, "
                f"Only {available_units} Unit Available"
            )
            return (False, error_msg)
        
        # Update stock and request status
        BloodStockService.remove_blood_from_stock(request.bloodgroup, request.unit)
        BloodRequestRepository.update_status(request_id, Status.APPROVED)
        
        cache.delete_many(["request_pending_count", "request_approved_count"])
        
        # Send async email notification (non-blocking)
        if request.request_by_patient and hasattr(request.request_by_patient, 'user'):
            send_blood_request_approved_email.delay(
                patient_email=request.request_by_patient.user.email,
                patient_name=request.patient_name,
                bloodgroup=request.bloodgroup,
                unit=request.unit
            )
        
        return (True, None)
    
    @staticmethod
    @transaction.atomic
    def reject_request(request_id: int):
        """Reject a blood request"""
        request = BloodRequestRepository.get_by_id(request_id)
        if not request:
            raise BloodRequestNotFoundError(request_id)
        
        BloodRequestRepository.update_status(request_id, Status.REJECTED)
        cache.delete_many(["request_pending_count", "request_rejected_count"])
        
        # Send async email notification (non-blocking)
        if request.request_by_patient and hasattr(request.request_by_patient, 'user'):
            send_blood_request_rejected_email.delay(
                patient_email=request.request_by_patient.user.email,
                patient_name=request.patient_name,
                bloodgroup=request.bloodgroup,
                unit=request.unit,
                reason="Insufficient blood stock or other criteria not met"
            )
        
        return request
    
    @staticmethod
    def get_total_requests_count() -> int:
        """Get total count of all requests"""
        return BloodRequestRepository.count_all()
    
    @staticmethod
    def get_approved_requests_count() -> int:
        """Get count of approved requests"""
        return BloodRequestRepository.count_by_status(Status.APPROVED)


class BloodDonationService:
    """Service for managing blood donations"""
    
    @staticmethod
    def get_all_donations():
        """Get all blood donations"""
        return BloodDonateRepository.get_all()
    
    @staticmethod
    def get_donations_by_donor(donor):
        """Get all donations by a specific donor"""
        return BloodDonateRepository.get_by_donor(donor)
    
    @staticmethod
    def create_donation(donor, disease: str, age: int, bloodgroup: str, unit: int):
        """Create a new blood donation"""
        return BloodDonateRepository.create_donation(
            donor=donor,
            disease=disease,
            age=age,
            bloodgroup=bloodgroup,
            unit=unit
        )
    
    @staticmethod
    @transaction.atomic
    def approve_donation(donation_id: int):
        """Approve a blood donation and add to stock"""
        donation = BloodDonateRepository.get_by_id(donation_id)
        if not donation:
            from blood.exceptions import BloodDonationNotFoundError
            raise BloodDonationNotFoundError(donation_id)
        
        # Add blood to stock
        BloodStockService.add_blood_to_stock(donation.bloodgroup, donation.unit)
        
        # Update donation status
        BloodDonateRepository.update_status(donation_id, Status.APPROVED)
        
        # Send async email notification (non-blocking)
        if hasattr(donation.donor, 'user'):
            send_donation_approved_email.delay(
                donor_email=donation.donor.user.email,
                donor_name=donation.donor.get_name,
                bloodgroup=donation.bloodgroup,
                unit=donation.unit
            )
        
        return donation
    
    @staticmethod
    @transaction.atomic
    def reject_donation(donation_id: int):
        """Reject a blood donation"""
        donation = BloodDonateRepository.get_by_id(donation_id)
        if not donation:
            from blood.exceptions import BloodDonationNotFoundError
            raise BloodDonationNotFoundError(donation_id)
        
        BloodDonateRepository.update_status(donation_id, Status.REJECTED)
        
        # Send async email notification (non-blocking)
        if hasattr(donation.donor, 'user'):
            send_donation_rejected_email.delay(
                donor_email=donation.donor.user.email,
                donor_name=donation.donor.get_name,
                bloodgroup=donation.bloodgroup,
                reason=donation.disease if donation.disease != "Nothing" else ""
            )
        
        return donation
