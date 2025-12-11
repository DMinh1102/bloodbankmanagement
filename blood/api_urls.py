"""
API URL Configuration for Blood Bank Management System
Centralized API routing for all JSON endpoints
"""
from django.urls import path
from blood import api_views as blood_api
from donor import api_views as donor_api
from patient import api_views as patient_api

urlpatterns = [
    # Blood Stock APIs
    path('blood-stock/', blood_api.blood_stock_list, name='api-blood-stock-list'),
    path('blood-stock/<str:bloodgroup>/', blood_api.blood_stock_detail, name='api-blood-stock-detail'),
    
    # Blood Request APIs
    path('blood-requests/', blood_api.blood_requests_list, name='api-blood-requests-list'),
    path('blood-requests/pending/', blood_api.blood_requests_pending, name='api-blood-requests-pending'),
    path('blood-requests/<int:pk>/', blood_api.blood_request_detail, name='api-blood-request-detail'),
    
    # Donation APIs
    path('donations/', blood_api.donations_list, name='api-donations-list'),
    path('donations/pending/', blood_api.donations_pending, name='api-donations-pending'),
    
    # Donor APIs
    path('donors/', donor_api.donors_list, name='api-donors-list'),
    path('donors/<int:pk>/', donor_api.donor_detail, name='api-donor-detail'),
    path('donors/<int:pk>/donations/', donor_api.donor_donations, name='api-donor-donations'),
    
    # Patient APIs
    path('patients/', patient_api.patients_list, name='api-patients-list'),
    path('patients/<int:pk>/', patient_api.patient_detail, name='api-patient-detail'),
    path('patients/<int:pk>/requests/', patient_api.patient_requests, name='api-patient-requests'),
    
    # System Stats API
    path('stats/', blood_api.system_stats, name='api-system-stats'),
]
