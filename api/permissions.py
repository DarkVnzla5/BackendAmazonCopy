from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow admin users to access.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'ADMIN'


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow read-only access to everyone,
    but only admins can create, update, or delete.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated and request.user.role == 'ADMIN'


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or admins to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Admins can do anything
        if request.user.role == 'ADMIN':
            return True
        # Users can only access their own profile
        return obj == request.user


class IsAdminOrStaff(permissions.BasePermission):
    """
    Custom permission to allow admin and staff users to access.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['ADMIN', 'STAFF']


class CanManageUsers(permissions.BasePermission):
    """
    Permission for user management:
    - Admins can do everything
    - Staff can view users
    - Customers can only view/update their own profile
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admins have full access
        if request.user.role == 'ADMIN':
            return True
        
        # Staff can read
        if request.user.role == 'STAFF' and request.method in permissions.SAFE_METHODS:
            return True
        
        # Customers can only access their own data (checked in has_object_permission)
        if request.user.role == 'CUSTOMER':
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        # Admins can do anything
        if request.user.role == 'ADMIN':
            return True
        
        # Staff can only read
        if request.user.role == 'STAFF':
            return request.method in permissions.SAFE_METHODS
        
        # Customers can only view/update their own profile
        if request.user.role == 'CUSTOMER':
            if request.method in permissions.SAFE_METHODS or request.method in ['PUT', 'PATCH']:
                return obj == request.user
        
        return False
