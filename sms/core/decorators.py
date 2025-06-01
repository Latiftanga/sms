# sms/decorators.py
from core.models import School
from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from functools import wraps
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
import logging

logger = logging.getLogger(__name__)


# Permission checking functions
def is_superuser(user):
    """Check if user is superuser"""
    return user.is_authenticated and user.is_superuser


def is_admin_user(user):
    """Check if user is admin or superuser"""
    return user.is_authenticated and (user.is_superuser or getattr(user, 'is_admin', False))


def is_teacher_user(user):
    """Check if user is teacher, admin, or superuser"""
    return user.is_authenticated and (
        user.is_superuser or
        getattr(user, 'is_admin', False) or
        getattr(user, 'is_teacher', False)
    )


def is_student_user(user):
    """Check if user is student"""
    return user.is_authenticated and getattr(user, 'is_student', False)


def can_manage_schools(user):
    """Check if user can manage school configurations"""
    return user.is_authenticated and (
        user.is_superuser or
        getattr(user, 'is_admin', False)
    )


def can_view_schools(user):
    """Check if user can view school information"""
    return user.is_authenticated and (
        user.is_superuser or
        getattr(user, 'is_admin', False) or
        getattr(user, 'is_teacher', False)
    )


# Function-based view decorators
def superuser_required(view_func=None, redirect_url=None, message=None):
    """
    Decorator for views that require superuser access
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('admin:login')

            if not is_superuser(request.user):
                if message:
                    messages.error(request, message)
                else:
                    messages.error(
                        request, "You don't have permission to access this page.")

                if redirect_url:
                    return redirect(redirect_url)
                return redirect('sms:dashboard')

            return view_func(request, *args, **kwargs)
        return _wrapped_view

    if view_func:
        return decorator(view_func)
    return decorator


def admin_required(view_func=None, redirect_url=None, message=None):
    """
    Decorator for views that require admin access
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('admin:login')

            if not is_admin_user(request.user):
                if message:
                    messages.error(request, message)
                else:
                    messages.error(
                        request, "You need admin privileges to access this page.")

                if redirect_url:
                    return redirect(redirect_url)
                return redirect('sms:dashboard')

            return view_func(request, *args, **kwargs)
        return _wrapped_view

    if view_func:
        return decorator(view_func)
    return decorator


def teacher_required(view_func=None, redirect_url=None, message=None):
    """
    Decorator for views that require teacher access or higher
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('admin:login')

            if not is_teacher_user(request.user):
                if message:
                    messages.error(request, message)
                else:
                    messages.error(
                        request, "You need teacher privileges to access this page.")

                if redirect_url:
                    return redirect(redirect_url)
                return redirect('sms:dashboard')

            return view_func(request, *args, **kwargs)
        return _wrapped_view

    if view_func:
        return decorator(view_func)
    return decorator


def school_manager_required(view_func=None, redirect_url=None, message=None):
    """
    Decorator for views that require school management permissions
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('admin:login')

            if not can_manage_schools(request.user):
                if message:
                    messages.error(request, message)
                else:
                    messages.error(
                        request, "You don't have permission to manage school configurations.")

                if redirect_url:
                    return redirect(redirect_url)
                return redirect('sms:dashboard')

            return view_func(request, *args, **kwargs)
        return _wrapped_view

    if view_func:
        return decorator(view_func)
    return decorator


def ajax_required(view_func):
    """
    Decorator for AJAX-only views
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'This endpoint requires AJAX'}, status=400)
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def api_permission_required(permission_func, error_message=None):
    """
    Decorator for API views that require specific permissions
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({'error': 'Authentication required'}, status=401)

            if not permission_func(request.user):
                error_msg = error_message or 'Permission denied'
                return JsonResponse({'error': error_msg}, status=403)

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


# Class-based view mixins
class SuperuserRequiredMixin(UserPassesTestMixin):
    """Mixin that requires superuser access"""

    def test_func(self):
        return is_superuser(self.request.user)

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('admin:login')

        messages.error(
            self.request, "You don't have permission to access this page.")
        return redirect('sms:dashboard')


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin that requires admin access"""

    def test_func(self):
        return is_admin_user(self.request.user)

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('admin:login')

        messages.error(
            self.request, "You need admin privileges to access this page.")
        return redirect('sms:dashboard')


class TeacherRequiredMixin(UserPassesTestMixin):
    """Mixin that requires teacher access or higher"""

    def test_func(self):
        return is_teacher_user(self.request.user)

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('admin:login')

        messages.error(
            self.request, "You need teacher privileges to access this page.")
        return redirect('sms:dashboard')


class SchoolManagerRequiredMixin(UserPassesTestMixin):
    """Mixin that requires school management permissions"""

    def test_func(self):
        return can_manage_schools(self.request.user)

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('admin:login')

        messages.error(
            self.request, "You don't have permission to manage school configurations.")
        return redirect('sms:dashboard')


class AjaxRequiredMixin:
    """Mixin for AJAX-only views"""

    def dispatch(self, request, *args, **kwargs):
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'This endpoint requires AJAX'}, status=400)
        return super().dispatch(request, *args, **kwargs)


# sms/permissions.py


class SchoolPermissions:
    """Custom permissions for school management"""

    PERMISSIONS = [
        ('view_school_config', 'Can view school configuration'),
        ('add_school_config', 'Can add school configuration'),
        ('change_school_config', 'Can change school configuration'),
        ('delete_school_config', 'Can delete school configuration'),
        ('manage_school_bulk', 'Can perform bulk operations on schools'),
        ('import_school_data', 'Can import school data'),
        ('export_school_data', 'Can export school data'),
        ('view_school_analytics', 'Can view school analytics'),
        ('manage_school_users', 'Can manage school users'),
        ('configure_school_settings', 'Can configure school settings'),
    ]

    @classmethod
    def create_custom_permissions(cls):
        """Create custom permissions for school management"""
        content_type = ContentType.objects.get_for_model(School)

        created_permissions = []
        for codename, name in cls.PERMISSIONS:
            permission, created = Permission.objects.get_or_create(
                codename=codename,
                content_type=content_type,
                defaults={'name': name}
            )
            if created:
                created_permissions.append(permission)

        return created_permissions

    @classmethod
    def assign_admin_permissions(cls, user):
        """Assign all school management permissions to admin user"""
        content_type = ContentType.objects.get_for_model(School)
        permissions = Permission.objects.filter(
            content_type=content_type,
            codename__in=[perm[0] for perm in cls.PERMISSIONS]
        )
        user.user_permissions.add(*permissions)

    @classmethod
    def assign_teacher_permissions(cls, user):
        """Assign read-only permissions to teacher user"""
        content_type = ContentType.objects.get_for_model(School)
        read_permissions = Permission.objects.filter(
            content_type=content_type,
            codename__in=['view_school_config', 'view_school_analytics']
        )
        user.user_permissions.add(*read_permissions)

    @classmethod
    def has_school_permission(cls, user, permission_codename):
        """Check if user has specific school permission"""
        if user.is_superuser:
            return True

        return user.has_perm(f'sms.{permission_codename}')


def check_school_permission(permission_codename):
    """
    Decorator factory for checking school permissions
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('admin:login')

            if not SchoolPermissions.has_school_permission(request.user, permission_codename):
                messages.error(
                    request, f"You don't have permission: {permission_codename}")
                return redirect('sms:dashboard')

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


class SchoolPermissionMixin(UserPassesTestMixin):
    """Generic mixin for checking school permissions"""
    permission_required = None

    def test_func(self):
        if not self.permission_required:
            raise ValueError("permission_required must be set")

        return SchoolPermissions.has_school_permission(
            self.request.user,
            self.permission_required
        )

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('admin:login')

        messages.error(
            self.request,
            f"You don't have permission: {self.permission_required}"
        )
        return redirect('sms:dashboard')


# Logging decorator for sensitive operations
def log_school_operation(operation_type):
    """
    Decorator to log school management operations
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            try:
                result = view_func(request, *args, **kwargs)

                # Log successful operation
                logger.info(
                    f"School {operation_type} - User: {request.user.username}, "
                    f"IP: {request.META.get('REMOTE_ADDR')}, "
                    f"Args: {args}, Kwargs: {kwargs}"
                )

                return result

            except Exception as e:
                # Log failed operation
                logger.error(
                    f"Failed school {operation_type} - User: {request.user.username}, "
                    f"IP: {request.META.get('REMOTE_ADDR')}, "
                    f"Error: {str(e)}, Args: {args}, Kwargs: {kwargs}"
                )
                raise

        return _wrapped_view
    return decorator


# Rate limiting decorator (basic implementation)
def rate_limit(max_requests=5, window_seconds=60):
    """
    Basic rate limiting decorator
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # This is a basic implementation
            # In production, use Django-ratelimit or Redis

            from django.core.cache import cache

            key = f"rate_limit_{request.user.id}_{view_func.__name__}"
            current_requests = cache.get(key, 0)

            if current_requests >= max_requests:
                return JsonResponse(
                    {'error': 'Rate limit exceeded. Try again later.'},
                    status=429
                )

            cache.set(key, current_requests + 1, window_seconds)
            return view_func(request, *args, **kwargs)

        return _wrapped_view
    return decorator
