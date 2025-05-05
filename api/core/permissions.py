# apps/school/api/permissions.py

from rest_framework import permissions


class IsSchoolAdmin(permissions.BasePermission):
    """
    Permission to only allow school admins of a specific school.
    """

    message = "You must be an admin of a school to perform this action."

    def has_permission(self, request, view):
        """Check if user is authenticated and is a school admin"""
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'school') and
            request.user.school is not None and
            hasattr(request.user, 'is_admin') and
            request.user.is_admin
        )

    def has_object_permission(self, request, view, obj):
        """Check if object belongs to user's school and user is admin"""
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'school') and
            request.user.school is not None and
            hasattr(request.user, 'is_admin') and
            request.user.is_admin and
            obj.school_id == request.user.school.id
        )
