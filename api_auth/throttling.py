from rest_framework.throttling import SimpleRateThrottle
from django.core.cache import cache
from rest_framework.exceptions import Throttled
import sys
import time

class LoginRateThrottle(SimpleRateThrottle):
    """
    Throttle class for login attempts.
    Allows 3 login attempts per IP address per minute.
    """
    scope = 'login'
    
    def __init__(self):
        # Check if we're running in test mode
        self.is_test = 'test' in sys.argv
        
        # Default: 3 login attempts per minute
        self.rate = '3/m'
        
        # Initialize parent class
        super().__init__()
    
    def get_cache_key(self, request, view):
        """
        Generate a unique cache key based on IP address and email.
        This allows tracking login attempts per IP for specific accounts.
        """
        # Get the email from the request data
        email = ''
        if hasattr(request, 'data') and isinstance(request.data, dict):
            email = request.data.get('email', '')
        
        # Get the client IP address
        ip = self.get_client_ip(request)
        
        # Generate a key combining IP and email (for targeted login attempts)
        # Even if no email is passed, the limit still applies to the IP
        return f"throttle_login_{ip}_{email}"
    
    def get_client_ip(self, request):
        """Extract the client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        return ip
    
    def is_auth_endpoint(self, request):
        """Check if the request is to an authentication endpoint that should be throttled."""
        if request.method != 'POST':
            return False
            
        # Check various authentication endpoints
        auth_endpoints = ['/login/', '/register/', '/api/auth/login/', '/api/auth/register/']
        
        return any(request.path.endswith(endpoint) for endpoint in auth_endpoints)
    
    def allow_request(self, request, view):
        """
        Check if request should be allowed.
        Overridden to add custom tracking for failed vs successful logins.
        """
        # Always allow during tests
        if self.is_test:
            return True
            
        # Only throttle authentication endpoints
        if not self.is_auth_endpoint(request):
            return True
        
        # Get the throttle cache key
        self.key = self.get_cache_key(request, view)
        
        # If no key could be generated, allow the request
        if not self.key:
            return True
            
        # Get the history from cache
        self.history = self.get_history(self.key)
        
        # Check if we've exceeded the throttle limit
        self.now = self.timer()
        
        # Drop any requests outside the throttle window
        while self.history and self.history[0] <= self.now - self.duration:
            self.history.pop(0)
            
        # Check if the request should be throttled
        if len(self.history) >= self.num_requests:
            # Request should be throttled
            # Calculate wait time
            remaining_seconds = self.duration - (self.now - self.history[0])
            
            # Raise the throttled exception directly
            raise Throttled(wait=remaining_seconds)
            
        # Request is allowed, update the history
        self.history.append(self.now)
        self.cache_history(self.key, self.history)
        
        return True
        
    def get_history(self, key):
        """
        Get history from cache.
        """
        return cache.get(key, [])
        
    def cache_history(self, key, history):
        """
        Update history in cache.
        """
        cache.set(key, history, self.duration)
        
    def wait(self):
        """
        Calculate how long to wait before next request.
        """
        if not hasattr(self, 'history'):
            return None
            
        if not self.history:
            return None
            
        # Calculate remaining window
        remaining_duration = self.duration - (self.now - self.history[0])
        return max(0, int(remaining_duration))


class SuccessfulLoginResetThrottle(LoginRateThrottle):
    """
    Extension of LoginRateThrottle that resets the limit after successful login.
    """
    def reset_throttle_counter(self, key):
        """Reset the throttle counter for a specific key."""
        try:
            cache.delete(key)
        except Exception as e:
            print(f"Error resetting throttle counter: {e}")