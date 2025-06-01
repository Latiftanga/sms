# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from core.models import User, School


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User Admin"""
    list_display = ('username', 'email', 'user_type_display',
                    'is_active', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_teacher',
                   'is_student', 'is_admin')
    search_fields = ('username', 'email')
    ordering = ('username',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('email',)}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('User Type', {
            'fields': ('is_admin', 'is_teacher', 'is_student'),
            'description': 'Select the user type. Only one should be selected.'
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email', 'is_teacher', 'is_student', 'is_admin'),
        }),
    )

    def user_type_display(self, obj):
        """Display user type with colored badges"""
        if obj.is_superuser:
            return format_html('<span style="color: #dc3545; font-weight: bold;">Superuser</span>')
        elif obj.is_admin:
            return format_html('<span style="color: #fd7e14; font-weight: bold;">Admin</span>')
        elif obj.is_teacher:
            return format_html('<span style="color: #20c997; font-weight: bold;">Teacher</span>')
        elif obj.is_student:
            return format_html('<span style="color: #0d6efd; font-weight: bold;">Student</span>')
        else:
            return format_html('<span style="color: #6c757d;">Regular User</span>')

    user_type_display.short_description = 'User Type'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related()

    def save_model(self, request, obj, form, change):
        """Ensure only one user type is selected"""
        user_types = [obj.is_admin, obj.is_teacher, obj.is_student]
        if sum(user_types) > 1:
            # Reset all and keep the last selected one
            if form.cleaned_data.get('is_admin'):
                obj.is_teacher = obj.is_student = False
            elif form.cleaned_data.get('is_teacher'):
                obj.is_admin = obj.is_student = False
            elif form.cleaned_data.get('is_student'):
                obj.is_admin = obj.is_teacher = False

        super().save_model(request, obj, form, change)


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    """School Admin"""
    list_display = ('name', 'school_type', 'ownership',
                    'region', 'district', 'is_active', 'created_at')
    list_filter = ('school_type', 'ownership', 'region',
                   'is_active', 'has_boarding')
    search_fields = ('name', 'emis_code', 'ges_number', 'district', 'town')
    readonly_fields = ('slug', 'created_at', 'updated_at', 'registration_date')

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'school_type', 'ownership', 'motto')
        }),
        ('Registration Details', {
            'fields': ('emis_code', 'ges_number', 'establishment_date', 'registration_date'),
            'classes': ('collapse',)
        }),
        ('Location', {
            'fields': ('region', 'district', 'town', 'digital_address', 'physical_address')
        }),
        ('Contact Information', {
            'fields': ('headmaster_name', 'email', 'phone_primary', 'phone_secondary', 'website')
        }),
        ('Media & Settings', {
            'fields': ('logo', 'has_boarding', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request)

    def logo_preview(self, obj):
        """Display logo preview in admin"""
        if obj.logo:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 8px;" />',
                obj.logo.url
            )
        return "No logo"

    logo_preview.short_description = 'Logo Preview'

    def school_status(self, obj):
        """Display school status with colored indicator"""
        if obj.is_active:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">● Active</span>'
            )
        else:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">● Inactive</span>'
            )

    school_status.short_description = 'Status'

    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }
        js = ('admin/js/custom_admin.js',)


# Custom Admin Site Configuration
admin.site.site_header = "T. I. Ahmadiyya SHS Administration"
admin.site.site_title = "T. I. Ahmadiyya SHS Admin"
admin.site.index_title = "School Management System"

# Add custom CSS for admin
admin.site.enable_nav_sidebar = True
