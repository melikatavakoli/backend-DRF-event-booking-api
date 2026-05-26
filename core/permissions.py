from rest_framework import permissions


class IsAdminRole(permissions.BasePermission):
    """
    Allows access only to users with the 'A' (Admin) role.
    """

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and request.user.role == "A"
        )


class IsStaffOrAdminRole(permissions.BasePermission):
    """
    Allows access to 'A' (Admin) and 'S' (Staff) roles.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ["A", "S"]
        )
