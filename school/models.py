import string
import random
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser, PermissionsMixin
)
from django.core.validators import (
    MinLengthValidator
)
from django.utils import timezone
from django.core.exceptions import ValidationError
from school.validators import PHONE_VALIDATOR, GHANA_CARD_VALIDATOR
from school.managers import UserManager
from django.conf import settings
from .validators import PHONE_VALIDATOR, GHANA_CARD_VALIDATOR



# TimeStampedModel
# ================

class TimeStampedModel(models.Model):
    """Abstract model with created and modified timestamps"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# School Model
# ============

class School(TimeStampedModel):
    """School information stored in database"""

    # Basic Information
    name = models.CharField(max_length=200)
    # Used for ID generation
    code = models.CharField(max_length=10, unique=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=15)
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
    primary_color = models.CharField(
        max_length=7, default="#15ca5d")  # Hex color
    secondary_color = models.CharField(max_length=7, default="#7a7d6c")

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
                name='School Management System',
                code='SCH',
                address='Address not set',
                phone='Phone not set',
                email='email@school.edu'
            )
        return school

    def get_current_academic_year(self):
        """Get current academic year based on start month"""
        now = timezone.now()
        if now.month >= self.academic_year_start_month:
            return now.year
        else:
            return now.year - 1


# User Model (SINGLE DEFINITION)
# ==============================

class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    """Custom User model for Django authentication"""

    # Core fields required by Django
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    first_name = models.CharField(
        max_length=150, blank=True)  # Django compatibility
    last_name = models.CharField(
        max_length=150, blank=True)   # Django compatibility

    # Permission fields (from PermissionsMixin)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    # School-specific fields
    is_teacher = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    # Timestamps (inherited from TimeStampedModel, but we need date_joined for Django)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(blank=True, null=True)

    # Required for Django authentication
    objects = UserManager()
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []  # Email is optional for students

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def get_full_name(self):
        """Get full name from related profile if exists"""
        if self.is_student and hasattr(self, 'student_profile'):
            return self.student_profile.get_full_name()
        elif self.is_teacher and hasattr(self, 'teacher_profile'):
            return self.teacher_profile.get_full_name()
        else:
            return f"{self.first_name} {self.last_name}".strip() or self.username

    def get_short_name(self):
        """Get short name for display"""
        if self.is_student and hasattr(self, 'student_profile'):
            return self.student_profile.first_name
        elif self.is_teacher and hasattr(self, 'teacher_profile'):
            return self.teacher_profile.first_name
        else:
            return self.first_name or self.username

    def get_profile(self):
        """Get the related Student or Teacher profile"""
        if self.is_student and hasattr(self, 'student_profile'):
            return self.student_profile
        elif self.is_teacher and hasattr(self, 'teacher_profile'):
            return self.teacher_profile
        return None

    def __str__(self):
        full_name = self.get_full_name()
        if full_name != self.username:
            return f"{full_name} ({self.username})"
        return self.username


# ID Generation Mixin
# ===================

class IDGenerationMixin:
    """Mixin for models that need auto-generated IDs using School model"""
    ID_PREFIX = ''  # Default prefix, should be overridden in subclass
    id_field = None  # Should be set in subclass

    def generate_id(self):
        """Generate a unique ID with pattern: {ID_PREFIX}{school_code}{SEQ:03d}{Year}"""
        # Get school code from database
        school = School.get_current_school()
        school_code = school.code

        # Get year (2 digits)
        year = str(getattr(self, 'year_admitted', timezone.now().year))[-2:]

        # Get prefix
        prefix = self.ID_PREFIX

        # Find the highest existing sequence number for this year
        model_class = self.__class__
        id_field = self.id_field

        # Pattern for this year: {PREFIX}{SCHOOL_CODE}???{YEAR}
        year_pattern_start = f"{prefix}{school_code}"
        year_pattern_end = year

        existing_ids = model_class.objects.filter(
            **{f"{id_field}__startswith": year_pattern_start},
            **{f"{id_field}__endswith": year_pattern_end}
        ).values_list(id_field, flat=True)

        # Extract the sequence numbers for this year
        max_seq = 0
        expected_length = len(year_pattern_start) + 3 + len(year_pattern_end)

        for existing_id in existing_ids:
            if len(existing_id) == expected_length:
                try:
                    # Extract the 3-digit sequence part
                    seq_part = existing_id[len(
                        year_pattern_start):-len(year_pattern_end)]
                    if seq_part.isdigit() and len(seq_part) == 3:
                        seq_num = int(seq_part)
                        max_seq = max(max_seq, seq_num)
                except (ValueError, IndexError):
                    pass

        # Create new ID with incremented sequence, padded to 3 digits
        new_seq = max_seq + 1
        return f"{prefix}{school_code}{new_seq:03d}{year}"


# Abstract Person Model
# =====================

class Person(IDGenerationMixin, TimeStampedModel):
    """Abstract base model for all person types (Student, Teacher, etc.)"""

    GENDER_CHOICES = (('M', 'Male'), ('F', 'Female'))

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,  # Use settings instead of direct User reference
        on_delete=models.SET_NULL,
        # Creates student_profile, teacher_profile automatically
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


# Programme Model
# ===============

class Programme(TimeStampedModel):
    """Academic programmes like Arts, Business, Science"""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=5, unique=True,
                            editable=False, blank=True)
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


# Subject Model
# =============

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
    code = models.CharField(max_length=10, unique=True, blank=True,
                            help_text="Short code for the subject (e.g., ENG for English)")

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
# ===========

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
        related_name='taught_classes',  # Add related_name to avoid conflicts
        help_text="Form teacher for this class"
    )
    capacity = models.PositiveIntegerField(
        default=45, help_text="Maximum number of students")

    class Meta:
        verbose_name = 'Class'
        verbose_name_plural = 'Classes'
        ordering = ['level', 'programme__code', 'name']
        unique_together = ['level', 'programme', 'name']  # Prevent duplicates

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

    def get_students(self):
        """Get all students in this class"""
        return self.students.filter(is_active=True)

    def is_full(self):
        """Check if class is at capacity"""
        return self.get_student_count() >= self.capacity


# Student Model
# =============

class Student(Person):
    """Student model - inherits from Person with IDGenerationMixin"""

    # ID Generation configuration
    ID_PREFIX = 'STU'  # Student prefix
    id_field = 'student_id'

    student_id = models.CharField(max_length=20, unique=True, blank=True)

    # Academic Information
    current_class = models.ForeignKey(
        Class,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students'  # Add related_name to avoid conflicts
    )
    year_admitted = models.IntegerField()  # Used by IDGenerationMixin for year

    # Guardian Information (important for students without email)
    guardian_name = models.CharField(max_length=200, blank=True, null=True)
    guardian_phone = models.CharField(max_length=15, blank=True, null=True)
    guardian_email = models.EmailField(blank=True, null=True)
    relationship_to_guardian = models.CharField(
        max_length=50, blank=True, null=True)

    def get_contact_email(self):
        """Get student email or guardian email as fallback"""
        if self.email:
            return self.email
        elif self.guardian_email:
            return self.guardian_email
        return None

    def get_contact_phone(self):
        """Get student phone or guardian phone as fallback"""
        if self.phone:
            return self.phone
        elif self.guardian_phone:
            return self.guardian_phone
        return None

    def __str__(self):
        return f"{self.get_full_name()} ({self.student_id})"


# Teacher Model
# =============

class Teacher(Person):
    """Teacher model - inherits from Person with IDGenerationMixin"""

    # ID Generation configuration
    ID_PREFIX = 'TCH'  # Teacher prefix
    id_field = 'teacher_id'

    teacher_id = models.CharField(max_length=20, unique=True, blank=True)

    # Professional Information
    qualification = models.CharField(max_length=200)
    specialization = models.CharField(max_length=200, blank=True, null=True)
    years_of_experience = models.IntegerField(default=0)
    date_of_employment = models.DateField()

    # Teaching subjects
    subjects = models.ManyToManyField(Subject, blank=True)

    def __str__(self):
        return f"{self.get_full_name()} ({self.teacher_id})"


# Helper Functions
# ================

def generate_random_password(length=8):
    """Generate a random password"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


def create_student_with_user(first_name, last_name, year_admitted, password=None, email=None, **student_data):
    """Create both User account AND Student profile"""

    # Generate password if not provided
    if not password:
        password = generate_random_password()

    # Create Student profile first (to generate ID)
    student = Student(
        first_name=first_name,
        last_name=last_name,
        year_admitted=year_admitted,
        email=email,
        **student_data  # middle_name, gender, date_of_birth, etc.
    )
    student.save()  # This triggers ID generation

    # Create User account with generated student_id
    user = User.objects.create_student_user(
        student_id=student.student_id,
        password=password,
        email=email
    )

    # Link student to user
    student.user = user
    student.save()

    return {
        'student': student,
        'username': student.student_id,
        'password': password,
        'student_id': student.student_id
    }


def create_teacher_with_user(first_name, last_name, date_of_employment, password=None, email=None, is_admin=False, **teacher_data):
    """Create both User account AND Teacher profile"""

    # Generate password if not provided
    if not password:
        password = generate_random_password()

    # Create Teacher profile first (to generate ID)
    teacher = Teacher(
        first_name=first_name,
        last_name=last_name,
        date_of_employment=date_of_employment,
        email=email,
        **teacher_data  # middle_name, gender, qualification, etc.
    )
    teacher.save()  # This triggers ID generation

    # Create User account with generated teacher_id
    user = User.objects.create_teacher_user(
        teacher_id=teacher.teacher_id,
        password=password,
        email=email,
        is_admin=is_admin
    )

    # Link teacher to user
    teacher.user = user
    teacher.save()

    return {
        'teacher': teacher,
        'username': teacher.teacher_id,
        'password': password,
        'teacher_id': teacher.teacher_id
    }
