"""
Constants for Blood Bank Management System
Centralized configuration values for blood groups, statuses, and user groups.
"""

# Blood Groups
class BloodGroup:
    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"
    
    ALL_GROUPS = [
        A_POSITIVE,
        A_NEGATIVE,
        B_POSITIVE,
        B_NEGATIVE,
        AB_POSITIVE,
        AB_NEGATIVE,
        O_POSITIVE,
        O_NEGATIVE,
    ]
    
    CHOICES = [
        (A_POSITIVE, "A+"),
        (A_NEGATIVE, "A-"),
        (B_POSITIVE, "B+"),
        (B_NEGATIVE, "B-"),
        (AB_POSITIVE, "AB+"),
        (AB_NEGATIVE, "AB-"),
        (O_POSITIVE, "O+"),
        (O_NEGATIVE, "O-"),
    ]


# Request/Donation Status
class Status:
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    
    CHOICES = [
        (PENDING, "Pending"),
        (APPROVED, "Approved"),
        (REJECTED, "Rejected"),
    ]


# User Groups
class UserGroup:
    DONOR = "DONOR"
    PATIENT = "PATIENT"
    ADMIN = "ADMIN"
