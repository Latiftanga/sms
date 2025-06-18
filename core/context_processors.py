from school.models import School, AcademicYear, Term
from django import template
from django.utils.html import format_html
from django.urls import reverse
from school.models import Student


register = template.Library()


def school_context(request):
    """Add school context to all templates"""
    try:
        school = School.get_current_school()
        current_academic_year = AcademicYear.objects.filter(
            is_current=True).first()
        current_term = Term.objects.filter(is_current=True).first()

        return {
            'school': school,
            'current_academic_year': current_academic_year,
            'current_term': current_term,
        }
    except Exception:
        return {
            'school': None,
            'current_academic_year': None,
            'current_term': None,
        }


def student_stats(request):
    """Add basic student statistics to template context"""
    if request.user.is_authenticated and (request.user.is_admin or request.user.is_teacher):
        return {
            'total_students_count': Student.objects.filter(is_active=True).count(),
            'inactive_students_count': Student.objects.filter(is_active=False).count(),
        }
    return {}


@register.filter
def student_avatar_initials(student):
    """Get student initials for avatar"""
    if hasattr(student, 'first_name') and hasattr(student, 'last_name'):
        return f"{student.first_name[0].upper()}{student.last_name[0].upper()}"
    return "ST"


@register.filter
def student_status_badge(is_active):
    """Render student status as a badge"""
    if is_active:
        return format_html('<span class="badge badge-success">Active</span>')
    else:
        return format_html('<span class="badge bg-danger">Inactive</span>')


@register.filter
def student_class_display(student):
    """Display student's class with programme if available"""
    if not student.current_class:
        return "No Class"

    class_name = str(student.current_class)
    if student.current_class.programme:
        return f"{class_name} ({student.current_class.programme.code})"
    return class_name


@register.simple_tag
def student_detail_url(student):
    """Generate student detail URL"""
    return reverse('student:student_detail', kwargs={'pk': student.pk})


@register.inclusion_tag('student/tags/student_card.html')
def student_card(student, show_actions=True):
    """Render a student card component"""
    return {
        'student': student,
        'show_actions': show_actions
    }


@register.filter
def contact_display(student):
    """Display primary contact for student"""
    if student.email:
        return student.email
    elif student.phone:
        return student.phone
    elif student.guardian_phone:
        return student.guardian_phone
    return "No contact"


def school_theme(request):
    """Add school configuration and theme colors to all templates"""
    try:
        school = School.get_current_school()
        
        # Generate color variations from primary and secondary colors
        theme_colors = generate_theme_colors(school.primary_color, school.secondary_color)
        
        return {
            'school': school,
            'theme_colors': theme_colors,
            'school_primary_color': school.primary_color,
            'school_secondary_color': school.secondary_color,
        }
    except Exception:
        # Fallback to default colors if school not found
        return {
            'school': None,
            'theme_colors': generate_theme_colors('#1B5E20', '#2E7D32'),
            'school_primary_color': '#1B5E20',
            'school_secondary_color': '#2E7D32',
        }


def generate_theme_colors(primary_color, secondary_color):
    """Generate a complete color theme from primary and secondary colors"""
    from .utils import ColorThemeGenerator
    
    generator = ColorThemeGenerator(primary_color, secondary_color)
    
    return {
        'primary': primary_color,
        'primary_light': generator.lighten_color(primary_color, 0.1),
        'primary_dark': generator.darken_color(primary_color, 0.1),
        'primary_rgb': generator.hex_to_rgb(primary_color),
        
        'secondary': secondary_color,
        'secondary_light': generator.lighten_color(secondary_color, 0.1),
        'secondary_dark': generator.darken_color(secondary_color, 0.1),
        'secondary_rgb': generator.hex_to_rgb(secondary_color),
        
        'success': generator.generate_success_color(primary_color),
        'info': generator.generate_info_color(primary_color),
        'warning': generator.generate_warning_color(primary_color),
        'danger': generator.generate_danger_color(primary_color),
        
        'accent': generator.generate_accent_color(primary_color, secondary_color),
        'gradient': f"linear-gradient(135deg, {primary_color}, {secondary_color})",
        'gradient_light': f"linear-gradient(135deg, {generator.lighten_color(primary_color, 0.2)}, {generator.lighten_color(secondary_color, 0.2)})",
    }