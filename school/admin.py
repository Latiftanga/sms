from django.contrib import admin
from school.models import (
    School, AcademicYear, Term, Programme, House,
    Subject, Class, Student, Teacher
)
from django import forms
from django.utils.html import format_html


class SchoolAdminForm(forms.ModelForm):
    """Custom form for School admin with color picker"""

    class Meta:
        model = School
        fields = '__all__'
        widgets = {
            'primary_color': forms.TextInput(attrs={
                'type': 'color',
                'style': 'width: 50px; height: 40px; border: none; cursor: pointer;'
            }),
            'secondary_color': forms.TextInput(attrs={
                'type': 'color',
                'style': 'width: 50px; height: 40px; border: none; cursor: pointer;'
            }),
        }


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    form = SchoolAdminForm

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'address', 'phone', 'email', 'website')
        }),
        ('School Details', {
            'fields': ('motto', 'established_year', 'logo')
        }),
        ('Academic Settings', {
            'fields': ('academic_year_start_month', 'terms_per_year')
        }),
        ('Contact Information', {
            'fields': ('headmaster_name', 'assistant_headmaster_name')
        }),
        ('Theme Colors', {
            'fields': ('primary_color', 'secondary_color'),
            'description': 'Choose colors that will be applied throughout the system interface'
        }),
    )

    list_display = ['name', 'code', 'phone', 'email', 'color_preview']

    def color_preview(self, obj):
        """Display color preview in admin list"""
        return format_html(
            '<div style="display: flex; gap: 5px;">'
            '<div style="width: 20px; height: 20px; background-color: {}; border: 1px solid #ccc; border-radius: 3px;"></div>'
            '<div style="width: 20px; height: 20px; background-color: {}; border: 1px solid #ccc; border-radius: 3px;"></div>'
            '</div>',
            obj.primary_color, obj.secondary_color
        )
    color_preview.short_description = 'Colors'
    color_preview.allow_tags = True


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('year', 'start_date', 'end_date',
                    'is_current', 'created_at')
    list_filter = ('is_current', 'year')
    search_fields = ('year',)
    ordering = ('-year',)


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'academic_year',
                    'start_date', 'end_date', 'is_current')
    list_filter = ('academic_year', 'term_number', 'is_current')
    search_fields = ('academic_year__year',)
    ordering = ('-academic_year__year', 'term_number')


@admin.register(Programme)
class ProgrammeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'created_at')
    search_fields = ('name', 'code')
    readonly_fields = ('code',)
    ordering = ('name',)


@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    list_display = ('name', 'house_master', 'color', 'created_at')
    list_filter = ('house_master',)
    search_fields = ('name', 'house_master__first_name',
                     'house_master__last_name')
    ordering = ('name',)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'subject_type', 'created_at')
    list_filter = ('subject_type',)
    search_fields = ('name', 'code')
    readonly_fields = ('code',)
    ordering = ('name',)


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'get_full_name', 'level', 'programme',
                    'class_teacher', 'get_student_count', 'capacity')
    list_filter = ('level', 'programme', 'class_teacher')
    search_fields = ('name', 'programme__name',
                     'class_teacher__first_name', 'class_teacher__last_name')
    ordering = ('level', 'programme__name', 'name')

    def get_student_count(self, obj):
        return obj.get_student_count()
    get_student_count.short_description = 'Students'


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'get_full_name',
                    'current_class', 'house', 'year_admitted', 'is_active')
    list_filter = ('current_class', 'house',
                   'year_admitted', 'is_active', 'gender')
    search_fields = ('student_id', 'first_name',
                     'last_name', 'email', 'guardian_name')
    readonly_fields = ('student_id', 'created_at', 'updated_at')
    ordering = ('-created_at',)

    fieldsets = (
        ('Student Information', {
            'fields': ('student_id', 'first_name', 'middle_name', 'last_name', 'gender', 'date_of_birth')
        }),
        ('Contact Information', {
            'fields': ('phone', 'email', 'address', 'ghana_card_number')
        }),
        ('Academic Information', {
            'fields': ('current_class', 'house', 'year_admitted')
        }),
        ('Guardian Information', {
            'fields': ('guardian_name', 'guardian_phone', 'guardian_email', 'relationship_to_guardian')
        }),
        ('System Information', {
            'fields': ('user', 'is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('teacher_id', 'get_full_name', 'qualification',
                    'date_of_employment', 'years_of_experience', 'is_active')
    list_filter = ('qualification', 'date_of_employment',
                   'is_active', 'gender')
    search_fields = ('teacher_id', 'first_name',
                     'last_name', 'email', 'qualification')
    readonly_fields = ('teacher_id', 'created_at', 'updated_at')
    filter_horizontal = ('subjects',)
    ordering = ('-created_at',)

    fieldsets = (
        ('Teacher Information', {
            'fields': ('teacher_id', 'first_name', 'middle_name', 'last_name', 'gender', 'date_of_birth')
        }),
        ('Contact Information', {
            'fields': ('phone', 'email', 'address', 'ghana_card_number')
        }),
        ('Professional Information', {
            'fields': ('qualification', 'specialization', 'years_of_experience', 'date_of_employment')
        }),
        ('Teaching Subjects', {
            'fields': ('subjects',)
        }),
        ('System Information', {
            'fields': ('user', 'is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
