from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def admin_or_teacher_required(view_func):
    """Decorator to require admin or teacher permissions"""
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not (request.user.is_admin or request.user.is_teacher):
            raise PermissionDenied(
                "You must be an admin or teacher to access this page.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def admin_required(view_func):
    """Decorator to require admin permissions only"""
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_admin:
            raise PermissionDenied("You must be an admin to access this page.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view
