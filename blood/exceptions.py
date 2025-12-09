"""
Custom exceptions for Blood Bank Management System
"""


class BloodBankException(Exception):
    """Base exception for blood bank operations"""
    pass


class InsufficientBloodStockError(BloodBankException):
    """Raised when there is not enough blood in stock for a request"""
    def __init__(self, bloodgroup, requested_units, available_units):
        self.bloodgroup = bloodgroup
        self.requested_units = requested_units
        self.available_units = available_units
        super().__init__(
            f"Insufficient stock for {bloodgroup}. "
            f"Requested: {requested_units} units, Available: {available_units} units"
        )


class InvalidBloodGroupError(BloodBankException):
    """Raised when an invalid blood group is provided"""
    def __init__(self, bloodgroup):
        self.bloodgroup = bloodgroup
        super().__init__(f"Invalid blood group: {bloodgroup}")


class DonorNotFoundError(BloodBankException):
    """Raised when a donor is not found"""
    def __init__(self, user_id=None, donor_id=None):
        self.user_id = user_id
        self.donor_id = donor_id
        super().__init__(f"Donor not found (user_id={user_id}, donor_id={donor_id})")


class PatientNotFoundError(BloodBankException):
    """Raised when a patient is not found"""
    def __init__(self, user_id=None, patient_id=None):
        self.user_id = user_id
        self.patient_id = patient_id
        super().__init__(f"Patient not found (user_id={user_id}, patient_id={patient_id})")


class BloodRequestNotFoundError(BloodBankException):
    """Raised when a blood request is not found"""
    def __init__(self, request_id):
        self.request_id = request_id
        super().__init__(f"Blood request not found (id={request_id})")


class BloodDonationNotFoundError(BloodBankException):
    """Raised when a blood donation is not found"""
    def __init__(self, donation_id):
        self.donation_id = donation_id
        super().__init__(f"Blood donation not found (id={donation_id})")
