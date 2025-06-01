# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from django.core.paginator import Paginator
import json
import logging

from .models import User, School
from .forms import LoginForm, SchoolSettingsForm

# Set up logging
logger = logging.getLogger(__name__)


def is_admin_or_staff(user):
    """Check if user is admin or staff"""
    return user.is_authenticated and (user.is_admin or user.is_staff or user.is_superuser)


def login_view(request):
    """Handle user login"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data.get('remember_me', False)

            user = authenticate(request, username=username, password=password)

            if user is not None:
                if user.is_active:
                    login(request, user)

                    # Set session expiry based on remember me
                    if not remember_me:
                        # Session expires when browser closes
                        request.session.set_expiry(0)
                    else:
                        request.session.set_expiry(settings.SESSION_COOKIE_AGE)

                    # Log successful login
                    logger.info(f"Successful login for user: {username}")

                    # Role-based redirect
                    next_url = request.GET.get('next', 'dashboard')

                    # Add welcome message based on role
                    if user.is_superuser:
                        messages.success(request, f'Welcome back, Superuser!')
                    elif user.is_admin or user.is_staff:
                        messages.success(
                            request, f'Welcome back, Administrator!')
                    elif user.is_teacher:
                        messages.success(request, f'Welcome back, Teacher!')
                    elif user.is_student:
                        messages.success(request, f'Welcome back, Student!')
                    else:
                        messages.success(request, f'Welcome back!')

                    return redirect(next_url)
                else:
                    logger.warning(
                        f"Login attempt for inactive user: {username}")
                    messages.error(
                        request, 'Your account has been deactivated. Please contact the administrator.')
            else:
                logger.warning(
                    f"Failed login attempt for username: {username}")
                messages.error(request, 'Invalid username or password.')
        else:
            logger.warning(
                f"Invalid login form submission from IP: {request.META.get('REMOTE_ADDR')}")
    else:
        form = LoginForm()

    return render(request, 'core/login.html', {'form': form})


def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('login')


@login_required
def dashboard(request):
    """Main dashboard view"""
    try:
        # Get school statistics
        context = {
            'user': request.user,
            'total_students': User.objects.filter(is_student=True, is_active=True).count(),
            'total_teachers': User.objects.filter(is_teacher=True, is_active=True).count(),
            'total_classes': 24,  # You can update this based on your models
            'total_subjects': 15,  # You can update this based on your models
            'today': timezone.now().date(),
        }

        # Add role-specific information
        if request.user.is_admin or request.user.is_staff:
            # Get recent registrations
            context['recent_students'] = User.objects.filter(
                is_student=True,
                is_active=True
            ).order_by('-date_joined')[:5]

        elif request.user.is_teacher:
            # Add teacher-specific context
            # You can populate this based on your models
            context['my_classes'] = []

        elif request.user.is_student:
            # Add student-specific context
            # You can populate this based on your models
            context['my_subjects'] = []

        return render(request, 'dashboard/dashboard.html', context)

    except Exception as e:
        logger.error(f"Dashboard error for user {request.user.username}: {e}")
        messages.error(
            request, 'An error occurred while loading the dashboard.')
        context = {
            'user': request.user,
            'total_students': 0,
            'total_teachers': 0,
            'total_classes': 0,
            'total_subjects': 0,
            'today': timezone.now().date(),
        }
        return render(request, 'core/dashboard.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
def school_settings(request):
    """School settings management"""
    try:
        # Get the first school (assuming single school setup)
        school = School.objects.first()
        if not school:
            # Create a default school for T. I. Ahmadiyya SHS Wa
            with transaction.atomic():
                school = School.objects.create(
                    name="T. I. Ahmadiyya Senior High School, Wa",
                    school_type="shs",
                    ownership="mission",
                    region="upper_west",
                    district="Wa Municipal",
                    town="Wa",
                    headmaster_name="",
                    email="info@ahmadiyyashs-wa.edu.gh",
                    phone_primary="",
                    motto="Love for All, Hatred for None",
                    is_active=True,
                )
                logger.info(f"Created default school: {school.name}")

    except Exception as e:
        logger.error(f'Error accessing school settings: {e}')
        messages.error(request, f'Error accessing school settings: {e}')
        return redirect('dashboard')

    if request.method == 'POST':
        form = SchoolSettingsForm(request.POST, request.FILES, instance=school)
        if form.is_valid():
            try:
                with transaction.atomic():
                    updated_school = form.save()
                    logger.info(
                        f"School settings updated by {request.user.username}")
                    messages.success(
                        request, 'School settings updated successfully!')
                    return redirect('school_settings')
            except ValidationError as e:
                logger.warning(f"Validation error in school settings: {e}")
                messages.error(request, f'Validation error: {e}')
            except Exception as e:
                logger.error(f"Error saving school settings: {e}")
                messages.error(
                    request, 'An error occurred while saving. Please try again.')
        else:
            # Log form errors for debugging
            for field, errors in form.errors.items():
                for error in errors:
                    logger.warning(f"Form validation error - {field}: {error}")
            messages.error(request, 'Please correct the errors below.')
            logger.warning(
                f"Form validation failed for user {request.user.username}")
    else:
        form = SchoolSettingsForm(instance=school)

    return render(request, 'core/school_settings.html', {
        'form': form,
        'school': school
    })


@login_required
@user_passes_test(is_admin_or_staff)
@require_http_methods(["POST"])
def update_school_contact(request):
    """AJAX endpoint for updating school contact info"""
    try:
        school = School.objects.first()
        if not school:
            return JsonResponse({'success': False, 'error': 'School not found'})

        data = json.loads(request.body)

        # Update contact fields
        if 'email' in data:
            school.email = data['email']
        if 'phone_primary' in data:
            school.phone_primary = data['phone_primary']
        if 'phone_secondary' in data:
            school.phone_secondary = data['phone_secondary']
        if 'website' in data:
            school.website = data['website']

        school.full_clean()  # Validate
        school.save()

        return JsonResponse({'success': True, 'message': 'Contact information updated successfully'})

    except ValidationError as e:
        return JsonResponse({'success': False, 'error': str(e)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Unexpected error: {e}'})


@ login_required
@ user_passes_test(is_admin_or_staff)
@ require_http_methods(["POST"])
def toggle_school_status(request):
    """AJAX endpoint for toggling school active status"""
    try:
        school = School.objects.first()
        if not school:
            return JsonResponse({'success': False, 'error': 'School not found'})

        school.is_active = not school.is_active
        school.save()

        status = "activated" if school.is_active else "deactivated"
        return JsonResponse({
            'success': True,
            'message': f'School {status} successfully',
            'is_active': school.is_active
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error: {e}'})


@ login_required
def profile_view(request):
    """User profile view"""
    return render(request, 'core/profile.html', {'user': request.user})


# Additional utility views
@ login_required
def check_user_role(request):
    """API endpoint to check user role for frontend"""
    return JsonResponse({
        'is_admin': request.user.is_admin,
        'is_staff': request.user.is_staff,
        'is_teacher': request.user.is_teacher,
        'is_student': request.user.is_student,
        'is_superuser': request.user.is_superuser,
        'username': request.user.username,
        'email': request.user.email or '',
        'is_active': request.user.is_active,
    })


@ login_required
def get_school_info(request):
    """API endpoint to get school information"""
    try:
        school = School.objects.first()
        if not school:
            return JsonResponse({'success': False, 'error': 'School not found'})

        school_data = {
            'name': school.name,
            'school_type': school.get_school_type_display(),
            'ownership': school.get_ownership_display(),
            'region': school.get_region_display(),
            'district': school.district,
            'town': school.town,
            'email': school.email,
            'phone_primary': school.phone_primary,
            'phone_secondary': school.phone_secondary or '',
            'website': school.website or '',
            'motto': school.motto or '',
            'is_active': school.is_active,
            'has_boarding': school.has_boarding,
            'logo_url': school.logo.url if school.logo else None,
        }

        return JsonResponse({'success': True, 'school': school_data})

    except Exception as e:
        logger.error(f"Error getting school info: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@ login_required
def change_password(request):
    """Handle password change"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            current_password = data.get('current_password')
            new_password = data.get('new_password')
            confirm_password = data.get('confirm_password')

            # Validate current password
            if not request.user.check_password(current_password):
                return JsonResponse({'success': False, 'error': 'Current password is incorrect'})

            # Validate new password
            if new_password != confirm_password:
                return JsonResponse({'success': False, 'error': 'New passwords do not match'})

            if len(new_password) < 8:
                return JsonResponse({'success': False, 'error': 'Password must be at least 8 characters long'})

            # Change password
            request.user.set_password(new_password)
            request.user.save()

            logger.info(f"Password changed for user: {request.user.username}")
            return JsonResponse({'success': True, 'message': 'Password changed successfully'})

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
        except Exception as e:
            logger.error(
                f"Error changing password for {request.user.username}: {e}")
            return JsonResponse({'success': False, 'error': 'An error occurred'})

    return JsonResponse({'success': False, 'error': 'Method not allowed'})


@ login_required
@ user_passes_test(is_admin_or_staff)
def debug_info(request):
    """Debug information view for administrators"""
    if not settings.DEBUG:
        return JsonResponse({'error': 'Debug mode is disabled'})

    debug_data = {
        'django_version': __import__('django').get_version(),
        'python_version': __import__('sys').version,
        'user_info': {
            'username': request.user.username,
            'is_admin': request.user.is_admin,
            'is_staff': request.user.is_staff,
            'is_superuser': request.user.is_superuser,
        },
        'school_exists': School.objects.exists(),
        'total_users': User.objects.count(),
        'settings_info': {
            'auth_user_model': settings.AUTH_USER_MODEL,
            'time_zone': settings.TIME_ZONE,
            'media_url': settings.MEDIA_URL,
        }
    }

    return JsonResponse(debug_data)


@ login_required
@ user_passes_test(is_admin_or_staff)
def user_management(request):
    """User management view for admins"""
    user_type = request.GET.get('type', 'all')
    search = request.GET.get('search', '')

    # Filter users based on type
    users = User.objects.all()

    if user_type == 'teachers':
        users = users.filter(is_teacher=True)
    elif user_type == 'students':
        users = users.filter(is_student=True)
    elif user_type == 'admins':
        users = users.filter(is_admin=True)

    # Search functionality
    if search:
        users = users.filter(username__icontains=search)

    # Pagination
    paginator = Paginator(users, 25)  # Show 25 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'users': page_obj,
        'user_type': user_type,
        'search': search,
        'total_users': users.count(),
    }

    return render(request, 'core/user_management.html', context)
