from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.contrib import messages
from core.permissions import role_required
from school.models import (
    School, AcademicYear, Term,
    Subject, Class, Student, Teacher
)


def home_view(request):
    """Home page view - redirects to dashboard if logged in"""
    if not request.user.is_authenticated:
        redirect_url = 'account:login'
        return redirect(redirect_url)
    user = request.user
    if user.is_superuser or user.is_admin:
        return redirect('admin:admin_dashboard')
    elif user.is_teacher:
        return redirect('teacher:teacher_dashboard')
    elif user.is_student:
        return redirect('student:student_dashboard')
    else:
        messages.error(
            request, "No role assigned. Please contact administrator.")
        return redirect('account:login')


@login_required
def admin_dashboard(request):
    """Main dashboard view"""
    user = request.user
    school = School.get_current_school()

    # Get basic counts
    total_students = Student.objects.filter(is_active=True).count()
    total_teachers = Teacher.objects.filter(is_active=True).count()
    total_classes = Class.objects.count()
    total_subjects = Subject.objects.count()

    # Get current academic info
    current_academic_year = AcademicYear.objects.filter(
        is_current=True).first()
    current_term = Term.objects.filter(is_current=True).first()

    # Recent students (last 10)
    recent_students = Student.objects.filter(
        is_active=True).order_by('-created_at')[:10]

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

    return render(request, 'core/dashboard/admin.html', context)


@role_required(['teacher'])
def teacher_dashboard(request):
    """Teacher dashboard"""

    user = request.user
    school = School.get_current_school()
    current_academic_year = AcademicYear.objects.filter(
        is_current=True).first()
    current_term = Term.objects.filter(is_current=True).first()

    # Get teacher profile
    teacher_profile = None
    if hasattr(user, 'teacher_profile'):
        teacher_profile = user.teacher_profile

    # Get classes taught by this teacher
    taught_classes = []
    total_students = 0
    if teacher_profile:
        taught_classes = Class.objects.filter(class_teacher=teacher_profile)
        total_students = Student.objects.filter(
            current_class__in=taught_classes,
            is_active=True
        ).count()

    # Get subjects taught
    subjects_taught = []
    if teacher_profile:
        subjects_taught = teacher_profile.subjects.all()

    # Quick stats
    stats = {
        'classes_taught': taught_classes.count(),
        'total_students': total_students,
        'subjects_taught': subjects_taught.count(),
    }

    # Recent activities (placeholder for future features)
    recent_activities = []

    context = {
        'title': 'Teacher Dashboard',
        'school': school,
        'current_academic_year': current_academic_year,
        'current_term': current_term,
        'teacher_profile': teacher_profile,
        'taught_classes': taught_classes,
        'subjects_taught': subjects_taught,
        'stats': stats,
        'recent_activities': recent_activities,
    }

    return render(request, 'dashboard/teacher/dashboard.html', context)


@role_required(['student'])
def student_dashboard(request):
    """Student dashboard"""

    user = request.user
    school = School.get_current_school()
    current_academic_year = AcademicYear.objects.filter(
        is_current=True).first()
    current_term = Term.objects.filter(is_current=True).first()

    # Get student profile
    student_profile = None
    if hasattr(user, 'student_profile'):
        student_profile = user.student_profile

    # Get class information
    current_class = None
    classmates_count = 0
    class_teacher = None
    if student_profile and student_profile.current_class:
        current_class = student_profile.current_class
        classmates_count = Student.objects.filter(
            current_class=current_class,
            is_active=True
        ).exclude(id=student_profile.id).count()
        class_teacher = current_class.class_teacher

    # Get house information
    house = None
    house_mates_count = 0
    if student_profile and student_profile.house:
        house = student_profile.house
        house_mates_count = Student.objects.filter(
            house=house,
            is_active=True
        ).exclude(id=student_profile.id).count()

    # Quick stats
    stats = {
        'academic_year': current_academic_year.year if current_academic_year else 'Not Set',
        'current_term': current_term.get_term_number_display() if current_term else 'Not Set',
        'classmates': classmates_count,
        'house_mates': house_mates_count,
    }

    # Recent activities (placeholder for future features)
    recent_activities = []

    context = {
        'title': 'Student Dashboard',
        'school': school,
        'current_academic_year': current_academic_year,
        'current_term': current_term,
        'student_profile': student_profile,
        'current_class': current_class,
        'class_teacher': class_teacher,
        'house': house,
        'stats': stats,
        'recent_activities': recent_activities,
    }

    return render(request, 'dashboard/student/dashboard.html', context)


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
