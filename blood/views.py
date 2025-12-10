from django.contrib.auth import logout
from django.shortcuts import render, redirect, reverse
from . import forms
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from donor import models as dmodels
from patient import models as pmodels
from donor import forms as dforms
from patient import forms as pforms

# Import services
from .services import BloodStockService, BloodRequestService, BloodDonationService
from donor.services import DonorService
from patient.services import PatientService
from .constants import BloodGroup, UserGroup
from .exceptions import InsufficientBloodStockError


def home_view(request):
    """Homepage view - initializes blood stock if needed"""
    # Initialize stock if needed
    BloodStockService.initialize_stock_if_needed()
    
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request, 'blood/index.html')


def is_donor(user):
    """Check if user is in DONOR group"""
    return user.groups.filter(name=UserGroup.DONOR).exists()


def is_patient(user):
    """Check if user is in PATIENT group"""
    return user.groups.filter(name=UserGroup.PATIENT).exists()


def afterlogin_view(request):
    """Redirect user to appropriate dashboard after login"""
    if is_donor(request.user):
        return redirect('donor/donor-dashboard')
    elif is_patient(request.user):
        return redirect('patient/patient-dashboard')
    else:
        return redirect('admin-dashboard')


@login_required(login_url='adminlogin')
def admin_dashboard_view(request):
    """Admin dashboard with blood stock and statistics"""
    stocks = BloodStockService.get_all_stocks_dict()
    
    context = {
        'A1': stocks.get(BloodGroup.A_POSITIVE),
        'A2': stocks.get(BloodGroup.A_NEGATIVE),
        'B1': stocks.get(BloodGroup.B_POSITIVE),
        'B2': stocks.get(BloodGroup.B_NEGATIVE),
        'AB1': stocks.get(BloodGroup.AB_POSITIVE),
        'AB2': stocks.get(BloodGroup.AB_NEGATIVE),
        'O1': stocks.get(BloodGroup.O_POSITIVE),
        'O2': stocks.get(BloodGroup.O_NEGATIVE),
        'totaldonors': DonorService.get_total_donors_count(),
        'totalbloodunit': BloodStockService.get_total_units(),
        'totalrequest': BloodRequestService.get_total_requests_count(),
        'totalapprovedrequest': BloodRequestService.get_approved_requests_count()
    }
    return render(request, 'blood/admin_dashboard.html', context=context)


@login_required(login_url='adminlogin')
def admin_blood_view(request):
    """Admin blood stock management view"""
    stocks = BloodStockService.get_all_stocks_dict()
    
    context = {
        'bloodForm': forms.BloodForm(),
        'A1': stocks.get(BloodGroup.A_POSITIVE),
        'A2': stocks.get(BloodGroup.A_NEGATIVE),
        'B1': stocks.get(BloodGroup.B_POSITIVE),
        'B2': stocks.get(BloodGroup.B_NEGATIVE),
        'AB1': stocks.get(BloodGroup.AB_POSITIVE),
        'AB2': stocks.get(BloodGroup.AB_NEGATIVE),
        'O1': stocks.get(BloodGroup.O_POSITIVE),
        'O2': stocks.get(BloodGroup.O_NEGATIVE),
    }
    
    if request.method == 'POST':
        bloodForm = forms.BloodForm(request.POST)
        if bloodForm.is_valid():
            bloodgroup = bloodForm.cleaned_data['bloodgroup']
            unit = bloodForm.cleaned_data['unit']
            BloodStockService.update_stock_unit(bloodgroup, unit)
        return HttpResponseRedirect('admin-blood')
    
    return render(request, 'blood/admin_blood.html', context=context)


@login_required(login_url='adminlogin')
def admin_donor_view(request):
    """Admin view to see all donors"""
    donors = DonorService.get_all_donors()
    return render(request, 'blood/admin_donor.html', {'donors': donors})


@login_required(login_url='adminlogin')
def update_donor_view(request, pk):
    """Admin view to update donor information"""
    donor = DonorService.get_donor_by_id(pk)
    user = donor.user
    
    userForm = dforms.DonorUserForm(instance=user)
    donorForm = dforms.DonorForm(request.FILES, instance=donor)
    mydict = {'userForm': userForm, 'donorForm': donorForm}
    
    if request.method == 'POST':
        userForm = dforms.DonorUserForm(request.POST, instance=user)
        donorForm = dforms.DonorForm(request.POST, request.FILES, instance=donor)
        
        if userForm.is_valid() and donorForm.is_valid():
            # Prepare user data
            user_data = {
                'first_name': userForm.cleaned_data.get('first_name'),
                'last_name': userForm.cleaned_data.get('last_name'),
                'password': userForm.cleaned_data.get('password'),
            }
            
            # Prepare donor data
            donor_data = {
                'bloodgroup': donorForm.cleaned_data['bloodgroup'],
                'address': donorForm.cleaned_data.get('address'),
                'mobile': donorForm.cleaned_data.get('mobile'),
            }
            if request.FILES.get('profile_pic'):
                donor_data['profile_pic'] = request.FILES['profile_pic']
            
            # Update using service
            DonorService.update_donor(pk, user_data=user_data, donor_data=donor_data)
            return redirect('admin-donor')
    
    return render(request, 'blood/update_donor.html', context=mydict)


@login_required(login_url='adminlogin')
def delete_donor_view(request, pk):
    """Admin view to delete a donor"""
    DonorService.delete_donor(pk)
    return HttpResponseRedirect('/admin-donor')


@login_required(login_url='adminlogin')
def admin_patient_view(request):
    """Admin view to see all patients"""
    patients = PatientService.get_all_patients()
    return render(request, 'blood/admin_patient.html', {'patients': patients})


@login_required(login_url='adminlogin')
def update_patient_view(request, pk):
    """Admin view to update patient information"""
    patient = PatientService.get_patient_by_id(pk)
    user = patient.user
    
    userForm = pforms.PatientUserForm(instance=user)
    patientForm = pforms.PatientForm(request.FILES, instance=patient)
    mydict = {'userForm': userForm, 'patientForm': patientForm}
    
    if request.method == 'POST':
        userForm = pforms.PatientUserForm(request.POST, instance=user)
        patientForm = pforms.PatientForm(request.POST, request.FILES, instance=patient)
        
        if userForm.is_valid() and patientForm.is_valid():
            # Prepare user data
            user_data = {
                'first_name': userForm.cleaned_data.get('first_name'),
                'last_name': userForm.cleaned_data.get('last_name'),
                'password': userForm.cleaned_data.get('password'),
            }
            
            # Prepare patient data
            patient_data = {
                'bloodgroup': patientForm.cleaned_data['bloodgroup'],
                'age': patientForm.cleaned_data.get('age'),
                'disease': patientForm.cleaned_data.get('disease'),
                'doctorname': patientForm.cleaned_data.get('doctorname'),
                'address': patientForm.cleaned_data.get('address'),
                'mobile': patientForm.cleaned_data.get('mobile'),
            }
            if request.FILES.get('profile_pic'):
                patient_data['profile_pic'] = request.FILES['profile_pic']
            
            # Update using service
            PatientService.update_patient(pk, user_data=user_data, patient_data=patient_data)
            return redirect('admin-patient')
    
    return render(request, 'blood/update_patient.html', context=mydict)


@login_required(login_url='adminlogin')
def delete_patient_view(request, pk):
    """Admin view to delete a patient"""
    PatientService.delete_patient(pk)
    return HttpResponseRedirect('/admin-patient')


@login_required(login_url='adminlogin')
def admin_request_view(request):
    """Admin view to see pending blood requests"""
    requests = BloodRequestService.get_pending_requests()
    return render(request, 'blood/admin_request.html', {'requests': requests})


@login_required(login_url='adminlogin')
def admin_request_history_view(request):
    """Admin view to see blood request history"""
    requests = BloodRequestService.get_request_history()
    return render(request, 'blood/admin_request_history.html', {'requests': requests})


@login_required(login_url='adminlogin')
def admin_donation_view(request):
    """Admin view to see all blood donations"""
    donations = BloodDonationService.get_all_donations()
    return render(request, 'blood/admin_donation.html', {'donations': donations})


@login_required(login_url='adminlogin')
def update_approve_status_view(request, pk):
    """Admin view to approve a blood request"""
    success, error_message = BloodRequestService.approve_request(pk)
    
    requests = BloodRequestService.get_pending_requests()
    context = {'requests': requests}
    
    if not success:
        context['message'] = error_message
    
    return render(request, 'blood/admin_request.html', context)


@login_required(login_url='adminlogin')
def update_reject_status_view(request, pk):
    """Admin view to reject a blood request"""
    BloodRequestService.reject_request(pk)
    return HttpResponseRedirect('/admin-request')


@login_required(login_url='adminlogin')
def approve_donation_view(request, pk):
    """Admin view to approve a blood donation"""
    BloodDonationService.approve_donation(pk)
    return HttpResponseRedirect('/admin-donation')


@login_required(login_url='adminlogin')
def reject_donation_view(request, pk):
    """Admin view to reject a blood donation"""
    BloodDonationService.reject_donation(pk)
    return HttpResponseRedirect('/admin-donation')

def logout_view(request):
    logout(request)
    return redirect('adminlogin') # Hoặc tên URL trang login của bạn