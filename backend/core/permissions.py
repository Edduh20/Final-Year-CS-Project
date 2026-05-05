from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        return getattr(request.user, "role", None) in ["admin", "superadmin"]


class IsLandOfficer(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        return getattr(request.user, "role", None) in ["land_officer", "admin", "superadmin"]


class IsLegalOfficer(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        return getattr(request.user, "role", None) in ["legal_officer", "admin", "superadmin"]


class IsOwnerOrOfficer(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser or request.user.is_staff:
            return True

        if not hasattr(request.user, 'profile'):
            return False

        user_profile = request.user.profile

        if user_profile.role in ['admin', 'superadmin', 'land_officer', 'legal_officer']:
            return True

        if hasattr(obj, 'owner') and obj.owner == user_profile:
            return True

        if hasattr(obj, 'uploaded_by') and obj.uploaded_by == user_profile:
            return True

        if hasattr(obj, 'user') and obj.user == user_profile:
            return True

        return False


class ReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS