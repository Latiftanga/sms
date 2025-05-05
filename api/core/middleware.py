# apps/core/middleware.py

from django.utils.deprecation import MiddlewareMixin
from threading import local

# Thread-local storage to hold current school
_school_thread_local = local()


def get_current_school():
    """Get the current school from thread-local storage"""
    return getattr(_school_thread_local, 'school', None)


def set_current_school(school):
    """Set the current school in thread-local storage"""
    _school_thread_local.school = school


class SchoolIsolationMiddleware(MiddlewareMixin):
    """
    Middleware that isolates each school by setting the current school
    in thread-local storage based on the authenticated user.
    """

    def process_request(self, request):
        """Process each request to set the current school"""
        # Clear any previous school
        set_current_school(None)

        # Set current school based on authenticated user
        if hasattr(request, 'user') and request.user.is_authenticated and hasattr(request.user, 'school'):
            set_current_school(request.user.school)

        return None
