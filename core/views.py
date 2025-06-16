# File: apps/core/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count

from school.models import (
    School, AcademicYear, Term,
    Subject, Class, Student, Teacher
)


@login_required
def dashboard_view(request):
    """Main dashboard view"""
    user = request.user
    school = School.get_current_school()
    
    # Get basic counts
    total_students = Student.objects.filter(is_active=True).count()
    total_teachers = Teacher.objects.filter(is_active=True).count()
    total_classes = Class.objects.count()
    total_subjects = Subject.objects.count()
    
    # Get current academic info
    current_academic_year = AcademicYear.objects.filter(is_current=True).first()
    current_term = Term.objects.filter(is_current=True).first()
    
    # Recent students (last 10)
    recent_students = Student.objects.filter(is_active=True).order_by('-created_at')[:10]
    
    # Class statistics
    class_stats = []
    for cls in Class.objects.all()[:5]:  # Top 5 classes
        student_count = cls.students.filter(is_active=True).count()
        class_stats.append({
            'class': cls,
            'student_count': student_count,
            'capacity': cls.capacity,
            'percentage': (student_count / cls.capacity * 100) if cls.capacity > 0 else 0
        })
    
    # Students by level
    students_by_level = Student.objects.filter(is_active=True).values(
        'current_class__level'
    ).annotate(count=Count('id')).order_by('current_class__level')
    
    # Students by programme
    students_by_programme = Student.objects.filter(
        is_active=True,
        current_class__programme__isnull=False
    ).values(
        'current_class__programme__name'
    ).annotate(count=Count('id')).order_by('-count')
    
    # Recent activity (simplified)
    recent_activity = []
    
    # Add recent student registrations
    for student in Student.objects.filter(is_active=True).order_by('-created_at')[:3]:
        recent_activity.append({
            'type': 'student_registered',
            'message': f'New student {student.get_full_name()} registered',
            'time': student.created_at,
            'icon': 'fas fa-user-plus',
            'color': 'success'
        })
    
    # Add recent class assignments
    for student in Student.objects.filter(
        current_class__isnull=False,
        is_active=True
    ).order_by('-updated_at')[:2]:
        recent_activity.append({
            'type': 'class_assigned',
            'message': f'{student.get_full_name()} assigned to {student.current_class}',
            'time': student.updated_at,
            'icon': 'fas fa-door-open',
            'color': 'info'
        })
    
    # Sort recent activity by time
    recent_activity.sort(key=lambda x: x['time'], reverse=True)
    recent_activity = recent_activity[:5]
    
    context = {
        'user': user,
        'school': school,
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_classes': total_classes,
        'total_subjects': total_subjects,
        'current_academic_year': current_academic_year,
        'current_term': current_term,
        'recent_students': recent_students,
        'class_stats': class_stats,
        'students_by_level': students_by_level,
        'students_by_programme': students_by_programme,
        'recent_activity': recent_activity,
        'title': 'Dashboard'
    }
    
    return render(request, 'core/dashboard.html', context)


def home_view(request):
    """Home page view - redirects to dashboard if logged in"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    return redirect('account:login')


@login_required
def profile_view(request):
    """User profile view"""
    user = request.user
    profile = user.get_profile()
    
    context = {
        'user': user,
        'profile': profile,
        'title': 'My Profile'
    }
    return render(request, 'core/profile.html', context)


# Mixins for view permissions
class AdminRequiredMixin:
    """Mixin for views that require admin access"""
    
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_authenticated and 
                (request.user.is_admin or request.user.is_superuser)):
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        return super().dispatch(request, *args, **kwargs)


class TeacherRequiredMixin:
    """Mixin for views that require teacher access"""
    
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_authenticated and 
                (request.user.is_teacher or request.user.is_admin or 
                 request.user.is_superuser)):
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        return super().dispatch(request, *args, **kwargs)