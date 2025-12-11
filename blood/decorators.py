"""
Rate limiting decorators for blood bank endpoints.

This module provides decorators to prevent API abuse and ensure fair usage
of blood bank system endpoints using Django's built-in cache framework.
"""

from functools import wraps
from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import render
import time
import hashlib


def get_client_identifier(request, key_type='ip'):
    """
    Get unique identifier for rate limiting.
    
    Args:
        request: Django request object
        key_type: 'ip', 'user', or 'user_or_ip'
    
    Returns:
        Unique identifier string
    """
    if key_type == 'user' and request.user.is_authenticated:
        return f"user:{request.user.id}"
    elif key_type == 'user_or_ip':
        if request.user.is_authenticated:
            return f"user:{request.user.id}"
        return f"ip:{get_client_ip(request)}"
    else:  # ip
        return f"ip:{get_client_ip(request)}"


def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    return ip


def parse_rate(rate):
    """
    Parse rate string into count and period.
    
    Args:
        rate: String like '10/m', '100/h', '1000/d'
    
    Returns:
        Tuple of (count, period_seconds)
    """
    count, period = rate.split('/')
    count = int(count)
    
    period_map = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400,
    }
    
    period_seconds = period_map.get(period, 60)
    return count, period_seconds


def bloodbank_ratelimit(rate='10/m', method='ALL', key='ip', block=True):
    """
    Rate limit decorator for blood bank views.
    
    Args:
        rate: Rate limit string (e.g., '10/m' = 10 per minute, '100/h' = 100 per hour)
        method: HTTP method to limit ('GET', 'POST', 'ALL')
        key: Key to use for rate limiting:
            - 'ip': Limit by IP address (for anonymous users)
            - 'user': Limit by user ID (for authenticated users)
            - 'user_or_ip': Use user ID if authenticated, else IP
        block: If True, block requests that exceed limit
    """
    max_requests, period = parse_rate(rate)
    
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            # Check if method matches
            if method != 'ALL' and request.method != method:
                return view_func(request, *args, **kwargs)
            
            # Get client identifier
            client_id = get_client_identifier(request, key)
            cache_key = f"ratelimit:{view_func.__name__}:{client_id}"
            
            # Get current request count
            current_time = time.time()
            request_data = cache.get(cache_key, {'count': 0, 'reset_time': current_time + period})
            
            # Reset if period expired
            if current_time >= request_data['reset_time']:
                request_data = {'count': 0, 'reset_time': current_time + period}
            
            # Check if limit exceeded
            if request_data['count'] >= max_requests:
                if block:
                    # Mark request as limited
                    request.limited = True
                    
                    # Return custom rate limit error page
                    context = {
                        'error_title': 'Too Many Requests',
                        'error_message': 'You have exceeded the rate limit. Please try again later.',
                        'retry_after': '1 minute'
                    }
                    return render(request, 'blood/rate_limit_error.html', context, status=429)
            
            # Increment counter
            request_data['count'] += 1
            cache.set(cache_key, request_data, period)
            
            # Mark request as not limited
            request.limited = False
            
            return view_func(request, *args, **kwargs)
        
        return wrapped_view
    return decorator


# Predefined rate limiters for different use cases

def public_endpoint_limit(view_func):
    """
    Rate limit for public endpoints (e.g., blood stock query).
    Limit: 20 requests per minute per IP
    """
    return bloodbank_ratelimit(rate='20/m', key='ip')(view_func)


def donor_action_limit(view_func):
    """
    Rate limit for donor actions (e.g., blood donation, blood request).
    Limit: 5 requests per minute per user
    """
    return bloodbank_ratelimit(rate='5/m', key='user_or_ip')(view_func)


def patient_action_limit(view_func):
    """
    Rate limit for patient actions (e.g., blood request).
    Limit: 5 requests per minute per user
    """
    return bloodbank_ratelimit(rate='5/m', key='user_or_ip')(view_func)


def admin_action_limit(view_func):
    """
    Rate limit for admin actions (more lenient).
    Limit: 30 requests per minute per user
    """
    return bloodbank_ratelimit(rate='30/m', key='user')(view_func)


def strict_limit(view_func):
    """
    Strict rate limit for sensitive operations.
    Limit: 3 requests per minute per IP
    """
    return bloodbank_ratelimit(rate='3/m', key='ip')(view_func)

