# context_processors.py
from django.conf import settings
from django.utils import timezone
from .models import School


def school_context(request):
    """
    Context processor to provide school information to all templates
    """
    context = {}

    try:
        # Get the first (and likely only) school
        school = School.objects.first()
        context['school'] = school

        if school:
            context['school_name'] = school.name
            context['school_logo'] = school.logo
            context['school_motto'] = school.motto
            context['school_is_active'] = school.is_active
        else:
            context['school_name'] = settings.SCHOOL_SETTINGS.get(
                'DEFAULT_SCHOOL_NAME', 'School Management System')
            context['school_logo'] = None
            context['school_motto'] = None
            context['school_is_active'] = True

    except Exception:
        # Fallback values if there's any error
        context['school'] = None
        context['school_name'] = settings.SCHOOL_SETTINGS.get(
            'DEFAULT_SCHOOL_NAME', 'School Management System')
        context['school_logo'] = None
        context['school_motto'] = None
        context['school_is_active'] = True

    # Add current date/time
    context['today'] = timezone.now().date()
    context['current_time'] = timezone.now()

    # Add academic year info
    current_date = timezone.now().date()
    academic_year_start = settings.SCHOOL_SETTINGS.get(
        'ACADEMIC_YEAR_START_MONTH', 9)

    if current_date.month >= academic_year_start:
        context['current_academic_year'] = f"{current_date.year}/{current_date.year + 1}"
    else:
        context['current_academic_year'] = f"{current_date.year - 1}/{current_date.year}"

    # Add user role information if user is authenticated
    if request.user.is_authenticated:
        context['user_role'] = get_user_role_display(request.user)
        context['user_permissions'] = get_user_permissions(request.user)

    return context


def get_user_role_display(user):
    """Get display name for user role"""
    if user.is_superuser:
        return "Superuser"
    elif user.is_admin:
        return "Administrator"
    elif user.is_teacher:
        return "Teacher"
    elif user.is_student:
        return "Student"
    else:
        return "User"


def get_user_permissions(user):
    """Get user permissions for template usage"""
    permissions = {
        'can_manage_school': user.is_superuser or user.is_admin or user.is_staff,
        'can_manage_students': user.is_superuser or user.is_admin or user.is_staff,
        'can_manage_teachers': user.is_superuser or user.is_admin or user.is_staff,
        'can_view_reports': user.is_superuser or user.is_admin or user.is_staff or user.is_teacher,
        'can_take_attendance': user.is_superuser or user.is_admin or user.is_staff or user.is_teacher,
        'can_enter_grades': user.is_superuser or user.is_admin or user.is_staff or user.is_teacher,
        'is_admin_or_staff': user.is_superuser or user.is_admin or user.is_staff,
        'is_teacher_or_above': user.is_superuser or user.is_admin or user.is_staff or user.is_teacher,
    }
    return permissions
