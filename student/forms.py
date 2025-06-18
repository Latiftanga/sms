# File: student/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from school.models import Student, Class, House, Programme
import csv
import io


class StudentForm(forms.ModelForm):
    """Form for creating and updating student records"""

    class Meta:
        model = Student
        fields = [
            'first_name', 'middle_name', 'last_name', 'gender', 'date_of_birth',
            'email', 'phone', 'address', 'ghana_card_number', 'year_admitted',
            'current_class', 'house', 'guardian_name', 'guardian_phone',
            'guardian_email', 'relationship_to_guardian'
        ]

        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter first name'
            }),
            'middle_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter middle name (optional)'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter last name'
            }),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'student@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '0244123456'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter full address'
            }),
            'ghana_card_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'GHA-XXXXXXXXX-X'
            }),
            'year_admitted': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 2000,
                'max': timezone.now().year + 1
            }),
            'current_class': forms.Select(attrs={'class': 'form-select'}),
            'house': forms.Select(attrs={'class': 'form-select'}),
            'guardian_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Guardian full name'
            }),
            'guardian_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '0244123456'
            }),
            'guardian_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'guardian@example.com'
            }),
            'relationship_to_guardian': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Father, Mother, Uncle'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set default year_admitted to current year
        if not self.instance.pk:
            self.fields['year_admitted'].initial = timezone.now().year

        # Make certain fields required
        self.fields['guardian_name'].required = True
        self.fields['guardian_phone'].required = True

        # Order classes by level and name
        self.fields['current_class'].queryset = Class.objects.all().order_by(
            'level', 'programme__code', 'name'
        )

        # Order houses alphabetically
        self.fields['house'].queryset = House.objects.all().order_by('name')

    def clean_date_of_birth(self):
        """Validate date of birth"""
        date_of_birth = self.cleaned_data.get('date_of_birth')
        if date_of_birth:
            today = timezone.now().date()
            age = today.year - date_of_birth.year - (
                (today.month, today.day) < (
                    date_of_birth.month, date_of_birth.day)
            )

            if date_of_birth > today:
                raise ValidationError("Date of birth cannot be in the future.")

            if age < 10 or age > 25:
                raise ValidationError(
                    "Student age should be between 10 and 25 years for SHS admission."
                )

        return date_of_birth

    def clean_year_admitted(self):
        """Validate year admitted"""
        year_admitted = self.cleaned_data.get('year_admitted')
        current_year = timezone.now().year

        if year_admitted:
            if year_admitted < 2000:
                raise ValidationError("Year admitted cannot be before 2000.")

            if year_admitted > current_year + 1:
                raise ValidationError(
                    f"Year admitted cannot be more than {current_year + 1}."
                )

        return year_admitted

    def clean_email(self):
        """Validate email uniqueness (if provided)"""
        email = self.cleaned_data.get('email')
        if email:
            # Check for existing student with same email (excluding current instance)
            queryset = Student.objects.filter(email=email)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise ValidationError(
                    "A student with this email already exists.")

        return email

    def clean_ghana_card_number(self):
        """Validate Ghana Card number uniqueness (if provided)"""
        ghana_card = self.cleaned_data.get('ghana_card_number')
        if ghana_card:
            # Check for existing student with same Ghana Card (excluding current instance)
            queryset = Student.objects.filter(ghana_card_number=ghana_card)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise ValidationError(
                    "A student with this Ghana Card number already exists.")

        return ghana_card


class BulkUploadForm(forms.Form):
    """Form for bulk uploading students from CSV"""

    csv_file = forms.FileField(
        label="CSV File",
        help_text="Upload a CSV file with student data. Download template for format.",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv'
        })
    )

    default_class = forms.ModelChoiceField(
        queryset=Class.objects.all().order_by('level', 'programme__code', 'name'),
        required=False,
        empty_label="Select default class (optional)",
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Default class for students without class specified in CSV"
    )

    default_house = forms.ModelChoiceField(
        queryset=House.objects.all().order_by('name'),
        required=False,
        empty_label="Select default house (optional)",
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Default house for students without house specified in CSV"
    )

    def clean_csv_file(self):
        """Validate CSV file"""
        csv_file = self.cleaned_data.get('csv_file')

        if not csv_file:
            raise ValidationError("Please select a CSV file.")

        if not csv_file.name.endswith('.csv'):
            raise ValidationError("File must be a CSV file.")

        if csv_file.size > 5 * 1024 * 1024:  # 5MB limit
            raise ValidationError("File size must be less than 5MB.")

        # Validate CSV structure
        try:
            csv_file.seek(0)
            content = csv_file.read().decode('utf-8')
            csv_file.seek(0)  # Reset file pointer

            reader = csv.DictReader(io.StringIO(content))

            required_fields = ['first_name', 'last_name',
                               'gender', 'date_of_birth', 'year_admitted']
            headers = reader.fieldnames

            missing_fields = [
                field for field in required_fields if field not in headers]
            if missing_fields:
                raise ValidationError(
                    f"Missing required columns: {', '.join(missing_fields)}"
                )

            # Check if file has data
            row_count = sum(1 for row in reader)
            if row_count == 0:
                raise ValidationError("CSV file appears to be empty.")

            if row_count > 1000:
                raise ValidationError(
                    "Maximum 1000 students can be uploaded at once.")

        except UnicodeDecodeError:
            raise ValidationError(
                "File encoding error. Please save as UTF-8 CSV.")
        except Exception as e:
            raise ValidationError(f"Error reading CSV file: {str(e)}")

        return csv_file


class PromotionForm(forms.Form):
    """Form for promoting students to next class/level"""

    from_class = forms.ModelChoiceField(
        queryset=Class.objects.all().order_by('level', 'programme__code', 'name'),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_from_class'
        }),
        help_text="Select the class to promote students from"
    )

    to_class = forms.ModelChoiceField(
        queryset=Class.objects.all().order_by('level', 'programme__code', 'name'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Select the class to promote students to"
    )

    students = forms.ModelMultipleChoiceField(
        queryset=Student.objects.none(),
        widget=forms.CheckboxSelectMultiple(
            attrs={'class': 'form-check-input'}),
        help_text="Select students to promote"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize with empty student queryset
        self.fields['students'].queryset = Student.objects.none()

        # If form is bound and has from_class, filter students
        if self.is_bound and 'from_class' in self.data:
            try:
                from_class_id = int(self.data.get('from_class'))
                self.fields['students'].queryset = Student.objects.filter(
                    current_class_id=from_class_id,
                    is_active=True
                ).order_by('last_name', 'first_name')
            except (ValueError, TypeError):
                pass

    def clean(self):
        """Validate promotion logic"""
        cleaned_data = super().clean()
        from_class = cleaned_data.get('from_class')
        to_class = cleaned_data.get('to_class')
        students = cleaned_data.get('students')

        if from_class and to_class:
            # Prevent promoting to same class
            if from_class == to_class:
                raise ValidationError(
                    "Cannot promote students to the same class.")

            # Check if promotion is logical (typically to higher level)
            if to_class.level < from_class.level:
                raise ValidationError(
                    "Warning: You are demoting students to a lower level. "
                    "Please confirm this is intentional."
                )

        if students and students.exists():
            # Validate all students belong to from_class
            invalid_students = students.exclude(current_class=from_class)
            if invalid_students.exists():
                raise ValidationError(
                    "Some selected students do not belong to the source class."
                )

        return cleaned_data


class StudentSearchForm(forms.Form):
    """Form for searching and filtering students"""

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, student ID, or email...'
        })
    )

    class_filter = forms.ModelChoiceField(
        queryset=Class.objects.all().order_by('level', 'programme__code', 'name'),
        required=False,
        empty_label="All Classes",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    house_filter = forms.ModelChoiceField(
        queryset=House.objects.all().order_by('name'),
        required=False,
        empty_label="All Houses",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    programme_filter = forms.ModelChoiceField(
        queryset=Programme.objects.all().order_by('name'),
        required=False,
        empty_label="All Programmes",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    year_admitted_filter = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Populate year choices
        years = Student.objects.values_list(
            'year_admitted', flat=True
        ).distinct().order_by('-year_admitted')

        year_choices = [('', 'All Years')] + [(year, str(year))
                                              for year in years]
        self.fields['year_admitted_filter'].choices = year_choices


class StudentProfileForm(forms.ModelForm):
    """Form for students to update their own profile (limited fields)"""

    class Meta:
        model = Student
        fields = ['email', 'phone', 'address']

        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your.email@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '0244123456'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Your current address'
            }),
        }
