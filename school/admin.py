from django.contrib import admin
from school.models import School


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'phone', 'email', 'established_year']
    fieldsets = [
        ('Basic Information', {
            'fields': ['name', 'code', 'address', 'phone', 'email', 'website']
        }),
        ('School Details', {
            'fields': ['motto', 'established_year', 'logo']
        }),
        ('Administration', {
            'fields': ['headmaster_name', 'assistant_headmaster_name']
        }),
        ('Academic Settings', {
            'fields': ['academic_year_start_month', 'terms_per_year'],
            'classes': ['collapse']
        }),
        ('Branding', {
            'fields': ['primary_color', 'secondary_color'],
            'classes': ['collapse']
        }),
    ]

    def has_add_permission(self, request):
        # Only allow one school record
        return not School.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Don't allow deleting the school record
        return False
