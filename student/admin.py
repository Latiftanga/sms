# # File: student/admin.py
# from django.contrib import admin
# from django.db.models import Q
# from django.utils.html import format_html
# from django.urls import reverse
# from django.utils.safestring import mark_safe
# from django.http import HttpResponse
# import csv
# from datetime import datetime

# from school.models import Student
# from .utils import export_students_to_csv


# class StudentAdmin(admin.ModelAdmin):
#     """Enhanced admin interface for Student model"""

#     list_display = [
#         'student_id', 'get_full_name', 'gender', 'current_class',
#         'house', 'year_admitted', 'is_active', 'has_user_account',
#         'guardian_contact'
#     ]

#     list_filter = [
#         'is_active', 'gender', 'year_admitted', 'current_class__level',
#         'current_class__programme', 'house', 'created_at'
#     ]

#     search_fields = [
#         'student_id', 'first_name', 'last_name', 'email',
#         'phone', 'guardian_name', 'guardian_phone', 'ghana_card_number'
#     ]

#     list_per_page = 25
#     list_max_show_all = 100

#     ordering = ['current_class__level',
#                 'current_class__name', 'last_name', 'first_name']

#     fieldsets = (
#         ('Basic Information', {
#             'fields': ('student_id', 'first_name', 'middle_name', 'last_name',
#                        'gender', 'date_of_birth', 'ghana_card_number')
#         }),
#         ('Contact Information', {
#             'fields': ('email', 'phone', 'address'),
#             'classes': ('collapse',)
#         }),
#         ('Academic Information', {
#             'fields': ('year_admitted', 'current_class', 'house')
#         }),
#         ('Guardian Information', {
#             'fields': ('guardian_name', 'guardian_phone', 'guardian_email',
#                        'relationship_to_guardian'),
#             'classes': ('collapse',)
#         }),
#         ('System Information', {
#             'fields': ('user', 'is_active'),
#             'classes': ('collapse',)
#         })
#     )

#     readonly_fields = ['student_id', 'created_at', 'updated_at']

#     actions = [
#         'export_selected_students',
#         'activate_students',
#         'deactivate_students',
#         'reset_student_passwords'
#     ]

#     def get_full_name(self, obj):
#         """Display full name with link to detail view"""
#         return format_html(
#             '<a href="{}" style="text-decoration: none;">{}</a>',
#             reverse('admin:school_student_change', args=[obj.pk]),
#             obj.get_full_name()
#         )
#     get_full_name.short_description = 'Full Name'
#     get_full_name.admin_order_field = 'last_name'

#     def has_user_account(self, obj):
#         """Display user account status"""
#         if obj.user:
#             if obj.user.is_active:
#                 return format_html(
#                     '<span style="color: green;">✓ Active</span>'
#                 )
#             else:
#                 return format_html(
#                     '<span style="color: orange;">⚠ Inactive</span>'
#                 )
#         return format_html(
#             '<span style="color: red;">✗ No Account</span>'
#         )
#     has_user_account.short_description = 'User Account'

#     def guardian_contact(self, obj):
#         """Display guardian contact information"""
#         if obj.guardian_phone:
#             return format_html(
#                 '<div style="font-size: 12px;">'
#                 '<strong>{}</strong><br>'
#                 '<a href="tel:{}">{}</a>'
#                 '</div>',
#                 obj.guardian_name or 'Guardian',
#                 obj.guardian_phone,
#                 obj.guardian_phone
#             )
#         return '-'
#     guardian_contact.short_description = 'Guardian Contact'

#     def get_queryset(self, request):
#         """Optimize queries with select_related"""
#         queryset = super().get_queryset(request)
#         return queryset.select_related(
#             'current_class', 'house', 'current_class__programme', 'user'
#         )

#     def export_selected_students(self, request, queryset):
#         """Export selected students to CSV"""
#         response = HttpResponse(content_type='text/csv')
#         timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
#         response['Content-Disposition'] = f'attachment; filename="students_export_{timestamp}.csv"'

#         csv_content = export_students_to_csv(queryset)
#         response.write(csv_content)

#         self.message_user(
#             request,
#             f'Successfully exported {queryset.count()} students to CSV.'
#         )
#         return response
#     export_selected_students.short_description = "Export selected students to CSV"

#     def activate_students(self, request, queryset):
#         """Activate selected students"""
#         updated = queryset.update(is_active=True)

#         # Also activate user accounts
#         for student in queryset:
#             if student.user:
#                 student.user.is_active = True
#                 student.user.save()

#         self.message_user(
#             request,
#             f'Successfully activated {updated} students.'
#         )
#     activate_students.short_description = "Activate selected students"

#     def deactivate_students(self, request, queryset):
#         """Deactivate selected students"""
#         updated = queryset.update(is_active=False)

#         # Also deactivate user accounts
#         for student in queryset:
#             if student.user:
#                 student.user.is_active = False
#                 student.user.save()

#         self.message_user(
#             request,
#             f'Successfully deactivated {updated} students.'
#         )
#     deactivate_students.short_description = "Deactivate selected students"

#     def reset_student_passwords(self, request, queryset):
#         """Reset passwords for selected students"""
#         from account.models import generate_random_password

#         reset_count = 0
#         for student in queryset:
#             if student.user:
#                 new_password = generate_random_password()
#                 student.user.set_password(new_password)
#                 student.user.save()
#                 reset_count += 1

#         self.message_user(
#             request,
#             f'Successfully reset passwords for {reset_count} students. '
#             f'New passwords have been generated.'
#         )
#     reset_student_passwords.short_description = "Reset passwords for selected students"

#     def changelist_view(self, request, extra_context=None):
#         """Add custom context to changelist view"""
#         extra_context = extra_context or {}

#         # Add summary statistics
#         queryset = self.get_queryset(request)

#         extra_context.update({
#             'total_students': queryset.filter(is_active=True).count(),
#             'inactive_students': queryset.filter(is_active=False).count(),
#             'students_without_accounts': queryset.filter(user__isnull=True).count(),
#             'students_by_level': queryset.values('current_class__level').distinct().count(),
#         })

#         return super().changelist_view(request, extra_context=extra_context)

#     def save_model(self, request, obj, form, change):
#         """Custom save logic"""
#         # Auto-generate student ID if not provided
#         if not obj.student_id:
#             obj.save()  # This will trigger the ID generation in the model
#         else:
#             super().save_model(request, obj, form, change)

#         # Create user account if doesn't exist
#         if not obj.user and not change:  # Only for new students
#             try:
#                 from account.models import create_student_with_user
#                 create_student_with_user(
#                     first_name=obj.first_name,
#                     last_name=obj.last_name,
#                     year_admitted=obj.year_admitted,
#                     email=obj.email,
#                     **{field.name: getattr(obj, field.name)
#                        for field in obj._meta.fields
#                        if field.name not in ['id', 'student_id', 'user']}
#                 )
#                 self.message_user(
#                     request,
#                     f'Student account created with username: {obj.student_id}'
#                 )
#             except Exception as e:
#                 self.message_user(
#                     request,
#                     f'Error creating user account: {str(e)}',
#                     level='ERROR'
#                 )

#     class Media:
#         css = {
#             'all': ('admin/css/student_admin.css',)
#         }
#         js = ('admin/js/student_admin.js',)


# # Custom admin site configuration
# admin.site.register(Student, StudentAdmin)

# # Customize admin site headers
# admin.site.site_header = "School Management System"
# admin.site.site_title = "SMS Admin"
# admin.site.index_title = "Welcome to School Management System Administration"
