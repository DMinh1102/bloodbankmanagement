"""
Rate limiting decorators for blood bank endpoints.

This module provides decorators to prevent API abuse and ensure fair usage
of blood bank system endpoints using Django's built-in cache framework.
"""

from functools import wraps
from django.shortcuts import render
from django_ratelimit.decorators import ratelimit
from django_ratelimit import ALL

def bloodbank_ratelimit(rate='10/m', method=ALL, key='ip', block=True):
    """
    Rate limit decorator for blood bank views using django-ratelimit.
    
    Args:
        rate: Rate limit string (e.g., '10/m' = 10 per minute)
        method: HTTP method to limit ('GET', 'POST', 'ALL' or list)
        key: Key to use for rate limiting:
            - 'ip': Limit by IP address
            - 'user': Limit by user ID (for authenticated users)
            - 'user_or_ip': Use user ID if authenticated, else IP
        block: If True, block requests that exceed limit and show error page
    """
    def decorator(view_func):
        @wraps(view_func)
        @ratelimit(key=key, rate=rate, method=method, block=False)
        def wrapped_view(request, *args, **kwargs):
            # Check if limit exceeded (set by django-ratelimit with block=False)
            if getattr(request, 'limited', False) and block:
                # Return custom rate limit error page
                context = {
                    'error_title': 'Too Many Requests',
                    'error_message': 'You have exceeded the rate limit. Please try again later.',
                    'retry_after': '1 minute'
                }
                return render(request, 'blood/rate_limit_error.html', context, status=429)
            
            return view_func(request, *args, **kwargs)
        
        return wrapped_view
    return decorator


# Predefined rate limiters for different use cases

def public_endpoint_limit(view_func):
    """
    Rate limit for public endpoints (e.g., blood stock query).
    Limit: 200 requests per minute per IP
    """
    return bloodbank_ratelimit(rate='200/m', key='ip')(view_func)


def donor_action_limit(view_func):
    """
    Rate limit for donor actions (e.g., blood donation, blood request).
    Limit: 50 requests per minute per user
    """
    return bloodbank_ratelimit(rate='50/m', key='user_or_ip')(view_func)


def patient_action_limit(view_func):
    """
    Rate limit for patient actions (e.g., blood request).
    Limit: 50 requests per minute per user
    """
    return bloodbank_ratelimit(rate='50/m', key='user_or_ip')(view_func)


def admin_action_limit(view_func):
    """
    Rate limit for admin actions (more lenient).
    Limit: 300 requests per minute per user
    """
    return bloodbank_ratelimit(rate='300/m', key='user')(view_func)


def strict_limit(view_func):
    """
    Strict rate limit for sensitive operations.
    Limit: 30 requests per minute per IP
    """
    return bloodbank_ratelimit(rate='30/m', key='ip')(view_func)

