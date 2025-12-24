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
from django.conf import settings

CACHE_TTL = getattr(settings, 'CACHE_TTL', 60 * 15)


class BloodStockService:
    """Service for managing blood stock inventory"""
    
    @staticmethod
    def initialize_stock_if_needed() -> None:
        """Initialize all blood group stocks if they don't exist"""
        StockRepository.initialize_stocks()
    
    @staticmethod
    def get_all_stocks():
        """Get all stock records"""
        key = "stock_all"
        data = cache.get(key)
        if data is None:
            data = list(StockRepository.get_all())
            cache.set(key, data, CACHE_TTL)
        return data
    
    @staticmethod
    def get_stock_by_bloodgroup(bloodgroup: str):
        """Get stock for a specific blood group"""
        key = f"stock_detail_{bloodgroup}"
        data = cache.get(key)
        if data is None:
            data = StockRepository.get_by_bloodgroup(bloodgroup)
            cache.set(key, data, CACHE_TTL)
        return data
    
    @staticmethod
    def get_all_stocks_dict() -> Dict:
        """Get all stocks as a dictionary for dashboard display"""
        key = "stock_dict_all"
        data = cache.get(key)
        if data is None:
            data = StockRepository.get_all_stocks_dict()
            cache.set(key, data, CACHE_TTL)
        return data
    
    @staticmethod
    def get_total_units() -> int:
        """Get total units of all blood in stock"""
        key = "stock_total_units"
        data = cache.get(key)
        if data is None:
            data = StockRepository.get_total_units()
            cache.set(key, data, CACHE_TTL)
        return data
    
    @staticmethod
    def update_stock_unit(bloodgroup: str, unit: int):
        """Update stock unit for a blood group"""
        result = StockRepository.update_unit(bloodgroup, unit)
        
        # Invalidate related caches
        keys_to_delete = [
            f"stock_detail_{bloodgroup}",
            "stock_dict_all",
            "stock_total_units",
            "api_system_stats"
        ]
        cache.delete_many(keys_to_delete)
        return result
    
    @staticmethod
    def add_blood_to_stock(bloodgroup: str, unit: int):
        """Add blood units to stock (for approved donations)"""
        result = StockRepository.increment_unit(bloodgroup, unit)
        
        # Invalidate related caches
        keys_to_delete = [
            f"stock_detail_{bloodgroup}",
            "stock_dict_all",
            "stock_total_units",
            "api_system_stats"
        ]
        cache.delete_many(keys_to_delete)
        return result
    
    @staticmethod
    def remove_blood_from_stock(bloodgroup: str, unit: int):
        """Remove blood units from stock (for approved requests)"""
        stock = StockRepository.get_by_bloodgroup(bloodgroup)
        if stock and stock.unit >= unit:
            result = StockRepository.decrement_unit(bloodgroup, unit)
            
            # Invalidate related caches
            keys_to_delete = [
                f"stock_detail_{bloodgroup}",
                "stock_dict_all",
                "stock_all",
                "stock_total_units",
                "api_system_stats"
            ]
            cache.delete_many(keys_to_delete)
            return result
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
        key = "req_all"
        data = cache.get(key)
        if data is None:
            data = list(BloodRequestRepository.get_all())
            cache.set(key, data, CACHE_TTL)
        return data
    
    @staticmethod
    def get_pending_requests():
        """Get all pending requests"""
        key = "req_pending"
        data = cache.get(key)
        if data is None:
            data = list(BloodRequestRepository.get_pending_requests())
            cache.set(key, data, CACHE_TTL)
        return data
    
    @staticmethod
    def get_request_history():
        """Get all non-pending requests (approved/rejected)"""
        key = "req_history"
        data = cache.get(key)
        if data is None:
            data = list(BloodRequestRepository.get_non_pending_requests())
            cache.set(key, data, CACHE_TTL)
        return data
    
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
        cache.delete_many([
            "req_all", 
            "req_pending", 
            "req_count_total",
            "api_system_stats",
            "request_total_count", # keeping old keys if used elsewhere, but mainly using new naming
            "request_pending_count"
        ])
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
        
        cache.delete_many([
            "req_all", 
            "req_pending",
            "req_history",
            "req_count_approved", 
            "req_count_total",
            "api_system_stats",
            "request_pending_count", 
            "req_all", 
            "req_pending",
            "req_history",
            "req_count_approved", 
            "req_count_total",
            "api_system_stats",
            "request_pending_count", 
            "request_approved_count",
            f"req_detail_{request_id}"
        ])
        
        return (True, None)

    @staticmethod
    def get_request_by_id(request_id):
        """Get request by ID"""
        key = f"req_detail_{request_id}"
        data = cache.get(key)
        if data is None:
            data = BloodRequestRepository.get_by_id(request_id)
            if data:
                cache.set(key, data, CACHE_TTL)
        return data
    
    @staticmethod
    @transaction.atomic
    def reject_request(request_id: int):
        """Reject a blood request"""
        request = BloodRequestRepository.get_by_id(request_id)
        if not request:
            raise BloodRequestNotFoundError(request_id)
        
        BloodRequestRepository.update_status(request_id, Status.REJECTED)
        cache.delete_many([
            "req_all", 
            "req_pending",
            "req_history",
            "req_count_total",
            "api_system_stats",
            "request_pending_count", 
            "request_rejected_count"
        ])
        return request
    
    @staticmethod
    def get_total_requests_count() -> int:
        """Get total count of all requests"""
        key = "req_count_total"
        data = cache.get(key)
        if data is None:
            data = BloodRequestRepository.count_all()
            cache.set(key, data, CACHE_TTL)
        return data
    
    @staticmethod
    def get_approved_requests_count() -> int:
        """Get count of approved requests"""
        key = "req_count_approved"
        data = cache.get(key)
        if data is None:
            data = BloodRequestRepository.count_by_status(Status.APPROVED)
            cache.set(key, data, CACHE_TTL)
        return data


class BloodDonationService:
    """Service for managing blood donations"""
    
    @staticmethod
    def get_all_donations():
        """Get all blood donations"""
        key = "donation_all"
        data = cache.get(key)
        if data is None:
            data = list(BloodDonateRepository.get_all())
            cache.set(key, data, CACHE_TTL)
        return data
    
    @staticmethod
    def get_pending_donations():
        """Get all pending donations"""
        key = "donation_pending"
        data = cache.get(key)
        if data is None:
            from .constants import Status
            data = list(BloodDonateRepository.get_all().filter(status=Status.PENDING))
            cache.set(key, data, CACHE_TTL)
        return data

    @staticmethod
    def get_donations_by_donor(donor):
        """Get all donations by a specific donor"""
        return BloodDonateRepository.get_by_donor(donor)
    
    @staticmethod
    def create_donation(donor, disease: str, age: int, bloodgroup: str, unit: int):
        """Create a new blood donation"""
        donation = BloodDonateRepository.create_donation(
            donor=donor,
            disease=disease,
            age=age,
            bloodgroup=bloodgroup,
            unit=unit
        )
        
        cache.delete_many(["donation_all", "donation_pending", "api_system_stats"])
        return donation
    
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
        
        cache.delete_many(["donation_all", "donation_pending", "api_system_stats"])
        
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
        cache.delete_many(["donation_all", "donation_pending"])
        return donation
