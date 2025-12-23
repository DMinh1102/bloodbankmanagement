"""
Celery tasks for Blood Bank Management System
Handles async email notifications with retry logic
"""
import logging
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


class EmailTaskError(Exception):
    """Custom exception for email task failures"""
    pass


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,  # Exponential backoff: 60s, 120s, 240s
    retry_backoff_max=600,  # Max 10 minutes between retries
)
def send_blood_request_approved_email(self, patient_email, patient_name, bloodgroup, unit):
    """
    Send email notification when blood request is approved.
    Retries up to 3 times with exponential backoff on failure.
    """
    subject = f"Blood Request Approved - {bloodgroup}"
    message = f"""
Dear {patient_name},

Great news! Your blood request has been APPROVED.

Details:
- Blood Group: {bloodgroup}
- Units: {unit}

Please visit the Blood Bank to collect your blood.

Thank you for using our Blood Bank Management System.

Best regards,
Blood Bank Management Team
    """.strip()
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[patient_email],
            fail_silently=False,
        )
        logger.info(f"✅ Approval email sent to {patient_email}")
        return {"status": "success", "email": patient_email}
    
    except Exception as e:
        logger.error(f"❌ Failed to send approval email to {patient_email}: {e}")
        # Log final failure after all retries exhausted
        if self.request.retries >= self.max_retries:
            logger.critical(f"🚨 FINAL FAILURE: Could not send email to {patient_email} after {self.max_retries} retries")
            # Here you could save to DB for admin review
        raise


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def send_blood_request_rejected_email(self, patient_email, patient_name, bloodgroup, unit, reason=""):
    """
    Send email notification when blood request is rejected.
    """
    subject = f"Blood Request Update - {bloodgroup}"
    message = f"""
Dear {patient_name},

We regret to inform you that your blood request could not be approved at this time.

Details:
- Blood Group: {bloodgroup}
- Units Requested: {unit}
{f'- Reason: {reason}' if reason else ''}

This may be due to insufficient stock. Please contact the Blood Bank for more information.

Thank you for your understanding.

Best regards,
Blood Bank Management Team
    """.strip()
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[patient_email],
            fail_silently=False,
        )
        logger.info(f"✅ Rejection email sent to {patient_email}")
        return {"status": "success", "email": patient_email}
    
    except Exception as e:
        logger.error(f"❌ Failed to send rejection email to {patient_email}: {e}")
        if self.request.retries >= self.max_retries:
            logger.critical(f"🚨 FINAL FAILURE: Could not send email to {patient_email} after {self.max_retries} retries")
        raise


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def send_donation_approved_email(self, donor_email, donor_name, bloodgroup, unit):
    """
    Send email notification when blood donation is approved.
    """
    subject = f"Blood Donation Approved - Thank You!"
    message = f"""
Dear {donor_name},

Thank you for your generous blood donation! Your donation has been APPROVED and added to our blood bank.

Details:
- Blood Group: {bloodgroup}
- Units Donated: {unit}

Your donation will help save lives. Thank you for being a hero!

Best regards,
Blood Bank Management Team
    """.strip()
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[donor_email],
            fail_silently=False,
        )
        logger.info(f"✅ Donation approval email sent to {donor_email}")
        return {"status": "success", "email": donor_email}
    
    except Exception as e:
        logger.error(f"❌ Failed to send donation approval email to {donor_email}: {e}")
        if self.request.retries >= self.max_retries:
            logger.critical(f"🚨 FINAL FAILURE: Could not send email to {donor_email} after {self.max_retries} retries")
        raise


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def send_donation_rejected_email(self, donor_email, donor_name, bloodgroup, reason=""):
    """
    Send email notification when blood donation is rejected.
    """
    subject = f"Blood Donation Update"
    message = f"""
Dear {donor_name},

Thank you for your willingness to donate blood. Unfortunately, we were unable to accept your donation at this time.

Details:
- Blood Group: {bloodgroup}
{f'- Reason: {reason}' if reason else ''}

Please don't be discouraged. You may be eligible to donate in the future.
Contact us for more information.

Best regards,
Blood Bank Management Team
    """.strip()
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[donor_email],
            fail_silently=False,
        )
        logger.info(f"✅ Donation rejection email sent to {donor_email}")
        return {"status": "success", "email": donor_email}
    
    except Exception as e:
        logger.error(f"❌ Failed to send donation rejection email to {donor_email}: {e}")
        if self.request.retries >= self.max_retries:
            logger.critical(f"🚨 FINAL FAILURE: Could not send email to {donor_email} after {self.max_retries} retries")
        raise
