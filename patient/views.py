from django.shortcuts import render, redirect, reverse
from . import forms
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required, user_passes_test
from blood import forms as bforms

# Import services
from .services import PatientService
from blood.services import BloodRequestService

# Import rate limiting decorators
from blood.decorators import patient_action_limit, strict_limit


@strict_limit
def patient_signup_view(request):
    """Patient signup view (rate limited to prevent spam)"""
    userForm = forms.PatientUserForm()
    patientForm = forms.PatientForm()
    mydict = {'userForm': userForm, 'patientForm': patientForm}
    
    if request.method == 'POST':
        userForm = forms.PatientUserForm(request.POST)
        patientForm = forms.PatientForm(request.POST, request.FILES)
        
        if userForm.is_valid() and patientForm.is_valid():
            # Save user
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            
            # Create patient using service
            PatientService.create_patient(
                user=user,
                age=patientForm.cleaned_data['age'],
                bloodgroup=patientForm.cleaned_data['bloodgroup'],
                disease=patientForm.cleaned_data.get('disease'),
                doctorname=patientForm.cleaned_data.get('doctorname'),
                address=patientForm.cleaned_data.get('address'),
                mobile=patientForm.cleaned_data.get('mobile'),
                profile_pic=patientForm.cleaned_data.get('profile_pic')
            )
            
        return HttpResponseRedirect('patientlogin')
    
    return render(request, 'patient/patientsignup.html', context=mydict)


def patient_dashboard_view(request):
    """Patient dashboard with statistics"""
    patient = PatientService.get_patient_by_user_id(request.user.id)
    stats = BloodRequestService.get_request_stats_for_patient(patient)
    
    context = {
        'requestpending': stats['pending'],
        'requestapproved': stats['approved'],
        'requestmade': stats['total'],
        'requestrejected': stats['rejected'],
    }
    
    return render(request, 'patient/patient_dashboard.html', context=context)


@patient_action_limit
def make_request_view(request):
    """Patient blood request view (rate limited: 5 per minute)"""
    request_form = bforms.RequestForm()
    
    if request.method == 'POST':
        request_form = bforms.RequestForm(request.POST)
        if request_form.is_valid():
            patient = PatientService.get_patient_by_user_id(request.user.id)
            
            # Create request using service
            BloodRequestService.create_request(
                patient_name=request_form.cleaned_data['patient_name'],
                patient_age=request_form.cleaned_data['patient_age'],
                reason=request_form.cleaned_data['reason'],
                bloodgroup=request_form.cleaned_data['bloodgroup'],
                unit=request_form.cleaned_data['unit'],
                request_by_patient=patient
            )
            
            return HttpResponseRedirect('my-request')
    
    return render(request, 'patient/makerequest.html', {'request_form': request_form})


def my_request_view(request):
    """Patient request history view"""
    patient = PatientService.get_patient_by_user_id(request.user.id)
    blood_request = BloodRequestService.get_requests_by_patient(patient)
    return render(request, 'patient/my_request.html', {'blood_request': blood_request})

