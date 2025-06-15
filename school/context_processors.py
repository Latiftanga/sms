
from school.models import School


def school_context(request):
    """Add school information to all templates"""
    try:
        school = School.get_current_school()
        return {
            'school': school,
            'school_name': school.name,
            'school_code': school.code,
            'school_motto': school.motto,
            'school_colors': {
                'primary': school.primary_color,
                'secondary': school.secondary_color,
            }
        }
    except Exception:
        return {
            'school': None,
            'school_name': 'School Management System',
            'school_code': 'SCH',
            'school_motto': '',
        }
