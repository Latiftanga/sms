from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import MinLengthValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.conf import settings
from .validators import PHONE_VALIDATOR, GHANA_CARD_VALIDATOR


# TimeStampedModel
class TimeStampedModel(models.Model):
    """Abstract model with created and modified timestamps"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# School Model
class School(TimeStampedModel):
    """School information stored in database"""

    # Basic Information
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=10, unique=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=15, validators=[PHONE_VALIDATOR])
    email = models.EmailField()
    website = models.URLField(blank=True, null=True)

    # School Details
    motto = models.CharField(max_length=200, blank=True)
    established_year = models.IntegerField(blank=True, null=True)
    logo = models.ImageField(upload_to='school/', blank=True, null=True)

    # Administrative Settings
    academic_year_start_month = models.IntegerField(default=9)  # September
    terms_per_year = models.IntegerField(default=3)

    # Contact Information
    headmaster_name = models.CharField(max_length=200, blank=True)
    assistant_headmaster_name = models.CharField(max_length=200, blank=True)

    # School Colors (for UI theming)
    primary_color = models.CharField(max_length=7, default="#1B5E20")
    secondary_color = models.CharField(max_length=7, default="#2E7D32")

    class Meta:
        verbose_name = 'School Information'
        verbose_name_plural = 'School Information'

    def __str__(self):
        return f"{self.name} ({self.code})"

    @classmethod
    def get_current_school(cls):
        """Get the current school (only one should exist)"""
        school = cls.objects.first()
        if not school:
            # Create default school if none exists
            school = cls.objects.create(
                name='T. I. Ahmadiyya SHS',
                code='TTEK',
                address='Address not set',
                phone='0000000000',
                email='admin@ttek.edu.gh'
            )
        return school

    def get_current_academic_year(self):
        """Get current academic year based on start month"""
        now = timezone.now()
        if now.month >= self.academic_year_start_month:
            return now.year
        else:
            return now.year - 1


# Academic Year Model
class AcademicYear(TimeStampedModel):
    """Academic year model"""
    year = models.IntegerField(unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ['-year']

    def __str__(self):
        return f"{self.year} Academic Year"

    def save(self, *args, **kwargs):
        if self.is_current:
            # Ensure only one academic year is current
            AcademicYear.objects.filter(
                is_current=True).update(is_current=False)
        super().save(*args, **kwargs)


# Term Model
class Term(TimeStampedModel):
    """Academic term model"""
    TERM_CHOICES = [
        (1, 'First Term'),
        (2, 'Second Term'),
        (3, 'Third Term'),
    ]

    academic_year = models.ForeignKey(
        AcademicYear, on_delete=models.CASCADE, related_name='terms')
    term_number = models.IntegerField(choices=TERM_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    class Meta:
        unique_together = ['academic_year', 'term_number']
        ordering = ['academic_year', 'term_number']

    def __str__(self):
        return f"{self.get_term_number_display()} - {self.academic_year.year}"

    def save(self, *args, **kwargs):
        if self.is_current:
            # Ensure only one term is current
            Term.objects.filter(is_current=True).update(is_current=False)
        super().save(*args, **kwargs)


# Programme Model
class Programme(TimeStampedModel):
    """Academic programmes like Arts, Business, Science"""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=5, unique=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Programme'
        verbose_name_plural = 'Programmes'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.code:
            # Auto-generate code from first 3 letters of name
            self.code = self.name[:3].upper()

            # Ensure uniqueness
            counter = 1
            original_code = self.code
            while Programme.objects.filter(code=self.code).exists():
                self.code = f"{original_code}{counter}"
                counter += 1

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.code})"


# House Model
class House(TimeStampedModel):
    """Student houses for school organization"""
    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=7, default="#1B5E20")  # Hex color
    description = models.TextField(blank=True)
    house_master = models.ForeignKey(
        'Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='houses_led'
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


# Subject Model
class Subject(TimeStampedModel):
    """Subject taught in the school"""
    name = models.CharField(max_length=100, unique=True)
    subject_type = models.CharField(
        max_length=50,
        choices=[
            ('core', 'Core'),
            ('elective', 'Elective'),
            ('extracurricular', 'Extracurricular Activity')
        ],
        default='core',
        help_text="Type of subject"
    )
    code = models.CharField(max_length=10, unique=True, blank=True)

    class Meta:
        verbose_name = 'Subject'
        verbose_name_plural = 'Subjects'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.code:
            # Auto-generate code from first 3 letters of name
            self.code = self.name[:3].upper()

            # Ensure uniqueness
            counter = 1
            original_code = self.code
            while Subject.objects.filter(code=self.code).exists():
                self.code = f"{original_code}{counter}"
                counter += 1

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.code})"


# Class Model
class Class(TimeStampedModel):
    """Enhanced Class/Form with Programme and Level structure"""
    LEVEL_CHOICES = [
        (1, 'Form 1'),
        (2, 'Form 2'),
        (3, 'Form 3'),
    ]

    name = models.CharField(
        max_length=10, help_text="Class section (e.g., A, B, C)")
    programme = models.ForeignKey(
        Programme,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Academic programme (optional for SHS 1)"
    )
    level = models.PositiveSmallIntegerField(
        choices=LEVEL_CHOICES,
        help_text="Class level (1, 2, or 3)"
    )
    class_teacher = models.ForeignKey(
        'Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='taught_classes'
    )
    capacity = models.PositiveIntegerField(default=45)

    class Meta:
        verbose_name = 'Class'
        verbose_name_plural = 'Classes'
        ordering = ['level', 'programme__code', 'name']
        unique_together = ['level', 'programme', 'name']

    def __str__(self):
        """Generate class name like 1BUSA, 2SCIA, 1A"""
        parts = [str(self.level)]
        if self.programme:
            parts.append(self.programme.code)
        parts.append(self.name.upper())
        return ''.join(filter(None, parts))

    def get_full_name(self):
        """Get descriptive name like 'SHS 1 Business A' """
        level_name = f"SHS {self.level}"
        if self.programme:
            return f"{level_name} {self.programme.name} {self.name}"
        return f"{level_name} {self.name}"

    def get_student_count(self):
        """Get current number of students in this class"""
        return self.students.filter(is_active=True).count()

    def is_full(self):
        """Check if class is at capacity"""
        return self.get_student_count() >= self.capacity


# ID Generation Mixin
class IDGenerationMixin:
    """Mixin for models that need auto-generated IDs using School model"""
    ID_PREFIX = ''
    id_field = None

    def generate_id(self):
        """Generate a unique ID with pattern: {ID_PREFIX}{school_code}{SEQ:03d}{Year}"""
        school = School.get_current_school()
        school_code = school.code

        year = str(getattr(self, 'year_admitted', timezone.now().year))[-2:]
        prefix = self.ID_PREFIX

        model_class = self.__class__
        id_field = self.id_field

        year_pattern_start = f"{prefix}{school_code}"
        year_pattern_end = year

        existing_ids = model_class.objects.filter(
            **{f"{id_field}__startswith": year_pattern_start},
            **{f"{id_field}__endswith": year_pattern_end}
        ).values_list(id_field, flat=True)

        max_seq = 0
        expected_length = len(year_pattern_start) + 3 + len(year_pattern_end)

        for existing_id in existing_ids:
            if len(existing_id) == expected_length:
                try:
                    seq_part = existing_id[len(
                        year_pattern_start):-len(year_pattern_end)]
                    if seq_part.isdigit() and len(seq_part) == 3:
                        seq_num = int(seq_part)
                        max_seq = max(max_seq, seq_num)
                except (ValueError, IndexError):
                    pass

        new_seq = max_seq + 1
        return f"{prefix}{school_code}{new_seq:03d}{year}"


# Abstract Person Model
class Person(IDGenerationMixin, TimeStampedModel):
    """Abstract base model for all person types (Student, Teacher, etc.)"""

    GENDER_CHOICES = (('M', 'Male'), ('F', 'Female'))

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="%(class)s_profile",
        blank=True, null=True
    )
    first_name = models.CharField(
        max_length=100, validators=[MinLengthValidator(2)])
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, validators=[
                                 MinLengthValidator(2)])
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    phone = models.CharField(max_length=15, blank=True,
                             null=True, validators=[PHONE_VALIDATOR])
    address = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(max_length=128, blank=True, null=True)
    ghana_card_number = models.CharField(
        max_length=15, unique=True, blank=True, null=True, validators=[GHANA_CARD_VALIDATOR]
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True

    def get_full_name(self):
        return ' '.join(filter(None, [self.first_name, self.middle_name, self.last_name]))

    def clean(self):
        if self.date_of_birth and self.date_of_birth > timezone.now().date():
            raise ValidationError(
                {"date_of_birth": "Date of birth cannot be in the future"})

    def save(self, *args, **kwargs):
        """Auto-generate ID if not provided"""
        if self.id_field and not getattr(self, self.id_field):
            setattr(self, self.id_field, self.generate_id())
        super().save(*args, **kwargs)

    def __str__(self):
        return self.get_full_name()


# Student Model
class Student(Person):
    """Student model - inherits from Person with IDGenerationMixin"""

    ID_PREFIX = 'STU'
    id_field = 'student_id'

    student_id = models.CharField(max_length=20, unique=True, blank=True)
    current_class = models.ForeignKey(
        Class,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students'
    )
    house = models.ForeignKey(
        House,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students'
    )
    year_admitted = models.IntegerField()

    # Guardian Information
    guardian_name = models.CharField(max_length=200, blank=True, null=True)
    guardian_phone = models.CharField(
        max_length=15, blank=True, null=True, validators=[PHONE_VALIDATOR])
    guardian_email = models.EmailField(blank=True, null=True)
    relationship_to_guardian = models.CharField(
        max_length=50, blank=True, null=True)

    def get_contact_email(self):
        """Get student email or guardian email as fallback"""
        return self.email or self.guardian_email

    def get_contact_phone(self):
        """Get student phone or guardian phone as fallback"""
        return self.phone or self.guardian_phone

    def __str__(self):
        return f"{self.get_full_name()} ({self.student_id})"


# Teacher Model
class Teacher(Person):
    """Teacher model - inherits from Person with IDGenerationMixin"""

    ID_PREFIX = 'TCH'
    id_field = 'teacher_id'

    teacher_id = models.CharField(max_length=20, unique=True, blank=True)
    qualification = models.CharField(max_length=200)
    specialization = models.CharField(max_length=200, blank=True, null=True)
    years_of_experience = models.IntegerField(default=0)
    date_of_employment = models.DateField()
    subjects = models.ManyToManyField(Subject, blank=True)

    @property
    def year_admitted(self):
        """Use employment year for ID generation"""
        return self.date_of_employment.year

    def __str__(self):
        return f"{self.get_full_name()} ({self.teacher_id})"
