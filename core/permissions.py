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
