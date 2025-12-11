"""
API Views for Patient Management
JSON endpoints for performance testing with Postman
"""
import time
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .services import PatientService
from blood.services import BloodRequestService


@csrf_exempt
@require_http_methods(["GET"])
def patients_list(request):
    """Get all patients - API endpoint"""
    start_time = time.time()
    
    patients = PatientService.get_all_patients()
    
    data = {
        'success': True,
        'count': patients.count(),
        'patients': [
            {
                'id': patient.id,
                'name': patient.get_name,
                'age': patient.age,
                'bloodgroup': patient.bloodgroup,
                'disease': patient.disease,
                'doctorname': patient.doctorname,
                'address': patient.address,
                'mobile': patient.mobile,
                'username': patient.user.username,
                'email': patient.user.email
            }
            for patient in patients
        ],
        'query_time_ms': round((time.time() - start_time) * 1000, 2)
    }
    
    return JsonResponse(data)


@csrf_exempt
@require_http_methods(["GET"])
def patient_detail(request, pk):
    """Get specific patient details - API endpoint"""
    start_time = time.time()
    
    try:
        patient = PatientService.get_patient_by_id(pk)
        
        data = {
            'success': True,
            'patient': {
                'id': patient.id,
                'name': patient.get_name,
                'age': patient.age,
                'bloodgroup': patient.bloodgroup,
                'disease': patient.disease,
                'doctorname': patient.doctorname,
                'address': patient.address,
                'mobile': patient.mobile,
                'username': patient.user.username,
                'email': patient.user.email,
                'first_name': patient.user.first_name,
                'last_name': patient.user.last_name
            },
            'query_time_ms': round((time.time() - start_time) * 1000, 2)
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Patient {pk} not found',
            'query_time_ms': round((time.time() - start_time) * 1000, 2)
        }, status=404)


@csrf_exempt
@require_http_methods(["GET"])
def patient_requests(request, pk):
    """Get blood request history for a specific patient - API endpoint"""
    start_time = time.time()
    
    try:
        patient = PatientService.get_patient_by_id(pk)
        requests = BloodRequestService.get_requests_by_patient(patient)
        
        data = {
            'success': True,
            'patient_id': patient.id,
            'patient_name': patient.get_name,
            'count': requests.count(),
            'requests': [
                {
                    'id': req.id,
                    'patient_name': req.patient_name,
                    'patient_age': req.patient_age,
                    'bloodgroup': req.bloodgroup,
                    'unit': req.unit,
                    'reason': req.reason,
                    'status': req.status,
                    'date': req.date.isoformat()
                }
                for req in requests
            ],
            'query_time_ms': round((time.time() - start_time) * 1000, 2)
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Patient {pk} not found',
            'query_time_ms': round((time.time() - start_time) * 1000, 2)
        }, status=404)
