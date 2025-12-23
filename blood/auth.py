"""
JWT Authentication module for Blood Bank Management API
Provides decorators and endpoints for JWT-based authentication
"""
import json
from functools import wraps

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate
from django.contrib.auth.models import User, Group

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.authentication import JWTAuthentication

from donor.models import Donor
from patient.models import Patient
from blood.constants import UserGroup


def jwt_required(view_func):
    """
    Decorator to require JWT authentication for API views.
    Validates the Bearer token and attaches the user to the request.
    
    Usage:
        @jwt_required
        def my_api_view(request):
            user = request.user  # Authenticated user
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        jwt_auth = JWTAuthentication()
        
        try:
            # Attempt to authenticate using JWT
            auth_result = jwt_auth.authenticate(request)
            
            if auth_result is None:
                return JsonResponse({
                    'success': False,
                    'error': 'Authentication required',
                    'detail': 'No valid authentication credentials provided. Include "Authorization: Bearer <token>" header.'
                }, status=401)
            
            user, token = auth_result
            request.user = user
            request.auth = token
            
            return view_func(request, *args, **kwargs)
            
        except InvalidToken as e:
            return JsonResponse({
                'success': False,
                'error': 'Invalid token',
                'detail': str(e)
            }, status=401)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': 'Authentication failed',
                'detail': str(e)
            }, status=401)
    
    return wrapper


def get_tokens_for_user(user):
    """Generate JWT tokens (access + refresh) for a user"""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def get_user_info(user):
    """Get user information including role"""
    user_info = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
    }
    
    # Determine user role
    if user.is_superuser:
        user_info['role'] = 'admin'
    elif user.groups.filter(name=UserGroup.DONOR).exists():
        user_info['role'] = 'donor'
        try:
            donor = Donor.objects.get(user=user)
            user_info['donor_id'] = donor.id
            user_info['bloodgroup'] = donor.bloodgroup
        except Donor.DoesNotExist:
            pass
    elif user.groups.filter(name=UserGroup.PATIENT).exists():
        user_info['role'] = 'patient'
        try:
            patient = Patient.objects.get(user=user)
            user_info['patient_id'] = patient.id
            user_info['bloodgroup'] = patient.bloodgroup
        except Patient.DoesNotExist:
            pass
    else:
        user_info['role'] = 'unknown'
    
    return user_info


@csrf_exempt
@require_http_methods(["POST"])
def api_login(request):
    """
    Login endpoint - authenticate user and return JWT tokens
    
    POST /api/auth/login/
    Body: {"username": "...", "password": "..."}
    
    Returns:
        - success: true/false
        - tokens: {access, refresh}
        - user: user info
    """
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return JsonResponse({
                'success': False,
                'error': 'Missing credentials',
                'detail': 'Both username and password are required'
            }, status=400)
        
        user = authenticate(username=username, password=password)
        
        if user is None:
            return JsonResponse({
                'success': False,
                'error': 'Invalid credentials',
                'detail': 'Username or password is incorrect'
            }, status=401)
        
        if not user.is_active:
            return JsonResponse({
                'success': False,
                'error': 'Account disabled',
                'detail': 'This account has been disabled'
            }, status=401)
        
        tokens = get_tokens_for_user(user)
        user_info = get_user_info(user)
        
        return JsonResponse({
            'success': True,
            'tokens': tokens,
            'user': user_info
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON',
            'detail': 'Request body must be valid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Login failed',
            'detail': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_register(request):
    """
    Register endpoint - create new donor or patient account
    
    POST /api/auth/register/
    Body: {
        "username": "...",
        "password": "...",
        "email": "...",
        "first_name": "...",
        "last_name": "...",
        "role": "donor" or "patient",
        "bloodgroup": "A+",
        "address": "...",
        "mobile": "...",
        // For patients only:
        "age": 25,
        "disease": "...",
        "doctorname": "..."
    }
    """
    try:
        data = json.loads(request.body)
        
        # Required fields
        username = data.get('username')
        password = data.get('password')
        email = data.get('email', '')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        role = data.get('role', 'donor').lower()
        
        # Profile fields
        bloodgroup = data.get('bloodgroup')
        address = data.get('address', '')
        mobile = data.get('mobile', '')
        
        # Validation
        if not username or not password:
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields',
                'detail': 'username and password are required'
            }, status=400)
        
        if not bloodgroup:
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields',
                'detail': 'bloodgroup is required'
            }, status=400)
        
        if role not in ['donor', 'patient']:
            return JsonResponse({
                'success': False,
                'error': 'Invalid role',
                'detail': 'role must be "donor" or "patient"'
            }, status=400)
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            return JsonResponse({
                'success': False,
                'error': 'Username taken',
                'detail': 'This username is already registered'
            }, status=400)
        
        # Create user
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        
        # Assign to group
        group_name = UserGroup.DONOR if role == 'donor' else UserGroup.PATIENT
        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)
        
        # Create profile
        if role == 'donor':
            Donor.objects.create(
                user=user,
                bloodgroup=bloodgroup,
                address=address,
                mobile=mobile
            )
        else:
            age = data.get('age', 0)
            disease = data.get('disease', '')
            doctorname = data.get('doctorname', '')
            
            Patient.objects.create(
                user=user,
                bloodgroup=bloodgroup,
                address=address,
                mobile=mobile,
                age=age,
                disease=disease,
                doctorname=doctorname
            )
        
        # Generate tokens
        tokens = get_tokens_for_user(user)
        user_info = get_user_info(user)
        
        return JsonResponse({
            'success': True,
            'message': f'{role.capitalize()} account created successfully',
            'tokens': tokens,
            'user': user_info
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON',
            'detail': 'Request body must be valid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Registration failed',
            'detail': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_token_refresh(request):
    """
    Token refresh endpoint - get new access token using refresh token
    
    POST /api/auth/refresh/
    Body: {"refresh": "..."}
    
    Returns:
        - success: true/false
        - access: new access token
    """
    try:
        data = json.loads(request.body)
        refresh_token = data.get('refresh')
        
        if not refresh_token:
            return JsonResponse({
                'success': False,
                'error': 'Missing refresh token',
                'detail': 'refresh token is required'
            }, status=400)
        
        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)
            
            return JsonResponse({
                'success': True,
                'access': access_token
            })
            
        except TokenError as e:
            return JsonResponse({
                'success': False,
                'error': 'Invalid refresh token',
                'detail': str(e)
            }, status=401)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON',
            'detail': 'Request body must be valid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Token refresh failed',
            'detail': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def api_me(request):
    """
    Get current user info endpoint
    
    GET /api/auth/me/
    Headers: Authorization: Bearer <access_token>
    
    Returns:
        - success: true/false
        - user: user info
    """
    user_info = get_user_info(request.user)
    
    return JsonResponse({
        'success': True,
        'user': user_info
    })
