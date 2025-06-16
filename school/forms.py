# File: apps/school/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import (
    School, AcademicYear, Term, Programme, House,
    Subject, Class, Teacher
)


class SchoolConfigurationForm(forms.ModelForm):
    """Form for school basic configuration"""

    class Meta:
        model = School
        fields = [
            'name', 'code', 'address', 'phone', 'email', 'website',
            'motto', 'established_year', 'logo', 'academic_year_start_month',
            'terms_per_year', 'headmaster_name', 'assistant_headmaster_name',
            'primary_color', 'secondary_color'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'School Name'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'School Code (e.g., TTEK)'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'School Address'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '0244123456'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'admin@school.edu.gh'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.school.edu.gh'
            }),
            'motto': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'School Motto'
            }),
            'established_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1800,
                'max': timezone.now().year
            }),
            'logo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'academic_year_start_month': forms.Select(attrs={
                'class': 'form-select'
            }, choices=[
                (1, 'January'), (2, 'February'), (3, 'March'),
                (4, 'April'), (5, 'May'), (6, 'June'),
                (7, 'July'), (8, 'August'), (9, 'September'),
                (10, 'October'), (11, 'November'), (12, 'December')
            ]),
            'terms_per_year': forms.Select(attrs={
                'class': 'form-select'
            }, choices=[(2, '2 Terms'), (3, '3 Terms')]),
            'headmaster_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Headmaster Full Name'
            }),
            'assistant_headmaster_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Assistant Headmaster Full Name'
            }),
            'primary_color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
            'secondary_color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
        }


class AcademicYearForm(forms.ModelForm):
    """Form for academic year management"""

    class Meta:
        model = AcademicYear
        fields = ['year', 'start_date', 'end_date', 'is_current']
        widgets = {
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 2020,
                'max': 2050
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'is_current': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date >= end_date:
            raise ValidationError('End date must be after start date.')

        return cleaned_data


class TermForm(forms.ModelForm):
    """Form for term management"""

    class Meta:
        model = Term
        fields = ['academic_year', 'term_number',
                  'start_date', 'end_date', 'is_current']
        widgets = {
            'academic_year': forms.Select(attrs={
                'class': 'form-select'
            }),
            'term_number': forms.Select(attrs={
                'class': 'form-select'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'is_current': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date >= end_date:
            raise ValidationError('End date must be after start date.')

        return cleaned_data


class ProgrammeForm(forms.ModelForm):
    """Form for programme management"""

    class Meta:
        model = Programme
        fields = ['name', 'code', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Programme Name (e.g., General Arts)'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Code (e.g., ART, BUS, SCI)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Programme Description'
            })
        }


class HouseForm(forms.ModelForm):
    """Form for house management"""

    class Meta:
        model = House
        fields = ['name', 'color', 'description', 'house_master']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'House Name'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'House Description'
            }),
            'house_master': forms.Select(attrs={
                'class': 'form-select'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['house_master'].queryset = Teacher.objects.filter(
            is_active=True)
        self.fields['house_master'].empty_label = "Select House Master"


class SubjectForm(forms.ModelForm):
    """Form for subject management"""

    class Meta:
        model = Subject
        fields = ['name', 'subject_type']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Subject Name'
            }),
            'subject_type': forms.Select(attrs={
                'class': 'form-select'
            })
        }


class ClassForm(forms.ModelForm):
    """Form for class management"""

    class Meta:
        model = Class
        fields = ['name', 'programme', 'level', 'class_teacher', 'capacity']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Class Section (e.g., A, B, C)'
            }),
            'programme': forms.Select(attrs={
                'class': 'form-select'
            }),
            'level': forms.Select(attrs={
                'class': 'form-select'
            }),
            'class_teacher': forms.Select(attrs={
                'class': 'form-select'
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 10,
                'max': 100
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['programme'].queryset = Programme.objects.all()
        self.fields['programme'].empty_label = "Select Programme (Optional for Form 1)"
        self.fields['class_teacher'].queryset = Teacher.objects.filter(
            is_active=True)
        self.fields['class_teacher'].empty_label = "Select Class Teacher"


class QuickSetupForm(forms.Form):
    """Form for quick school setup"""

    # School basics
    school_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'T. I. Ahmadiyya SHS'
        })
    )

    school_code = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'TTEK'
        })
    )

    # Academic year
    academic_year = forms.IntegerField(
        initial=timezone.now().year,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 2020,
            'max': 2050
        })
    )

    # Programmes to create
    create_programmes = forms.MultipleChoiceField(
        choices=[
            ('general_arts', 'General Arts'),
            ('business', 'Business'),
            ('general_science', 'General Science'),
            ('visual_arts', 'Visual Arts'),
            ('home_economics', 'Home Economics'),
            ('technical', 'Technical'),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        required=False
    )

    # Houses to create
    create_houses = forms.MultipleChoiceField(
        choices=[
            ('red', 'Red House'),
            ('blue', 'Blue House'),
            ('green', 'Green House'),
            ('yellow', 'Yellow House'),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        required=False
    )

    # Admin user
    admin_username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'admin'
        })
    )

    admin_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Strong password'
        })
    )

    admin_email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'admin@school.edu.gh'
        })
    )
