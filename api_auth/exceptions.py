from rest_framework.views import exception_handler
from rest_framework.exceptions import Throttled
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    """Custom exception handler for more user-friendly throttling messages."""
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # Handle throttling exceptions specifically
    if isinstance(exc, Throttled):
        # Calculate wait time
        wait = getattr(exc, 'wait', None)
        
        error_data = {
            'error': 'Too many login attempts',
            'detail': 'Please try again later'
        }
        
        if wait:
            minutes, seconds = divmod(int(wait), 60)
            wait_msg = f"{minutes}m {seconds}s" if minutes else f"{seconds}s"
            error_data['detail'] = f'Please try again after {wait_msg}'
            error_data['wait_seconds'] = int(wait)
        
        return Response(error_data, status=status.HTTP_429_TOO_MANY_REQUESTS)
    
    return response