from rest_framework import permissions

class IsPetugas(permissions.BasePermission):
    """
    Custom permission to only allow petugas users to access.
    """
    message = "You must be a petugas to access this resource."

    def has_permission(self, request, view):
        # Check if the user is authenticated and is a petugas
        user = request.user
        if not user or not user.is_authenticated:
            return False
            
        try:
            # Check if the user has a petugas profile
            petugas = user.petugas
            return True
        except AttributeError:
            return False
        
class IsAdmin(permissions.BasePermission):
    """
    Custom permission to only allow admin users (superusers) to access.
    """
    message = "You must be an admin to access this resource."

    def has_permission(self, request, view):
        # Check if the user is authenticated and is a superuser
        return request.user and request.user.is_authenticated and request.user.is_superuser