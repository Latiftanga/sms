import uuid
import re
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from core.models import (
    Person, IDGenerationMixin, BaseVoucher,
    TimeStampedModel, PHONE_VALIDATOR, School
)


class Programme(TimeStampedModel):
    """Student programmes"""
    school = models.ForeignKey(
        'core.School',
        on_delete=models.CASCADE,
        related_name='programmes',
        verbose_name=_("School")
    )
    name = models.CharField(
        _("Programme Name"),
        max_length=128
    )
    code = models.CharField(
        _("Programme Code"),
        max_length=64,
        blank=True
    )
    description = models.TextField(
        _("Description"),
        blank=True,
        null=True
    )
    is_active = models.BooleanField(
        _("Active"),
        default=True
    )

    class Meta:
        ordering = ['name']
        # Changed unique_together to include school - this ensures uniqueness only within a school
        unique_together = [['school', 'name'], ['school', 'code']]
        verbose_name = _("Programme")
        verbose_name_plural = _("Programmes")

    def __str__(self):
        # Removed school name from string representation
        return f'{self.name} ({self.code})'

    def clean(self):
        """Ensure code is uppercase and auto-generate if not provided"""
        # Auto-generate code if not provided
        if not self.code:
            self.code = self._generate_code_from_name()

        # Ensure code is uppercase
        if self.code:
            self.code = self.code.upper()

        # Make sure code is unique within this school only
        if self.code and self.pk is None:  # Only check on creation
            if Programme.objects.filter(
                school=self.school,
                code=self.code
            ).exists():
                raise ValidationError({
                    'code': _("Programme with this code already exists.")
                })

    def _generate_code_from_name(self):
        """Generate a school-specific code from the programme name"""
        if not self.name:
            return ""

        # Split the name into words
        words = self.name.split()

        # Skip common small words
        skip_words = ['and', 'or', 'the', 'of', 'in', 'for', 'to']
        filtered_words = [
            word for word in words if word.lower() not in skip_words]

        if not filtered_words:
            # If all words were filtered out, use the original name
            filtered_words = words

        # Generate code based on the first letter of each word
        if len(filtered_words) == 1:
            # If only one word, take first two letters
            code = filtered_words[0][:2]
        else:
            # If multiple words, take first letter of each word (up to 3 words)
            code = ''.join(word[0] for word in filtered_words[:3])

        # Remove any non-alphanumeric characters
        code = re.sub(r'[^a-zA-Z0-9]', '', code)

        # Ensure the code is uppercase
        code = code.upper()

        # Check if this code is already in use IN THIS SCHOOL
        original_code = code
        counter = 1

        while Programme.objects.filter(
            school=self.school,
            code=code
        ).exists():
            # Code exists in this school - create a unique one by adding a number
            code = f"{original_code}{counter}"
            counter += 1

        return code

    def save(self, *args, **kwargs):
        """Override save to ensure clean is called"""
        self.clean()
        super().save(*args, **kwargs)


class Class(models.Model):
    """Students classes"""

    class EducationalStage(models.TextChoices):
        KINDERGARTEN = 'KG', _('Kindergarten')
        PRIMARY = 'PR', _('Primary School')
        JHS = 'JHS', _('Junior High School')
        SHS = 'SHS', _('Senior High School')

    # School relationship - essential for multi-tenant isolation
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='classes',
        verbose_name=_("School")
    )

    # Stage information
    stage = models.CharField(
        max_length=5,
        choices=EducationalStage.choices,
        db_index=True,
        verbose_name=_("Educational Stage")
    )
    stream = models.CharField(
        max_length=128,
        verbose_name=_("Stream"),
        help_text=_("Stream/section designation (e.g., 'A', 'Gold')")
    )
    # levels within the stage
    level = models.PositiveSmallIntegerField(
        verbose_name=_("Level"),
        help_text=_(
            "Numerical ordering within stage (1-6 for primary, 1-3 for JHS/SHS)"),
        validators=[
            MinValueValidator(1),
            MaxValueValidator(6)
        ]
    )
    programme = models.ForeignKey(
        Programme,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='classes',
        verbose_name=_("Programme"),
        help_text=_("For SHS only (e.g. Science, Arts etc.)")
    )
    max_students = models.PositiveIntegerField(
        default=50,
        verbose_name=_("Maximum Students"),
        help_text=_("Maximum number of students allowed in this class")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Whether this class is active in the current academic year")
    )

    # Define stage-specific maximum order values
    STAGE_LIMITS = {
        EducationalStage.KINDERGARTEN: 2,
        EducationalStage.PRIMARY: 6,
        EducationalStage.JHS: 3,
        EducationalStage.SHS: 3
    }

    # Define stage-level mappings
    STAGE_LEVEL_PREFIX = {
        EducationalStage.KINDERGARTEN: 'KG',
        EducationalStage.PRIMARY: 'P',
        EducationalStage.JHS: 'JHS',
        EducationalStage.SHS: 'SHS'
    }

    class Meta:
        ordering = ['stage', 'level', 'stream']
        # Make class unique within a school by stage, level, stream and programme
        unique_together = [['school', 'stage', 'level', 'stream', 'programme']]
        verbose_name = _("Class")
        verbose_name_plural = _("Classes")
        indexes = [
            models.Index(fields=['stage']),
            # Add school index for faster lookups
            models.Index(fields=['school']),
            models.Index(fields=['is_active']),  # For filtering active classes
            # Common query pattern
            models.Index(fields=['school', 'stage', 'level']),
        ]

    def __str__(self):
        """
        Display class like KG1A, P3B, JHS2C, SHS3 Science Gold
        """
        prefix = self.STAGE_LEVEL_PREFIX.get(self.stage, '')

        if self.stage == self.EducationalStage.SHS and self.programme:
            return f"{prefix}{self.level} {self.programme.code} {self.stream}"
        else:
            return f"{prefix}{self.level}{self.stream}"

    def clean(self):
        """Validate Ghana-specific grade rules with school context"""
        # Validate level ranges
        max_level = self.STAGE_LIMITS.get(self.stage)
        if self.level > max_level:
            raise ValidationError({
                'level': _("Maximum level for %(stage)s is %(max_level)s") % {
                    'stage': self.get_stage_display(),
                    'max_level': max_level
                }
            })

        # Validate programme is provided for SHS only
        if self.stage == self.EducationalStage.SHS and not self.programme:
            raise ValidationError({
                'programme': _("Programme is required for Senior High School classes")
            })
        elif self.stage != self.EducationalStage.SHS and self.programme:
            raise ValidationError({
                'programme': _("Programme should only be specified for Senior High School classes")
            })

        # Validate that the programme belongs to the same school
        if self.programme and self.programme.school_id != self.school_id:
            raise ValidationError({
                'programme': _("The programme must belong to the same school as the class")
            })

        # Check for duplicate class within the same school
        if not self.pk:  # Only check on creation
            existing = Class.objects.filter(
                school=self.school,
                stage=self.stage,
                level=self.level,
                stream=self.stream
            )

            # For SHS, we need to include programme in the uniqueness check
            if self.stage == self.EducationalStage.SHS:
                existing = existing.filter(programme=self.programme)

            if existing.exists():
                raise ValidationError(
                    _("A class with these details already exists in this school"))

    def save(self, *args, **kwargs):
        """Validate before saving"""
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def current_enrollment(self):
        """Get current student count in this class (cached for efficiency)"""
        if not hasattr(self, '_enrollment_count'):
            self._enrollment_count = self.students.count()
        return self._enrollment_count

    @property
    def is_full(self):
        """Check if class has reached maximum capacity"""
        return self.current_enrollment >= self.max_students

    @property
    def display_name(self):
        """Returns the formatted class name"""
        return self.__str__()

    @property
    def available_seats(self):
        """Returns number of available seats in the class"""
        return max(0, self.max_students - self.current_enrollment)

    @property
    def capacity_percentage(self):
        """Returns the percentage of class capacity filled"""
        if self.max_students > 0:
            return (self.current_enrollment / self.max_students) * 100
        return 0


class Guardian(TimeStampedModel):
    """Student Guardian model"""
    TITLE_CHOICES = (
        ('Mr.', 'Mr.'),
        ('Mrs.', 'Mrs.'),
        ('Ms.', 'Ms.'),
        ('Miss', 'Miss'),
        ('Dr.', 'Dr.'),
        ('Prof.', 'Prof.'),
        ('Rev.', 'Rev.'),
        ('Sheikh', 'Sheikh'),
        ('Maulvi', 'Maulvi'),
        ('Mallam', 'Mallam')
    )

    title = models.CharField(max_length=16, choices=TITLE_CHOICES)
    name = models.CharField(max_length=128)
    phone = models.CharField(max_length=15, validators=[PHONE_VALIDATOR])
    email = models.EmailField(blank=True, null=True)
    address = models.CharField(max_length=255)
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="guardians"
    )
    # Added user relationship for portal access
    user = models.OneToOneField(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='guardian_profile'
    )

    class Meta:
        verbose_name = 'guardian'
        verbose_name_plural = 'guardians'
        indexes = [
            models.Index(fields=['phone']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.title} {self.get_name()}"

    def get_name(self):
        return f"{self.name}"


class Student(Person, IDGenerationMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student_id = models.CharField(max_length=20, unique=True, blank=True)
    year_admitted = models.PositiveIntegerField(default=timezone.now().year)
    current_class = models.ForeignKey(
        Class,
        on_delete=models.PROTECT,
        related_name="students"
    )
    guardians = models.ManyToManyField(
        Guardian,
        through='StudentGuardian',
        related_name='wards'
    )
    # Additional fields for academic tracking
    status = models.CharField(
        max_length=20,
        choices=(
            ('active', 'Active'),
            ('graduated', 'Graduated'),
            ('withdrawn', 'Withdrawn'),
            ('suspended', 'Suspended'),
            ('transferred', 'Transferred'),
        ),
        default='active'
    )

    id_field = 'student_id'
    ID_PREFIX = 'STU'

    class Meta:
        indexes = [
            models.Index(fields=['student_id']),
            models.Index(fields=['school', 'year_admitted']),
            models.Index(fields=['status'])
        ]
        verbose_name = 'student'
        verbose_name_plural = 'students'

    def save(self, *args, **kwargs):
        if not self.student_id:
            self.student_id = self.generate_id()
        super().save(*args, **kwargs)

    @property
    def is_active_student(self):
        """Check if student is currently active"""
        return self.status == 'active'


class StudentGuardian(TimeStampedModel):
    """Model for many-to-many rel. between students and guardians"""
    RELATIONSHIP_CHOICES = (
        ('parent', 'Parent'),
        ('guardian', 'Guardian'),
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('uncle', 'Uncle'),
        ('aunt', 'Aunt'),
        ('grandparent', 'Grandparent'),
        ('sibling', 'Sibling'),
        ('other', 'Other'),
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="student_guardians"
    )
    guardian = models.ForeignKey(
        Guardian,
        on_delete=models.CASCADE,
        related_name="guardian_students"
    )
    relationship = models.CharField(
        max_length=20,
        choices=RELATIONSHIP_CHOICES,
        default='guardian'
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Indicates if this guardian is the primary contact for the student"
    )
    can_pickup = models.BooleanField(
        default=True,
        help_text="Indicates if this guardian is authorized to pickup the student"
    )
    emergency_contact = models.BooleanField(
        default=False,
        help_text="Indicates if this guardian is an emergency contact"
    )

    class Meta:
        verbose_name = 'student guardian relationship'
        verbose_name_plural = 'student guardian relationships'
        unique_together = ('student', 'guardian')
        indexes = [
            models.Index(fields=['student', 'is_primary']),
            models.Index(fields=['guardian', 'relationship']),
        ]

    def __str__(self):
        return f"{self.guardian} is {self.relationship} of {self.student}"

    def save(self, *args, **kwargs):
        # If this guardian is being set as primary, unset any existing primary guardians
        if self.is_primary:
            StudentGuardian.objects.filter(
                student=self.student,
                is_primary=True
            ).exclude(
                pk=self.pk
            ).update(
                is_primary=False
            )
        super().save(*args, **kwargs)


class AcademicYear(TimeStampedModel):
    """Academic year model for tracking school years"""
    year = models.CharField(
        max_length=9,
        unique=True,
        help_text="Academic year (e.g., '2024-2025')"
    )
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ['-year']

    def __str__(self):
        return self.year

    def clean(self):
        """Validate academic year dates"""
        if self.end_date <= self.start_date:
            raise ValidationError("End date must be after start date")

        # Format validation for year field (YYYY-YYYY)
        import re
        if not re.match(r'^\d{4}-\d{4}$', self.year):
            raise ValidationError("Year must be in format 'YYYY-YYYY'")

        start_year, end_year = self.year.split('-')
        if int(end_year) != int(start_year) + 1:
            raise ValidationError("End year must be one year after start year")

    def save(self, *args, **kwargs):
        """Ensure only one current academic year"""
        if self.is_current:
            # Set all other academic years to not current
            AcademicYear.objects.exclude(pk=self.pk).update(is_current=False)

        self.full_clean()
        super().save(*args, **kwargs)


class Enrollment(TimeStampedModel):
    """Student enrollment in a specific grade level for an academic year"""
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    grade_level = models.ForeignKey(
        Class,
        on_delete=models.PROTECT,
        related_name='enrollments'
    )
    date_enrolled = models.DateField(default=timezone.now)
    status = models.CharField(
        max_length=20,
        choices=(
            ('active', 'Active'),
            ('completed', 'Completed'),
            ('withdrawn', 'Withdrawn'),
            ('promoted', 'Promoted'),
            ('repeated', 'Repeated'),
        ),
        default='active'
    )

    class Meta:
        unique_together = ['student', 'academic_year']
        indexes = [
            models.Index(fields=['student', 'academic_year']),
            models.Index(fields=['grade_level', 'academic_year']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.student} - {self.grade_level} ({self.academic_year})"


class StudentVoucher(BaseVoucher):
    """Voucher model for registration of students"""
    # Class the student will be registered in
    grade_level = models.ForeignKey(
        'Class',
        on_delete=models.CASCADE,
        related_name='student_vouchers'
    )
    # Add specific relationship to Student
    used_by = models.OneToOneField(
        'Student',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='registration_voucher'
    )

    def __str__(self):
        status = "Used" if self.is_used else "Unused"
        return f"Student Voucher: {self.serial_number} - {self.grade_level} ({status})"

    def mark_as_used_by(self, student):
        """Mark voucher as used by a specific student"""
        self.used_by = student
        self.mark_as_used()

    def get_prefix(self):
        """Return the prefix for student vouchers"""
        return "S"

    class Meta(BaseVoucher.Meta):
        verbose_name = "Student Voucher"
        verbose_name_plural = "Student Vouchers"

    """Voucher model for registration of guardians"""

    # Add specific relationship to Guardian
    used_by_guardian = models.OneToOneField(
        'Guardian',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='registration_voucher'
    )

    # Other methods remain the same

    def mark_as_used_by_guardian(self, guardian):
        """Mark voucher as used by a specific guardian"""
        self.used_by_guardian = guardian
        self.mark_as_used()
