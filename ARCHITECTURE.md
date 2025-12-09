# Layered Architecture Documentation

## Overview

This Blood Bank Management System now follows a **clean layered architecture** pattern with clear separation of concerns. The refactoring maintains backward compatibility while significantly improving code organization, testability, and maintainability.

## Architecture Layers

```
┌─────────────────────────────────────┐
│     Presentation Layer (Views)      │  ← HTTP Request/Response, Templates
├─────────────────────────────────────┤
│      Service Layer (Services)       │  ← Business Logic, Orchestration
├─────────────────────────────────────┤
│   Repository Layer (Repositories)   │  ← Data Access, ORM Queries
├─────────────────────────────────────┤
│       Model Layer (Models)          │  ← Domain Models, Database Schema
└─────────────────────────────────────┘
```

### 1. Presentation Layer (`views.py`)
**Responsibility**: Handle HTTP requests and responses
- Receive user input from forms
- Call appropriate service methods
- Render templates with data
- Handle authentication/authorization decorators

**Example**:
```python
def admin_dashboard_view(request):
    stocks = BloodStockService.get_all_stocks_dict()
    context = {
        'totaldonors': DonorService.get_total_donors_count(),
        'totalbloodunit': BloodStockService.get_total_units(),
    }
    return render(request, 'blood/admin_dashboard.html', context=context)
```

### 2. Service Layer (`services.py`)
**Responsibility**: Contain business logic and orchestrate operations
- Implement business rules
- Coordinate between multiple repositories
- Handle transactions
- Validate business constraints

**Example**:
```python
class BloodRequestService:
    @staticmethod
    def approve_request(request_id: int) -> Tuple[bool, Optional[str]]:
        # Business logic for approving blood request
        request = BloodRequestRepository.get_by_id(request_id)
        is_available, available_units = BloodStockService.check_stock_availability(
            request.bloodgroup, request.unit
        )
        if not is_available:
            return (False, f"Only {available_units} Unit Available")
        
        BloodStockService.remove_blood_from_stock(request.bloodgroup, request.unit)
        BloodRequestRepository.update_status(request_id, Status.APPROVED)
        return (True, None)
```

### 3. Repository Layer (`repositories.py`)
**Responsibility**: Abstract data access operations
- Encapsulate ORM queries
- Provide clean interface for data operations
- Hide database implementation details

**Example**:
```python
class DonorRepository:
    @staticmethod
    def get_by_user_id(user_id: int) -> Optional[Donor]:
        try:
            return Donor.objects.get(user_id=user_id)
        except Donor.DoesNotExist:
            return None
```

### 4. Model Layer (`models.py`)
**Responsibility**: Define domain models
- Django ORM models (unchanged from original)
- Database schema definitions

## Project Structure

```
bloodbankmanagement/
├── blood/                      # Main app
│   ├── constants.py           # ✨ NEW: Centralized constants
│   ├── exceptions.py          # ✨ NEW: Custom exceptions
│   ├── repositories.py        # ✨ NEW: Data access layer
│   ├── services.py            # ✨ NEW: Business logic layer
│   ├── views.py               # ✅ REFACTORED: Thin controllers
│   ├── models.py              # Unchanged
│   └── forms.py               # Unchanged
│
├── donor/                      # Donor app
│   ├── repositories.py        # ✨ NEW: Data access layer
│   ├── services.py            # ✨ NEW: Business logic layer
│   ├── views.py               # ✅ REFACTORED: Thin controllers
│   ├── models.py              # Unchanged
│   └── forms.py               # Unchanged
│
└── patient/                    # Patient app
    ├── repositories.py        # ✨ NEW: Data access layer
    ├── services.py            # ✨ NEW: Business logic layer
    ├── views.py               # ✅ REFACTORED: Thin controllers
    ├── models.py              # Unchanged
    └── forms.py               # Unchanged
```

## Key Components

### Constants (`blood/constants.py`)
Centralized configuration values:
- `BloodGroup`: All blood group types (A+, A-, B+, etc.)
- `Status`: Request/donation statuses (Pending, Approved, Rejected)
- `UserGroup`: User group names (DONOR, PATIENT, ADMIN)

### Exceptions (`blood/exceptions.py`)
Custom exceptions for better error handling:
- `InsufficientBloodStockError`: Raised when stock is insufficient
- `DonorNotFoundError`: Raised when donor doesn't exist
- `PatientNotFoundError`: Raised when patient doesn't exist
- `BloodRequestNotFoundError`: Raised when request doesn't exist

### Services

#### Blood App Services
- **BloodStockService**: Manage blood inventory
  - `initialize_stock_if_needed()`
  - `get_all_stocks_dict()`
  - `update_stock_unit()`
  - `add_blood_to_stock()`
  - `remove_blood_from_stock()`

- **BloodRequestService**: Handle blood requests
  - `get_pending_requests()`
  - `approve_request()`
  - `reject_request()`
  - `get_request_stats_for_donor()`
  - `get_request_stats_for_patient()`

- **BloodDonationService**: Handle donations
  - `get_all_donations()`
  - `approve_donation()`
  - `reject_donation()`

#### Donor App Services
- **DonorService**: Manage donors
  - `create_donor()`
  - `update_donor()`
  - `delete_donor()`
  - `get_donor_by_user()`

- **DonationService**: Manage donations
  - `create_donation()`
  - `get_donation_history()`

#### Patient App Services
- **PatientService**: Manage patients
  - `create_patient()`
  - `update_patient()`
  - `delete_patient()`
  - `get_patient_by_user()`

## Benefits of This Architecture

### 1. **Separation of Concerns**
Each layer has a single, well-defined responsibility:
- Views handle HTTP
- Services handle business logic
- Repositories handle data access

### 2. **Testability**
Business logic can be unit tested independently:
```python
# Test service without touching database or HTTP
def test_approve_request_with_insufficient_stock():
    success, error = BloodRequestService.approve_request(request_id)
    assert success == False
    assert "Only" in error
```

### 3. **Reusability**
Services can be reused across different views or even APIs:
```python
# Same service used in web view and API endpoint
donor = DonorService.get_donor_by_user(request.user)
```

### 4. **Maintainability**
Changes to business logic don't affect views:
- Modify stock calculation logic → Only change service
- Add new validation rule → Only change service
- Change database query → Only change repository

### 5. **Flexibility**
Easy to swap implementations:
- Replace ORM with raw SQL → Only change repositories
- Add caching → Only change repositories
- Add logging → Only change services

## Migration Notes

### What Changed
- ✅ All business logic moved from views to services
- ✅ All database queries moved to repositories
- ✅ Magic strings replaced with constants
- ✅ Custom exceptions added for better error handling

### What Stayed the Same
- ✅ Django models (no database changes)
- ✅ URLs and routing
- ✅ Templates
- ✅ Forms
- ✅ User-facing functionality

### Backward Compatibility
All existing functionality works exactly as before. This is purely an internal code organization refactoring.

## Usage Examples

### Creating a Blood Request
```python
# Old way (in views.py)
blood_request = request_form.save(commit=False)
blood_request.bloodgroup = request_form.cleaned_data['bloodgroup']
donor = models.Donor.objects.get(user_id=request.user.id)
blood_request.request_by_donor = donor
blood_request.save()

# New way (using services)
donor = DonorService.get_donor_by_user_id(request.user.id)
BloodRequestService.create_request(
    patient_name=request_form.cleaned_data['patient_name'],
    patient_age=request_form.cleaned_data['patient_age'],
    reason=request_form.cleaned_data['reason'],
    bloodgroup=request_form.cleaned_data['bloodgroup'],
    unit=request_form.cleaned_data['unit'],
    request_by_donor=donor
)
```

### Approving a Donation
```python
# Old way (in views.py)
donation = dmodels.BloodDonate.objects.get(id=pk)
stock = models.Stock.objects.get(bloodgroup=donation.bloodgroup)
stock.unit = stock.unit + donation.unit
stock.save()
donation.status = 'Approved'
donation.save()

# New way (using services)
BloodDonationService.approve_donation(pk)
```

## Best Practices

1. **Always use services in views** - Never access repositories or models directly from views
2. **Keep views thin** - Views should only handle HTTP concerns
3. **Use constants** - Never hardcode strings like "Pending" or "A+"
4. **Handle exceptions** - Use custom exceptions for business rule violations
5. **Type hints** - Services and repositories use type hints for better IDE support

## Future Enhancements

This architecture makes it easy to add:
- REST APIs (reuse existing services)
- GraphQL endpoints (reuse existing services)
- Background tasks (call services from Celery tasks)
- Caching layer (add to repositories)
- Logging and monitoring (add to services)
- Unit tests (test services independently)
