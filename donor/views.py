from django.db import transaction
from django.shortcuts import render, redirect, reverse
from . import forms
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required, user_passes_test
from blood import forms as bforms

# Import services
from .services import DonorService, DonationService
from blood.services import BloodRequestService

# Import rate limiting decorators
from blood.decorators import donor_action_limit, strict_limit


@strict_limit
@transaction.atomic
def donor_signup_view(request):
    """Donor signup view (rate limited to prevent spam)"""
    userForm = forms.DonorUserForm()
    donorForm = forms.DonorForm()
    mydict = {'userForm': userForm, 'donorForm': donorForm}
    
    if request.method == 'POST':
        userForm = forms.DonorUserForm(request.POST)
        donorForm = forms.DonorForm(request.POST, request.FILES)
        
        if userForm.is_valid() and donorForm.is_valid():
            # Save user
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            
            # Create donor using service
            DonorService.create_donor(
                user=user,
                bloodgroup=donorForm.cleaned_data['bloodgroup'],
                address=donorForm.cleaned_data.get('address'),
                mobile=donorForm.cleaned_data.get('mobile'),
                profile_pic=donorForm.cleaned_data.get('profile_pic')
            )
            
        return HttpResponseRedirect('donorlogin')
    
    return render(request, 'donor/donorsignup.html', context=mydict)

@login_required(login_url="donorlogin")
def donor_dashboard_view(request):
    """Donor dashboard with statistics"""
    donor = DonorService.get_donor_by_user_id(request.user.id)
    stats = BloodRequestService.get_request_stats_for_donor(donor)
    
    context = {
        'requestpending': stats['pending'],
        'requestapproved': stats['approved'],
        'requestmade': stats['total'],
        'requestrejected': stats['rejected'],
    }
    return render(request, 'donor/donor_dashboard.html', context=context)

@login_required(login_url="donorlogin")
@donor_action_limit
def donate_blood_view(request):
    """Donor blood donation view (rate limited: 5 per minute)"""
    donation_form = forms.DonationForm()
    
    if request.method == 'POST':
        donation_form = forms.DonationForm(request.POST)
        if donation_form.is_valid():
            donor = DonorService.get_donor_by_user_id(request.user.id)
            
            # Create donation using service
            DonationService.create_donation(
                donor=donor,
                disease=donation_form.cleaned_data.get('disease', 'Nothing'),
                age=donation_form.cleaned_data['age'],
                bloodgroup=donation_form.cleaned_data['bloodgroup'],
                unit=donation_form.cleaned_data['unit']
            )
            
            return HttpResponseRedirect('donation-history')
    
    return render(request, 'donor/donate_blood.html', {'donation_form': donation_form})

@login_required(login_url="donorlogin")
def donation_history_view(request):
    """Donor donation history view"""
    donor = DonorService.get_donor_by_user_id(request.user.id)
    donations = DonationService.get_donation_history(donor)
    return render(request, 'donor/donation_history.html', {'donations': donations})

@login_required(login_url="donorlogin")
@donor_action_limit
def make_request_view(request):
    """Donor blood request view (rate limited: 5 per minute)"""
    request_form = bforms.RequestForm()
    
    if request.method == 'POST':
        request_form = bforms.RequestForm(request.POST)
        if request_form.is_valid():
            donor = DonorService.get_donor_by_user_id(request.user.id)
            
            # Create request using service
            BloodRequestService.create_request(
                patient_name=request_form.cleaned_data['patient_name'],
                patient_age=request_form.cleaned_data['patient_age'],
                reason=request_form.cleaned_data['reason'],
                bloodgroup=request_form.cleaned_data['bloodgroup'],
                unit=request_form.cleaned_data['unit'],
                request_by_donor=donor
            )
            
            return HttpResponseRedirect('request-history')
    
    return render(request, 'donor/makerequest.html', {'request_form': request_form})

@login_required(login_url="donorlogin")
def request_history_view(request):
    """Donor request history view"""
    donor = DonorService.get_donor_by_user_id(request.user.id)
    blood_request = BloodRequestService.get_requests_by_donor(donor)
    return render(request, 'donor/request_history.html', {'blood_request': blood_request})

