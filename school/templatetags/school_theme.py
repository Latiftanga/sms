# File: school/templatetags/school_theme.py
from django import template
from django.utils.safestring import mark_safe
from django.conf import settings

register = template.Library()


@register.inclusion_tag('school/theme_colors.html')
def school_theme_css():
    """Include school theme CSS variables"""
    return {}


@register.simple_tag
def school_gradient(direction="135deg"):
    """Generate school gradient"""
    return mark_safe(f"linear-gradient({direction}, var(--school-primary), var(--school-secondary))")


@register.simple_tag
def school_color_rgb(color_name):
    """Get school color as RGB values"""
    color_map = {
        'primary': 'var(--school-primary-rgb)',
        'secondary': 'var(--school-secondary-rgb)',
    }
    return mark_safe(color_map.get(color_name, 'var(--school-primary-rgb)'))


@register.filter
def with_school_color(element_class, color_type="primary"):
    """Add school color to CSS class"""
    if color_type == "primary":
        return mark_safe(f"{element_class} school-primary-bg")
    elif color_type == "secondary":
        return mark_safe(f"{element_class} school-secondary-bg")
    return element_class
