"""
Rate limiting decorators for blood bank endpoints.

This module provides decorators to prevent API abuse and ensure fair usage
of blood bank system endpoints using Django's built-in cache framework.
"""

from functools import wraps
from django.shortcuts import render
from django.core.cache import cache
import time
import hashlib

# ============================================================
# TOGGLE THIS FLAG TO DISABLE RATE LIMITING FOR TESTING
# ============================================================
DISABLE_RATE_LIMITING = False  # Set to False to re-enable rate limiting
OVERRIDE_RATE = None # Set to string e.g. '5/m' to override all limits for testing
# ============================================================


def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    return ip


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


def ratelimit(key='ip', rate='10/m', method='ALL', block=True):
    """
    Rate limiting decorator.

    Args:
        key: 'ip', 'user', or 'user_or_ip'
        rate: Rate limit string (e.g., '10/m' = 10 per minute, '5/s' = 5 per second)
        method: HTTP method to limit ('GET', 'POST', 'ALL')
        block: If True, block requests that exceed limit. If False, just mark request.limited=True
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            # Skip rate limiting if disabled globally
            if DISABLE_RATE_LIMITING:
                request.limited = False
                return view_func(request, *args, **kwargs)

            # Check if method matches
            if method != 'ALL' and request.method != method:
                return view_func(request, *args, **kwargs)

            # Determine effective rate (allow override for testing)
            effective_rate = OVERRIDE_RATE if OVERRIDE_RATE else rate

            # Parse rate
            # Format: "count/period" where period can be 's', 'm', 'h', 'd'
            try:
                limit_count, period_char = effective_rate.split('/')
                limit_count = int(limit_count)

                if period_char.lower().startswith('s'):
                    period_seconds = 1
                elif period_char.lower().startswith('m'):
                    period_seconds = 60
                elif period_char.lower().startswith('h'):
                    period_seconds = 3600
                elif period_char.lower().startswith('d'):
                    period_seconds = 86400
                else:
                    period_seconds = 60 # Default to minute
            except ValueError:
                # Fallback defaults
                limit_count = 100
                period_seconds = 60

            # Get client identifier
            client_id = get_client_identifier(request, key)

            # Construct a unique cache key
            # ratelimit:<view_name>:<client_id>:<method>
            # We add a time window component to the bucket to auto-expire
            # Simple fixed window algorithm
            current_time = int(time.time())
            time_window = current_time // period_seconds

            cache_key = f"rl:{view_func.__name__}:{client_id}:{method}:{time_window}"

            # Use cache.incr for atomic increment
            # If key doesn't exist, we set it.
            # safe pattern is get_or_set or add then incr.

            # Try to increment, if it fails (key doesn't exist), set it
            try:
                # In some backends incr returns the new value, in some it raises ValueError if key missing
                # In LocalMemoryCache (default for tests), it raises ValueError
                current_count = cache.incr(cache_key)
            except ValueError:
                cache.set(cache_key, 1, period_seconds)
                current_count = 1

            # Safety check if backend returns None for some reason
            if current_count is None:
                 cache.set(cache_key, 1, period_seconds)
                 current_count = 1


            # Check if limit exceeded
            if current_count > limit_count:
                request.limited = True

                if block:
                    # Return custom rate limit error page
                    context = {
                        'error_title': 'Too Many Requests',
                        'error_message': 'You have exceeded the rate limit. Please try again later.',
                        'retry_after': f'{period_seconds} seconds'
                    }
                    return render(request, 'blood/rate_limit_error.html', context, status=429)
            else:
                request.limited = False

            return view_func(request, *args, **kwargs)

        return wrapped_view
    return decorator


def bloodbank_ratelimit(rate, key):
    """
    Wrapper for specific bloodbank rate limits.
    """
    return ratelimit(key=key, rate=rate, method='ALL', block=True)


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
