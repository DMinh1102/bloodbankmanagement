"""
API Views for Blood Bank Management System
JSON endpoints for performance testing with Postman
"""

import time
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .services import (
    BloodStockService,
    BloodRequestService,
    BloodDonationService,
)
from donor.services import DonorService
from patient.services import PatientService

from .decorators import strict_limit
from .auth import jwt_required


# =====================================================
# BLOOD STOCK
# =====================================================

@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
@strict_limit
def blood_stock_list(request):
    start_time = time.time()

    stocks = BloodStockService.get_all_stocks()

    data = {
        "success": True,
        "count": stocks.count(),
        "total_units": BloodStockService.get_total_units(),
        "stocks": [
            {
                "id": s.id,
                "bloodgroup": s.bloodgroup,
                "unit": s.unit,
            }
            for s in stocks
        ],
        "query_time_ms": round((time.time() - start_time) * 1000, 2),
    }

    return JsonResponse(data)


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def blood_stock_detail(request, bloodgroup):
    start_time = time.time()

    stock = BloodStockService.get_stock_by_bloodgroup(bloodgroup)

    if not stock:
        return JsonResponse(
            {
                "success": False,
                "error": f"Blood group {bloodgroup} not found",
                "query_time_ms": round((time.time() - start_time) * 1000, 2),
            },
            status=404,
        )

    data = {
        "success": True,
        "stock": {
            "id": stock.id,
            "bloodgroup": stock.bloodgroup,
            "unit": stock.unit,
        },
        "query_time_ms": round((time.time() - start_time) * 1000, 2),
    }

    return JsonResponse(data)


# =====================================================
# BLOOD REQUESTS
# =====================================================

@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def blood_requests_list(request):
    start_time = time.time()

    requests_qs = BloodRequestService.get_all_requests()

    data = {
        "success": True,
        "count": requests_qs.count(),
        "requests": [
            {
                "id": r.id,
                "patient_name": r.patient_name,
                "patient_age": r.patient_age,
                "bloodgroup": r.bloodgroup,
                "unit": r.unit,
                "reason": r.reason,
                "status": r.status,
                "date": r.date.isoformat(),
                "requested_by": "donor" if r.request_by_donor else "patient",
            }
            for r in requests_qs
        ],
        "query_time_ms": round((time.time() - start_time) * 1000, 2),
    }

    return JsonResponse(data)


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def blood_requests_pending(request):
    start_time = time.time()

    requests_qs = BloodRequestService.get_pending_requests()

    data = {
        "success": True,
        "count": requests_qs.count(),
        "requests": [
            {
                "id": r.id,
                "patient_name": r.patient_name,
                "patient_age": r.patient_age,
                "bloodgroup": r.bloodgroup,
                "unit": r.unit,
                "reason": r.reason,
                "status": r.status,
                "date": r.date.isoformat(),
                "requested_by": "donor" if r.request_by_donor else "patient",
            }
            for r in requests_qs
        ],
        "query_time_ms": round((time.time() - start_time) * 1000, 2),
    }

    return JsonResponse(data)


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def blood_request_detail(request, pk):
    start_time = time.time()

    request_obj = BloodRequestService.get_request_by_id(pk)

    if not request_obj:
        return JsonResponse(
            {
                "success": False,
                "error": f"Blood request {pk} not found",
                "query_time_ms": round((time.time() - start_time) * 1000, 2),
            },
            status=404,
        )

    data = {
        "success": True,
        "request": {
            "id": request_obj.id,
            "patient_name": request_obj.patient_name,
            "patient_age": request_obj.patient_age,
            "bloodgroup": request_obj.bloodgroup,
            "unit": request_obj.unit,
            "reason": request_obj.reason,
            "status": request_obj.status,
            "date": request_obj.date.isoformat(),
            "requested_by": (
                "donor" if request_obj.request_by_donor else "patient"
            ),
        },
        "query_time_ms": round((time.time() - start_time) * 1000, 2),
    }

    return JsonResponse(data)


# =====================================================
# DONATIONS
# =====================================================

@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def donations_list(request):
    start_time = time.time()

    donations = BloodDonationService.get_all_donations()

    data = {
        "success": True,
        "count": donations.count(),
        "donations": [
            {
                "id": d.id,
                "donor_id": d.donor.id,
                "donor_name": d.donor.get_name(),
                "bloodgroup": d.bloodgroup,
                "unit": d.unit,
                "disease": d.disease,
                "age": d.age,
                "status": d.status,
                "date": d.date.isoformat(),
            }
            for d in donations
        ],
        "query_time_ms": round((time.time() - start_time) * 1000, 2),
    }

    return JsonResponse(data)


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def donations_pending(request):
    start_time = time.time()

    donations = BloodDonationService.get_pending_donations()

    data = {
        "success": True,
        "count": donations.count(),
        "donations": [
            {
                "id": d.id,
                "donor_id": d.donor.id,
                "donor_name": d.donor.get_name(),
                "bloodgroup": d.bloodgroup,
                "unit": d.unit,
                "disease": d.disease,
                "age": d.age,
                "status": d.status,
                "date": d.date.isoformat(),
            }
            for d in donations
        ],
        "query_time_ms": round((time.time() - start_time) * 1000, 2),
    }

    return JsonResponse(data)


# =====================================================
# SYSTEM STATISTICS
# =====================================================

@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def system_stats(request):
    start_time = time.time()

    data = {
        "success": True,
        "stats": {
            "donors": {
                "total": DonorService.get_total_donors_count(),
            },
            "patients": {
                "total": PatientService.get_total_patients_count(),
            },
            "blood_stock": {
                "total_units": BloodStockService.get_total_units(),
                "by_group": BloodStockService.get_all_stocks_dict(),
            },
            "requests": {
                "total": BloodRequestService.get_total_requests_count(),
                "approved": BloodRequestService.get_approved_requests_count(),
            },
        },
        "query_time_ms": round((time.time() - start_time) * 1000, 2),
    }

    return JsonResponse(data)
