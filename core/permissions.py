from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def role_required(allowed_roles):
    """Decorator to check if user has required role"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')

            user = request.user
            user_roles = []

            if user.is_superuser or user.is_admin:
                user_roles.append('admin')
            if user.is_teacher:
                user_roles.append('teacher')
            if user.is_student:
                user_roles.append('student')

            if any(role in allowed_roles for role in user_roles):
                return view_func(request, *args, **kwargs)
            else:
                messages.error(
                    request, "You don't have permission to access this page.")
                return redirect('dashboard:dashboard_redirect')

        return wrapper
    return decorator


class StudentAccessMixin(UserPassesTestMixin):
    """Base mixin for student-related views requiring authentication"""

    def test_func(self):
        return self.request.user.is_authenticated

    def handle_no_permission(self):
        raise PermissionDenied("You must be logged in to access this page.")


class AdminOrTeacherRequiredMixin(UserPassesTestMixin):
    """Mixin requiring admin or teacher permissions"""

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (user.is_admin or user.is_teacher)

    def handle_no_permission(self):
        raise PermissionDenied(
            "You must be an admin or teacher to access this page.")


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin requiring admin permissions only"""

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.is_admin

    def handle_no_permission(self):
        raise PermissionDenied("You must be an admin to access this page.")
