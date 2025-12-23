"""
API Views for Donor Management
JSON endpoints for performance testing with Postman
"""
import time
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.cache import cache

from .services import DonorService, DonationService
from blood.auth import jwt_required

# ============================================================
# TOGGLE THIS FLAG TO ENABLE/DISABLE API CACHING
# ============================================================
USE_CACHE = True  # Set to True to enable caching
# ============================================================


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def donors_list(request):
    """Get all donors - API endpoint with optional caching"""
    start_time = time.time()
    
    # Try to get from cache first (only if USE_CACHE is True)
    if USE_CACHE:
        cache_key = 'api_donors_list_v1'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            # Return cached data with updated timing
            cached_data['query_time_ms'] = round((time.time() - start_time) * 1000, 2)
            cached_data['from_cache'] = True
            return JsonResponse(cached_data)
    
    # Cache miss or caching disabled - query database
    donors = DonorService.get_all_donors()
    
    data = {
        'success': True,
        'count': donors.count(),
        'donors': [
            {
                'id': donor.id,
                'name': donor.get_name,
                'bloodgroup': donor.bloodgroup,
                'address': donor.address,
                'mobile': donor.mobile,
                'username': donor.user.username,
                'email': donor.user.email
            }
            for donor in donors
        ],
        'from_cache': False
    }
    
    # Store in cache for 5 minutes (only if USE_CACHE is True)
    if USE_CACHE:
        cache.set(cache_key, data, 300)
    
    data['query_time_ms'] = round((time.time() - start_time) * 1000, 2)
    return JsonResponse(data)


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def donor_detail(request, pk):
    """Get specific donor details - API endpoint"""
    start_time = time.time()
    
    try:
        donor = DonorService.get_donor_by_id(pk)
        
        data = {
            'success': True,
            'donor': {
                'id': donor.id,
                'name': donor.get_name,
                'bloodgroup': donor.bloodgroup,
                'address': donor.address,
                'mobile': donor.mobile,
                'username': donor.user.username,
                'email': donor.user.email,
                'first_name': donor.user.first_name,
                'last_name': donor.user.last_name
            },
            'query_time_ms': round((time.time() - start_time) * 1000, 2)
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Donor {pk} not found',
            'query_time_ms': round((time.time() - start_time) * 1000, 2)
        }, status=404)


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def donor_donations(request, pk):
    """Get donation history for a specific donor - API endpoint"""
    start_time = time.time()
    
    try:
        donor = DonorService.get_donor_by_id(pk)
        donations = DonationService.get_donation_history(donor)
        
        data = {
            'success': True,
            'donor_id': donor.id,
            'donor_name': donor.get_name,
            'count': donations.count(),
            'donations': [
                {
                    'id': donation.id,
                    'bloodgroup': donation.bloodgroup,
                    'unit': donation.unit,
                    'disease': donation.disease,
                    'age': donation.age,
                    'status': donation.status,
                    'date': donation.date.isoformat()
                }
                for donation in donations
            ],
            'query_time_ms': round((time.time() - start_time) * 1000, 2)
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Donor {pk} not found',
            'query_time_ms': round((time.time() - start_time) * 1000, 2)
        }, status=404)
