from rest_framework import permissions

def get_role(user):
    return getattr(user, 'role', None)

class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow admin users to access.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and get_role(request.user) == 'ADMIN'


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated and get_role(request.user) == 'ADMIN'


class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if get_role(request.user) == 'ADMIN':
            return True
        return obj == request.user


class IsAdminOrStaff(permissions.BasePermission):

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
        
        role= get_role(request.user)
        # Admins have full access
        if role == 'ADMIN':
            return True
        
        # Staff can read
        if role == 'STAFF':
            request.method in permissions.SAFE_METHODS
            
        # Customers can only access their own data (checked in has_object_permission)
        if role == 'CUSTOMER':
            if view.action=='list':
                return False
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        role=get_role(request.user)

        if role == 'ADMIN':
            return True
        
        # Staff can only read
        if role == 'STAFF':
            return request.method in permissions.SAFE_METHODS
        
        # Customers can only view/update their own profile
        if role == 'CUSTOMER':
            return obj == request.user
        
        return False
