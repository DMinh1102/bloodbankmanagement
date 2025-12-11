"""
API Views for Donor Management
JSON endpoints for performance testing with Postman
"""
import time
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .services import DonorService, DonationService


@csrf_exempt
@require_http_methods(["GET"])
def donors_list(request):
    """Get all donors - API endpoint"""
    start_time = time.time()
    
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
        'query_time_ms': round((time.time() - start_time) * 1000, 2)
    }
    
    return JsonResponse(data)


@csrf_exempt
@require_http_methods(["GET"])
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
