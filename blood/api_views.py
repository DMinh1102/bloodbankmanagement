"""
API Views for Blood Bank Management System
JSON endpoints for performance testing with Postman
"""
import time
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .services import BloodStockService, BloodRequestService, BloodDonationService
from donor.services import DonorService
from patient.services import PatientService


@csrf_exempt
@require_http_methods(["GET"])
def blood_stock_list(request):
    """Get all blood stock - API endpoint"""
    start_time = time.time()
    
    stocks = BloodStockService.get_all_stocks()
    
    data = {
        'success': True,
        'count': stocks.count(),
        'total_units': BloodStockService.get_total_units(),
        'stocks': [
            {
                'id': stock.id,
                'bloodgroup': stock.bloodgroup,
                'unit': stock.unit
            }
            for stock in stocks
        ],
        'query_time_ms': round((time.time() - start_time) * 1000, 2)
    }
    
    return JsonResponse(data)


@csrf_exempt
@require_http_methods(["GET"])
def blood_stock_detail(request, bloodgroup):
    """Get specific blood group stock - API endpoint"""
    start_time = time.time()
    
    stock = BloodStockService.get_stock_by_bloodgroup(bloodgroup)
    
    if not stock:
        return JsonResponse({
            'success': False,
            'error': f'Blood group {bloodgroup} not found',
            'query_time_ms': round((time.time() - start_time) * 1000, 2)
        }, status=404)
    
    data = {
        'success': True,
        'stock': {
            'id': stock.id,
            'bloodgroup': stock.bloodgroup,
            'unit': stock.unit
        },
        'query_time_ms': round((time.time() - start_time) * 1000, 2)
    }
    
    return JsonResponse(data)


@csrf_exempt
@require_http_methods(["GET"])
def blood_requests_list(request):
    """Get all blood requests - API endpoint"""
    start_time = time.time()
    
    requests_qs = BloodRequestService.get_all_requests()
    
    data = {
        'success': True,
        'count': requests_qs.count(),
        'requests': [
            {
                'id': req.id,
                'patient_name': req.patient_name,
                'patient_age': req.patient_age,
                'bloodgroup': req.bloodgroup,
                'unit': req.unit,
                'reason': req.reason,
                'status': req.status,
                'date': req.date.isoformat(),
                'requested_by': 'donor' if req.request_by_donor else 'patient'
            }
            for req in requests_qs
        ],
        'query_time_ms': round((time.time() - start_time) * 1000, 2)
    }
    
    return JsonResponse(data)


@csrf_exempt
@require_http_methods(["GET"])
def blood_requests_pending(request):
    """Get pending blood requests - API endpoint"""
    start_time = time.time()
    
    requests_qs = BloodRequestService.get_pending_requests()
    
    data = {
        'success': True,
        'count': requests_qs.count(),
        'requests': [
            {
                'id': req.id,
                'patient_name': req.patient_name,
                'patient_age': req.patient_age,
                'bloodgroup': req.bloodgroup,
                'unit': req.unit,
                'reason': req.reason,
                'status': req.status,
                'date': req.date.isoformat(),
                'requested_by': 'donor' if req.request_by_donor else 'patient'
            }
            for req in requests_qs
        ],
        'query_time_ms': round((time.time() - start_time) * 1000, 2)
    }
    
    return JsonResponse(data)


@csrf_exempt
@require_http_methods(["GET"])
def blood_request_detail(request, pk):
    """Get specific blood request - API endpoint"""
    start_time = time.time()
    
    from .repositories import BloodRequestRepository
    req = BloodRequestRepository.get_by_id(pk)
    
    if not req:
        return JsonResponse({
            'success': False,
            'error': f'Blood request {pk} not found',
            'query_time_ms': round((time.time() - start_time) * 1000, 2)
        }, status=404)
    
    data = {
        'success': True,
        'request': {
            'id': req.id,
            'patient_name': req.patient_name,
            'patient_age': req.patient_age,
            'bloodgroup': req.bloodgroup,
            'unit': req.unit,
            'reason': req.reason,
            'status': req.status,
            'date': req.date.isoformat(),
            'requested_by': 'donor' if req.request_by_donor else 'patient'
        },
        'query_time_ms': round((time.time() - start_time) * 1000, 2)
    }
    
    return JsonResponse(data)


@csrf_exempt
@require_http_methods(["GET"])
def donations_list(request):
    """Get all blood donations - API endpoint"""
    start_time = time.time()
    
    donations = BloodDonationService.get_all_donations()
    
    data = {
        'success': True,
        'count': donations.count(),
        'donations': [
            {
                'id': donation.id,
                'donor_name': donation.donor.get_name,
                'donor_id': donation.donor.id,
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


@csrf_exempt
@require_http_methods(["GET"])
def donations_pending(request):
    """Get pending blood donations - API endpoint"""
    start_time = time.time()
    
    from donor.repositories import BloodDonateRepository
    donations = BloodDonateRepository.get_all().filter(status='Pending')
    
    data = {
        'success': True,
        'count': donations.count(),
        'donations': [
            {
                'id': donation.id,
                'donor_name': donation.donor.get_name,
                'donor_id': donation.donor.id,
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


@csrf_exempt
@require_http_methods(["GET"])
def system_stats(request):
    """Get overall system statistics - API endpoint"""
    start_time = time.time()
    
    data = {
        'success': True,
        'stats': {
            'donors': {
                'total': DonorService.get_total_donors_count()
            },
            'patients': {
                'total': PatientService.get_total_patients_count()
            },
            'blood_stock': {
                'total_units': BloodStockService.get_total_units(),
                'by_group': BloodStockService.get_all_stocks_dict()
            },
            'requests': {
                'total': BloodRequestService.get_total_requests_count(),
                'approved': BloodRequestService.get_approved_requests_count()
            }
        },
        'query_time_ms': round((time.time() - start_time) * 1000, 2)
    }
    
    return JsonResponse(data)
