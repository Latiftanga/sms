# File: student/templatetags/student_extras.py
from django import template
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, date
import json
import hashlib

from school.models import Student, Class, House, Programme

register = template.Library()


# =============================================================================
# FILTERS
# =============================================================================

@register.filter
def student_avatar_initials(student):
    """Get student initials for avatar display"""
    try:
        if hasattr(student, 'first_name') and hasattr(student, 'last_name'):
            first_initial = student.first_name[0].upper(
            ) if student.first_name else ''
            last_initial = student.last_name[0].upper(
            ) if student.last_name else ''
            return f"{first_initial}{last_initial}"
    except (AttributeError, IndexError):
        pass
    return "ST"


@register.filter
def student_status_badge(is_active):
    """Render student status as a colored badge"""
    if is_active:
        return format_html('<span class="badge badge-success"><i class="fas fa-check me-1"></i>Active</span>')
    else:
        return format_html('<span class="badge bg-danger"><i class="fas fa-times me-1"></i>Inactive</span>')


@register.filter
def student_class_display(student):
    """Display student's class with programme information"""
    try:
        if not hasattr(student, 'current_class') or not student.current_class:
            return format_html('<span class="text-muted">No Class Assigned</span>')

        class_name = str(student.current_class)
        if hasattr(student.current_class, 'programme') and student.current_class.programme:
            return format_html(
                '<span class="badge bg-primary">{}</span><br><small class="text-muted">{}</small>',
                class_name, student.current_class.programme.name
            )
        return format_html('<span class="badge bg-primary">{}</span>', class_name)
    except (AttributeError, TypeError):
        return format_html('<span class="text-muted">No Class</span>')


@register.filter
def contact_display(student):
    """Display primary contact for student (email or phone)"""
    try:
        if hasattr(student, 'email') and student.email:
            return format_html('<a href="mailto:{}" class="text-decoration-none"><i class="fas fa-envelope me-1"></i>{}</a>',
                               student.email, student.email)
        elif hasattr(student, 'phone') and student.phone:
            return format_html('<a href="tel:{}" class="text-decoration-none"><i class="fas fa-phone me-1"></i>{}</a>',
                               student.phone, student.phone)
        elif hasattr(student, 'guardian_phone') and student.guardian_phone:
            return format_html('<a href="tel:{}" class="text-decoration-none"><i class="fas fa-phone me-1"></i>{}</a><br><small class="text-muted">Guardian</small>',
                               student.guardian_phone, student.guardian_phone)
    except (AttributeError, TypeError):
        pass
    return format_html('<span class="text-muted">No contact available</span>')


@register.filter
def age_from_birthdate(birth_date):
    """Calculate age from birth date"""
    try:
        if not birth_date:
            return "Unknown"

        today = date.today()
        age = today.year - birth_date.year - \
            ((today.month, today.day) < (birth_date.month, birth_date.day))
        return f"{age} years"
    except (AttributeError, TypeError, ValueError):
        return "Unknown"


@register.filter
def guardian_contact_display(student):
    """Display guardian contact with relationship"""
    try:
        if not hasattr(student, 'guardian_name') or not student.guardian_name:
            return format_html('<span class="text-muted">Not provided</span>')

        contact_parts = [student.guardian_name]

        if hasattr(student, 'relationship_to_guardian') and student.relationship_to_guardian:
            contact_parts.append(f"({student.relationship_to_guardian})")

        contact_html = ' '.join(contact_parts)

        if hasattr(student, 'guardian_phone') and student.guardian_phone:
            contact_html += f'<br><small class="text-muted"><a href="tel:{student.guardian_phone}">{student.guardian_phone}</a></small>'

        return format_html(contact_html)
    except (AttributeError, TypeError):
        return format_html('<span class="text-muted">Not provided</span>')


@register.filter
def house_color_badge(house):
    """Display house name with its color"""
    try:
        if not house:
            return format_html('<span class="text-muted">No House</span>')

        color = getattr(house, 'color', '#6c757d')
        return format_html(
            '<span class="badge" style="background-color: {}; color: white;"><i class="fas fa-home me-1"></i>{}</span>',
            color, house.name
        )
    except (AttributeError, TypeError):
        return format_html('<span class="text-muted">No House</span>')


@register.filter
def student_avatar_color(student):
    """Generate consistent color for student avatar based on name"""
    try:
        if not student:
            return "#6c757d"

        # Generate color based on student name hash
        name = f"{getattr(student, 'first_name', '')}{getattr(student, 'last_name', '')}"
        if not name:
            return "#6c757d"

        colors = [
            "#007bff", "#28a745", "#dc3545", "#ffc107",
            "#17a2b8", "#6f42c1", "#e83e8c", "#fd7e14",
            "#20c997", "#6610f2", "#e91e63", "#ff9800"
        ]

        # Use hash to get consistent color
        hash_value = int(hashlib.md5(name.encode()).hexdigest(), 16)
        return colors[hash_value % len(colors)]
    except (AttributeError, TypeError):
        return "#6c757d"


@register.filter
def format_phone_number(phone):
    """Format phone number for display"""
    try:
        if not phone:
            return ""

        # Remove any non-digit characters
        digits = ''.join(filter(str.isdigit, str(phone)))

        # Format Ghana phone numbers
        if len(digits) == 10 and digits.startswith('0'):
            return f"{digits[:4]}-{digits[4:7]}-{digits[7:]}"
        elif len(digits) == 12 and digits.startswith('233'):
            return f"+{digits[:3]}-{digits[3:6]}-{digits[6:9]}-{digits[9:]}"
        elif len(digits) >= 10:
            # Generic formatting for long numbers
            return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"

        return phone
    except (AttributeError, TypeError, ValueError):
        return phone or ""


@register.filter
def days_since_created(student):
    """Calculate days since student was created"""
    try:
        if not hasattr(student, 'created_at') or not student.created_at:
            return "Unknown"

        delta = timezone.now() - student.created_at
        days = delta.days

        if days == 0:
            return "Today"
        elif days == 1:
            return "1 day ago"
        elif days < 7:
            return f"{days} days ago"
        elif days < 30:
            weeks = days // 7
            return f"{weeks} week{'s' if weeks > 1 else ''} ago"
        elif days < 365:
            months = days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
        else:
            years = days // 365
            return f"{years} year{'s' if years > 1 else ''} ago"
    except (AttributeError, TypeError):
        return "Unknown"


@register.filter
def student_progress_percentage(student):
    """Calculate completion percentage of student profile"""
    try:
        if not student:
            return 0

        fields_to_check = [
            'first_name', 'last_name', 'email', 'phone', 'address',
            'current_class', 'house', 'guardian_name', 'guardian_phone',
            'date_of_birth', 'ghana_card_number'
        ]

        completed_fields = 0
        for field in fields_to_check:
            try:
                value = getattr(student, field, None)
                if value:
                    completed_fields += 1
            except AttributeError:
                continue

        return int((completed_fields / len(fields_to_check)) * 100)
    except (AttributeError, TypeError, ZeroDivisionError):
        return 0


@register.filter
def student_age_group(student):
    """Categorize student by age group"""
    try:
        if not hasattr(student, 'date_of_birth') or not student.date_of_birth:
            return "Unknown"

        today = date.today()
        age = today.year - student.date_of_birth.year

        if age <= 15:
            return "Junior (≤15)"
        elif age <= 17:
            return "Senior (16-17)"
        else:
            return "Adult (18+)"
    except (AttributeError, TypeError, ValueError):
        return "Unknown"


@register.filter
def student_academic_year(student):
    """Get student's current academic year"""
    try:
        if not hasattr(student, 'year_admitted') or not student.year_admitted:
            return "Unknown"

        current_year = timezone.now().year
        years_in_school = current_year - student.year_admitted

        if years_in_school < 0:
            return "Future Student"
        elif years_in_school == 0:
            return "1st Year"
        elif years_in_school == 1:
            return "2nd Year"
        elif years_in_school == 2:
            return "3rd Year"
        elif years_in_school == 3:
            return "4th Year (Repeat)"
        else:
            return "Alumni"
    except (AttributeError, TypeError):
        return "Unknown"


@register.filter
def can_edit_student(user, student):
    """Check if user can edit the student"""
    try:
        if not user or not user.is_authenticated:
            return False

        if user.is_admin or user.is_superuser:
            return True

        if user.is_teacher:
            return True

        # Students can only edit their own profile (limited fields)
        if user.is_student and hasattr(user, 'student_profile'):
            return user.student_profile == student

        return False
    except (AttributeError, TypeError):
        return False


@register.filter
def can_delete_student(user, student):
    """Check if user can delete/deactivate the student"""
    try:
        if not user or not user.is_authenticated:
            return False

        return user.is_admin or user.is_superuser
    except (AttributeError, TypeError):
        return False


@register.filter
def student_full_contact(student):
    """Get full contact information formatted"""
    try:
        contacts = []

        if hasattr(student, 'email') and student.email:
            contacts.append(
                f'<i class="fas fa-envelope me-1"></i>{student.email}')

        if hasattr(student, 'phone') and student.phone:
            contacts.append(
                f'<i class="fas fa-phone me-1"></i>{student.phone}')

        if hasattr(student, 'guardian_phone') and student.guardian_phone:
            guardian_name = getattr(student, 'guardian_name', 'Guardian')
            contacts.append(
                f'<i class="fas fa-user-friends me-1"></i>{guardian_name}: {student.guardian_phone}')

        if contacts:
            return format_html('<br>'.join(contacts))
        else:
            return format_html('<span class="text-muted">No contact information</span>')
    except (AttributeError, TypeError):
        return format_html('<span class="text-muted">No contact information</span>')


# =============================================================================
# SIMPLE TAGS
# =============================================================================

@register.simple_tag
def student_detail_url(student):
    """Generate student detail URL"""
    try:
        return reverse('student:student_detail', kwargs={'pk': student.pk})
    except (AttributeError, TypeError):
        return '#'


@register.simple_tag
def student_edit_url(student):
    """Generate student edit URL"""
    try:
        return reverse('student:student_edit', kwargs={'pk': student.pk})
    except (AttributeError, TypeError):
        return '#'


@register.simple_tag
def student_delete_url(student):
    """Generate student delete URL"""
    try:
        return reverse('student:student_delete', kwargs={'pk': student.pk})
    except (AttributeError, TypeError):
        return '#'


@register.simple_tag
def student_count_by_class(class_obj):
    """Get student count for a specific class"""
    try:
        if not class_obj:
            return 0
        return Student.objects.filter(current_class=class_obj, is_active=True).count()
    except (AttributeError, TypeError):
        return 0


@register.simple_tag
def student_count_by_house(house_obj):
    """Get student count for a specific house"""
    try:
        if not house_obj:
            return 0
        return Student.objects.filter(house=house_obj, is_active=True).count()
    except (AttributeError, TypeError):
        return 0


@register.simple_tag
def get_recent_students(limit=5):
    """Get recently added students"""
    try:
        return Student.objects.filter(is_active=True).select_related(
            'current_class', 'house', 'current_class__programme'
        ).order_by('-created_at')[:limit]
    except (AttributeError, TypeError):
        return Student.objects.none()


@register.simple_tag
def get_students_without_class():
    """Get count of students without assigned class"""
    try:
        return Student.objects.filter(is_active=True, current_class__isnull=True).count()
    except (AttributeError, TypeError):
        return 0


@register.simple_tag
def get_students_without_house():
    """Get count of students without assigned house"""
    try:
        return Student.objects.filter(is_active=True, house__isnull=True).count()
    except (AttributeError, TypeError):
        return 0


@register.simple_tag
def students_by_gender_chart_data():
    """Generate chart data for students by gender"""
    try:
        male_count = Student.objects.filter(is_active=True, gender='M').count()
        female_count = Student.objects.filter(
            is_active=True, gender='F').count()

        return mark_safe(json.dumps({
            'labels': ['Male', 'Female'],
            'data': [male_count, female_count],
            'backgroundColor': ['#36A2EB', '#FF6384']
        }))
    except Exception:
        return mark_safe('{"labels": [], "data": [], "backgroundColor": []}')


@register.simple_tag
def students_by_level_chart_data():
    """Generate chart data for students by level"""
    try:
        levels_data = Student.objects.filter(is_active=True).values(
            'current_class__level'
        ).annotate(count=Count('id')).order_by('current_class__level')

        labels = []
        data = []

        for item in levels_data:
            if item['current_class__level']:
                labels.append(f"SHS {item['current_class__level']}")
                data.append(item['count'])

        return mark_safe(json.dumps({
            'labels': labels,
            'data': data,
            'backgroundColor': ['#667eea', '#f093fb', '#4facfe', '#43e97b']
        }))
    except Exception:
        return mark_safe('{"labels": [], "data": [], "backgroundColor": []}')


@register.simple_tag
def students_by_house_chart_data():
    """Generate chart data for students by house"""
    try:
        houses_data = Student.objects.filter(is_active=True).values(
            'house__name'
        ).annotate(count=Count('id')).order_by('house__name')

        labels = []
        data = []

        for item in houses_data:
            labels.append(item['house__name'] or 'No House')
            data.append(item['count'])

        return mark_safe(json.dumps({
            'labels': labels,
            'data': data,
            'backgroundColor': ['#667eea', '#f093fb', '#4facfe', '#43e97b', '#f5576c', '#38f9d7']
        }))
    except Exception:
        return mark_safe('{"labels": [], "data": [], "backgroundColor": []}')


@register.simple_tag
def student_bulk_action_url(action):
    """Generate URL for bulk student actions"""
    urls = {
        'export': 'student:bulk_export',
        'promote': 'student:promotion',
        'deactivate': 'student:bulk_deactivate',
    }

    try:
        url_name = urls.get(action)
        if url_name:
            return reverse(url_name)
    except:
        pass
    return '#'


@register.simple_tag
def total_students_count():
    """Get total active students count"""
    try:
        return Student.objects.filter(is_active=True).count()
    except:
        return 0


@register.simple_tag
def inactive_students_count():
    """Get total inactive students count"""
    try:
        return Student.objects.filter(is_active=False).count()
    except:
        return 0


@register.simple_tag
def students_by_programme_data():
    """Get students grouped by programme"""
    try:
        return Student.objects.filter(is_active=True).values(
            'current_class__programme__name'
        ).annotate(count=Count('id')).order_by('current_class__programme__name')
    except:
        return []


@register.simple_tag
def students_admitted_this_year():
    """Get count of students admitted this academic year"""
    try:
        current_year = timezone.now().year
        return Student.objects.filter(
            is_active=True,
            year_admitted=current_year
        ).count()
    except:
        return 0


# =============================================================================
# INCLUSION TAGS
# =============================================================================

@register.inclusion_tag('student/tags/student_card.html')
def student_card(student, show_actions=True, card_class=""):
    """Render a reusable student card component"""
    return {
        'student': student,
        'show_actions': show_actions,
        'card_class': card_class
    }


@register.inclusion_tag('student/tags/student_table_row.html')
def student_table_row(student, show_checkbox=True):
    """Render a student table row component"""
    return {
        'student': student,
        'show_checkbox': show_checkbox
    }


@register.inclusion_tag('student/tags/student_stats_widget.html')
def student_stats_widget():
    """Render student statistics widget"""
    try:
        total_students = Student.objects.filter(is_active=True).count()
        male_students = Student.objects.filter(
            is_active=True, gender='M').count()
        female_students = Student.objects.filter(
            is_active=True, gender='F').count()
        houses_count = House.objects.count()
        classes_count = Class.objects.count()

        return {
            'total_students': total_students,
            'male_students': male_students,
            'female_students': female_students,
            'houses_count': houses_count,
            'classes_count': classes_count
        }
    except:
        return {
            'total_students': 0,
            'male_students': 0,
            'female_students': 0,
            'houses_count': 0,
            'classes_count': 0
        }


@register.inclusion_tag('student/tags/student_search_form.html')
def student_search_form(request, classes=None, houses=None, programmes=None):
    """Render student search form component"""
    try:
        if not classes:
            classes = Class.objects.all().order_by('level', 'name')
        if not houses:
            houses = House.objects.all().order_by('name')
        if not programmes:
            programmes = Programme.objects.all().order_by('name')

        return {
            'request': request,
            'classes': classes,
            'houses': houses,
            'programmes': programmes
        }
    except:
        return {
            'request': request,
            'classes': [],
            'houses': [],
            'programmes': []
        }


@register.inclusion_tag('student/tags/student_bulk_actions.html')
def student_bulk_actions():
    """Render bulk actions toolbar"""
    return {}


@register.inclusion_tag('student/tags/student_filter_sidebar.html')
def student_filter_sidebar(request):
    """Render student filter sidebar"""
    try:
        classes = Class.objects.all().order_by('level', 'name')
        houses = House.objects.all().order_by('name')
        programmes = Programme.objects.all().order_by('name')
        years = Student.objects.values_list(
            'year_admitted', flat=True
        ).distinct().order_by('-year_admitted')

        return {
            'request': request,
            'classes': classes,
            'houses': houses,
            'programmes': programmes,
            'years': years
        }
    except:
        return {
            'request': request,
            'classes': [],
            'houses': [],
            'programmes': [],
            'years': []
        }


# =============================================================================
# CONTEXT TAGS
# =============================================================================

@register.simple_tag(takes_context=True)
def query_string(context, **kwargs):
    """Generate query string for pagination while preserving filters"""
    try:
        request = context.get('request')
        if not request:
            return ""

        query_dict = request.GET.copy()

        for key, value in kwargs.items():
            if value is None:
                query_dict.pop(key, None)
            else:
                query_dict[key] = value

        return f"?{query_dict.urlencode()}" if query_dict else ""
    except:
        return ""


@register.simple_tag(takes_context=True)
def current_url_with_params(context, **kwargs):
    """Get current URL with additional parameters"""
    try:
        request = context.get('request')
        if not request:
            return ""

        query_dict = request.GET.copy()
        query_dict.update(kwargs)

        return f"{request.path}?{query_dict.urlencode()}" if query_dict else request.path
    except:
        return ""


# =============================================================================
# ASSIGNMENT TAGS (for complex operations)
# =============================================================================

@register.simple_tag
def get_student_statistics():
    """Get comprehensive student statistics"""
    try:
        return {
            'total_active': Student.objects.filter(is_active=True).count(),
            'total_inactive': Student.objects.filter(is_active=False).count(),
            'male_count': Student.objects.filter(is_active=True, gender='M').count(),
            'female_count': Student.objects.filter(is_active=True, gender='F').count(),
            'without_class': Student.objects.filter(is_active=True, current_class__isnull=True).count(),
            'without_house': Student.objects.filter(is_active=True, house__isnull=True).count(),
            'this_year_admissions': Student.objects.filter(
                is_active=True,
                year_admitted=timezone.now().year
            ).count(),
        }
    except:
        return {
            'total_active': 0,
            'total_inactive': 0,
            'male_count': 0,
            'female_count': 0,
            'without_class': 0,
            'without_house': 0,
            'this_year_admissions': 0,
        }


@register.simple_tag
def get_class_distribution():
    """Get student distribution across classes"""
    try:
        return Student.objects.filter(is_active=True).values(
            'current_class__name',
            'current_class__level',
            'current_class__programme__name'
        ).annotate(
            student_count=Count('id')
        ).order_by('current_class__level', 'current_class__name')
    except:
        return []


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def safe_getattr(obj, attr, default=None):
    """Safely get attribute from object"""
    try:
        return getattr(obj, attr, default)
    except (AttributeError, TypeError):
        return default


def safe_format_html(template, *args, **kwargs):
    """Safely format HTML"""
    try:
        return format_html(template, *args, **kwargs)
    except:
        return mark_safe('<span class="text-muted">Error</span>')
