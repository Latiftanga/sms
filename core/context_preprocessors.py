from . import views
from django.urls import path
from school.models import School, AcademicYear, Term


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
