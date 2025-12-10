"""
Repository layer for Blood app
Handles all data access operations for Stock and BloodRequest models
"""
from typing import List, Optional, Dict

from django.core.cache import cache
from django.db.models import Sum

from bloodbankmanagement import settings
from .models import Stock, BloodRequest
from .constants import BloodGroup, Status
from .exceptions import InvalidBloodGroupError


class StockRepository:
    """Repository for Stock model operations"""
    
    @staticmethod
    def get_all():
        """Get all stock records"""
        return Stock.objects.all()
    
    @staticmethod
    def get_by_bloodgroup(bloodgroup: str) -> Optional[Stock]:
        """Get stock by blood group"""
        try:
            return Stock.objects.get(bloodgroup=bloodgroup)
        except Stock.DoesNotExist:
            return None
    
    @staticmethod
    def get_total_units() -> int:
        """Get total units of all blood groups"""
        result = Stock.objects.aggregate(Sum('unit'))
        return result['unit__sum'] or 0
    
    @staticmethod
    def create_stock(bloodgroup: str, unit: int = 0) -> Stock:
        """Create a new stock entry"""
        stock = Stock(bloodgroup=bloodgroup, unit=unit)
        stock.save()
        return stock
    
    @staticmethod
    def update_unit(bloodgroup: str, unit: int) -> Stock:
        """Update stock unit for a blood group"""
        stock = StockRepository.get_by_bloodgroup(bloodgroup)
        if stock:
            stock.unit = unit
            stock.save()
            cache.delete("all_stocks_dict_data")
        return stock
    
    @staticmethod
    def increment_unit(bloodgroup: str, unit: int) -> Stock:
        """Increment stock unit by specified amount"""
        stock = StockRepository.get_by_bloodgroup(bloodgroup)
        if stock:
            stock.unit += unit
            stock.save()
        return stock
    
    @staticmethod
    def decrement_unit(bloodgroup: str, unit: int) -> Stock:
        """Decrement stock unit by specified amount"""
        stock = StockRepository.get_by_bloodgroup(bloodgroup)
        if stock:
            stock.unit -= unit
            stock.save()
        return stock
    
    @staticmethod
    def get_all_stocks_dict() -> Dict[str, Stock]:
        """Get all stocks as a dictionary keyed by blood group"""
        cache_key = "all_stocks_dict"
        stocks = {}

        stocks = cache.get(cache_key)
        if stocks is not None:
            print("Using cached stocks")
            return stocks

        print("Fetching stocks from database")
        stocks = Stock.objects.all()
        stocks_dict = {stock.bloodgroup: stock for stock in stocks}
        cache.set(cache_key, stocks_dict, timeout=settings.CACHE_TTL)
        return stocks_dict
    
    @staticmethod
    def initialize_stocks() -> None:
        """Initialize all blood group stocks if they don't exist"""
        existing_stocks = StockRepository.get_all()
        if existing_stocks.count() == 0:
            for bloodgroup in BloodGroup.ALL_GROUPS:
                StockRepository.create_stock(bloodgroup, unit=0)


class BloodRequestRepository:
    """Repository for BloodRequest model operations"""
    
    @staticmethod
    def get_all():
        """Get all blood requests"""
        return BloodRequest.objects.all()
    
    @staticmethod
    def get_by_id(request_id: int) -> Optional[BloodRequest]:
        """Get blood request by ID"""
        try:
            return BloodRequest.objects.get(id=request_id)
        except BloodRequest.DoesNotExist:
            return None
    
    @staticmethod
    def get_by_status(status: str):
        """Get blood requests by status"""
        return BloodRequest.objects.filter(status=status)
    
    @staticmethod
    def get_pending_requests():
        """Get all pending blood requests"""
        return BloodRequestRepository.get_by_status(Status.PENDING)
    
    @staticmethod
    def get_approved_requests():
        """Get all approved blood requests"""
        return BloodRequestRepository.get_by_status(Status.APPROVED)
    
    @staticmethod
    def get_rejected_requests():
        """Get all rejected blood requests"""
        return BloodRequestRepository.get_by_status(Status.REJECTED)
    
    @staticmethod
    def get_non_pending_requests():
        """Get all non-pending requests (approved or rejected)"""
        return BloodRequest.objects.exclude(status=Status.PENDING)
    
    @staticmethod
    def get_requests_by_donor(donor):
        """Get all requests made by a specific donor"""
        return BloodRequest.objects.filter(request_by_donor=donor)
    
    @staticmethod
    def get_requests_by_patient(patient):
        """Get all requests made by a specific patient"""
        return BloodRequest.objects.filter(request_by_patient=patient)
    
    @staticmethod
    def count_by_status(status: str) -> int:
        """Count requests by status with caching"""
        cache_key = f"request_{status.lower()}_count"
        count = cache.get(cache_key)
        
        if count is not None:
            print(f"Using cached {status} requests count")
            return count
            
        print(f"Fetching {status} requests count from database")
        count = BloodRequestRepository.get_by_status(status).count()
        cache.set(cache_key, count, timeout=settings.CACHE_TTL)
        return count
    
    @staticmethod
    def count_all() -> int:
        """Count all blood requests with caching"""
        cache_key = "request_total_count"
        count = cache.get(cache_key)
        
        if count is not None:
            print("Using cached total requests count")
            return count
            
        print("Fetching total requests count from database")
        count = BloodRequest.objects.count()
        cache.set(cache_key, count, timeout=settings.CACHE_TTL)
        return count
    
    @staticmethod
    def create_request(patient_name: str, patient_age: int, reason: str, 
                      bloodgroup: str, unit: int, request_by_donor=None, 
                      request_by_patient=None) -> BloodRequest:
        """Create a new blood request"""
        request = BloodRequest(
            patient_name=patient_name,
            patient_age=patient_age,
            reason=reason,
            bloodgroup=bloodgroup,
            unit=unit,
            request_by_donor=request_by_donor,
            request_by_patient=request_by_patient,
            status=Status.PENDING
        )
        request.save()
        return request
    
    @staticmethod
    def update_status(request_id: int, status: str) -> Optional[BloodRequest]:
        """Update the status of a blood request"""
        request = BloodRequestRepository.get_by_id(request_id)
        if request:
            request.status = status
            request.save()
        return request
