from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser, PermissionsMixin
)
from django.core.validators import (
    MinLengthValidator
)
from django.utils import timezone
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.conf import settings
from school.validators import PHONE_VALIDATOR, GHANA_CARD_VALIDATOR
from school.managers import UserManager


class TimeStampedModel(models.Model):
    """Abstract model with created and modified timestamps"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class IDGenerationMixin:
    """Mixin for models that need auto-generated IDs"""
    ID_PREFIX = ''  # Default prefix, should be overridden in subclass
    id_field = None  # Should be set in subclass

    def generate_id(self):
        """Generate a unique ID based on the prefix, school code, and year"""
        if not hasattr(self, 'school') or not self.school:
            raise ValueError("School is required for ID generation")

        year = str(getattr(self, 'year_admitted', timezone.now().year))[-2:]
        prefix = self.ID_PREFIX
        school_code = self.school.code if hasattr(self.school, 'code') else ''

        # Find the highest existing ID number for this pattern
        model_class = self.__class__
        id_field = self.id_field

        pattern = f"{prefix}{school_code}{year}"
        existing_ids = model_class.objects.filter(
            **{f"{id_field}__startswith": pattern}
        ).values_list(id_field, flat=True)

        # Extract the numeric part of existing IDs and find the maximum
        max_num = 0
        for existing_id in existing_ids:
            # Extract the numeric part after the pattern
            if existing_id.startswith(pattern):
                try:
                    num = int(existing_id[len(pattern):])
                    max_num = max(max_num, num)
                except ValueError:
                    pass

        # Create new ID with incremented number, padded to 4 digits
        new_num = max_num + 1
        return f"{pattern}{new_num:04d}"


class School(TimeStampedModel):
    SCHOOL_TYPE = [
        ('basic', 'Basic School'),
        ('shs', 'Senior High School (SHS)'),
        ('technical', 'Technical/Vocational School'),
        ('combined', 'Combined School (Multiple Levels)'),
    ]

    REGION_CHOICES = [
        ('greater_accra', 'Greater Accra'),
        ('ashanti', 'Ashanti'),
        ('western', 'Western'),
        ('eastern', 'Eastern'),
        ('central', 'Central'),
        ('volta', 'Volta'),
        ('northern', 'Northern'),
        ('upper_east', 'Upper East'),
        ('upper_west', 'Upper West'),
        ('bono', 'Bono'),
        ('ahafo', 'Ahafo'),
        ('bono_east', 'Bono East'),
        ('north_east', 'North East'),
        ('savannah', 'Savannah'),
        ('oti', 'Oti'),
        ('western_north', 'Western North'),
    ]

    OWNERSHIP_CHOICES = [
        ('public', 'Public/Government'),
        ('private', 'Private'),
        ('mission', 'Mission/Religious'),
        ('international', 'International'),
    ]

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    code = models.CharField(max_length=10, unique=True,
                            help_text="Short code for the school (e.g., TIA)")
    school_type = models.CharField(max_length=20, choices=SCHOOL_TYPE)
    ownership = models.CharField(max_length=20, choices=OWNERSHIP_CHOICES)

    # Registration information
    emis_code = models.CharField(
        "EMIS Code", max_length=50, blank=True, null=True,
        unique=True,
        help_text="Educational Management Information System code"
    )
    ges_number = models.CharField(
        "GES Number", max_length=50, blank=True, null=True)
    registration_date = models.DateTimeField(auto_now_add=True)
    establishment_date = models.DateField(
        "Date of Establishment", blank=True, null=True)

    # Location
    region = models.CharField(max_length=20, choices=REGION_CHOICES)
    district = models.CharField(max_length=100)
    town = models.CharField(max_length=100)
    digital_address = models.CharField(
        "Ghana Post Digital Address", max_length=50, blank=True, null=True)
    physical_address = models.CharField(max_length=255, blank=True, null=True)

    # Contact information
    headmaster_name = models.CharField(
        "Headmaster/Principal Name", max_length=255)
    email = models.EmailField()
    phone_primary = models.CharField(max_length=20)
    phone_secondary = models.CharField(max_length=20, blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    # School details
    logo = models.ImageField(upload_to='school_logos/', blank=True, null=True)
    motto = models.CharField(max_length=255, blank=True, null=True)
    primary_color = models.CharField(max_length=7, default='#1B5E20')
    secondary_color = models.CharField(max_length=7, default='#2E7D32')
    accent_color = models.CharField(max_length=7, default='#FFB300')
    has_boarding = models.BooleanField(
        "Offers Boarding Facilities", default=False)

    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.code:
            # Generate a code from the school name
            words = self.name.split()
            self.code = ''.join([word[0].upper() for word in words[:3]])
        super().save(*args, **kwargs)

    def clean(self):
        """Validate that school has either domain or subdomain"""
        if not self.domain and not self.subdomain:
            raise ValidationError(
                "School must have either a custom domain or subdomain.")

    def __str__(self):
        return f"{self.name}"

    def get_student_count(self):
        """Get total number of active students"""
        return self.students.filter(is_active=True).count()

    def get_teacher_count(self):
        """Get total number of active teachers"""
        return self.teachers.filter(is_active=True).count()

    class Meta:
        ordering = ['name']
        verbose_name = 'School'
        verbose_name_plural = 'Schools'


class Person(TimeStampedModel):
    GENDER_CHOICES = (('M', 'Male'), ('F', 'Female'))

    # school field is inherited from TenantAwareMixin
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
        max_length=15, unique=True, blank=True,
        null=True, validators=[GHANA_CARD_VALIDATOR])
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True

    def get_full_name(self):
        return ' '.join(
            filter(None, [self.first_name, self.middle_name, self.last_name])
        )

    def clean(self):
        if self.date_of_birth and self.date_of_birth > timezone.now().date():
            raise ValidationError(
                {"date_of_birth": "Date of birth cannot be in the future"})

    def __str__(self):
        return self.get_full_name()


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    """User in the system - each user belongs to a specific school/tenant"""
    # school field is inherited from TenantAwareMixin
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_teacher = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)
    # School admin, not superuser
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)  # Can access Django admin
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'

    def clean(self):
        """Custom validation"""
        super().clean()
        # Ensure superusers don't need school
        if self.is_superuser and not self.school_id:
            pass  # Superusers can exist without a school
        elif not self.is_superuser and not self.school_id:
            raise ValidationError(
                "Non-superuser accounts must belong to a school")

    def __str__(self):
        if self.school:
            return f"{self.username} ({self.school.name})"
        return f"{self.username}"

    def get_role_display(self):
        """Get user role as string"""
        if self.is_superuser:
            return "Super Admin"
        elif self.is_admin:
            return "School Admin"
        elif self.is_teacher:
            return "Teacher"
        elif self.is_student:
            return "Student"
        return "User"


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


class Class(TimeStampedModel):
    """Enhanced Class/Form with Programme and Level structure"""
    LEVEL_CHOICES = [
        (1, 'Form 1'),
        (2, 'Form 2'),
        (3, 'Form 3'),
    ]

    name = models.CharField(
        max_length=10,
        help_text="Class section (e.g., A, B, C)"
    )
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
        help_text="Form teacher for this class"
    )
    capacity = models.PositiveIntegerField(
        default=45,
        help_text="Maximum number of students"
    )

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


class Student(Person, IDGenerationMixin):
    """Student profile"""
    ID_PREFIX = 'STU'
    id_field = 'student_id'

    student_id = models.CharField(
        max_length=20, unique=True, editable=False,
        help_text="Auto-generated student ID"
    )
    year_admitted = models.PositiveIntegerField(
        "Year Admitted", default=timezone.now().year,
        help_text="Year the student was admitted to the school"
    )

    # Updated class information
    currentClass = models.ForeignKey(
        Class,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
        verbose_name='Current Class',
        help_text="Student's current class"
    )

    # Guardian information
    guardian_name = models.CharField(max_length=200, blank=True)
    guardian_phone = models.CharField(
        max_length=15, blank=True, validators=[PHONE_VALIDATOR])
    guardian_email = models.EmailField(blank=True)
    guardian_relationship = models.CharField(
        max_length=50, blank=True,
        help_text="Relationship to student (e.g., Father, Mother, Uncle)"
    )
    guardian_address = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
        ordering = ['last_name', 'first_name']

    def save(self, *args, **kwargs):
        """Override save to generate student ID"""
        if not self.student_id:
            self.student_id = self.generate_id()
        super().save(*args, **kwargs)

    def clean(self):
        """Custom validation for Student model"""
        super().clean()
        current_year = timezone.now().year
        if self.year_admitted < 1900 or self.year_admitted > current_year:
            raise ValidationError(
                {"year_admitted": f"Year admitted must be between 1900 and {current_year}"}
            )

    def __str__(self):
        return f"{self.get_full_name()} ({self.student_id})"

    def has_user_account(self):
        """Check if student has a user account"""
        return self.user is not None

    def get_age(self):
        """Calculate student's age"""
        today = timezone.now().date()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (
                self.date_of_birth.month, self.date_of_birth.day)
        )

    def get_class_display(self):
        """Get class display name"""
        if self.currentClass:
            return str(self.currentClass)
        return "No class assigned"

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


class Teacher(Person, IDGenerationMixin):
    """Teacher profile"""
    ID_PREFIX = 'TCH'
    id_field = 'teacher_id'

    teacher_id = models.CharField(
        max_length=20, unique=True, editable=False,
        help_text="Auto-generated teacher ID"
    )
    subjects = models.ManyToManyField(
        'Subject',
        blank=True,
        related_name='teachers',
        help_text="Subjects taught by the teacher"
    )
    classes = models.ManyToManyField(
        Class,
        blank=True,
        related_name='teachers',
        help_text="Classes assigned to the teacher"
    )

    class Meta:
        verbose_name = 'Teacher'
        verbose_name_plural = 'Teachers'
        ordering = ['last_name', 'first_name']

    def save(self, *args, **kwargs):
        """Override save to generate teacher ID"""
        if not self.teacher_id:
            self.teacher_id = self.generate_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_full_name()} ({self.teacher_id})"

    def get_subjects_display(self):
        """Get comma-separated list of subjects taught"""
        return ', '.join([str(subject) for subject in self.subjects.all()])
