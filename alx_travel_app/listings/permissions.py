from rest_framework import permissions

class IsHostOrAdminUser(permissions.BasePermission):
    """
    Custom permission to allow only users with role 'host' or 'admin' to create listings.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        role = getattr(request.user, 'role', None)
        return request.user.is_authenticated and role in ['host', 'admin']
