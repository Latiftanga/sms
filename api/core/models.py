from django.utils.text import slugify
import uuid
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin
)
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import (
    AbstractBaseUser, PermissionsMixin, BaseUserManager
)
from django.core.validators import RegexValidator, MinLengthValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
import string
import secrets
import random


# Validators
PHONE_VALIDATOR = RegexValidator(
    regex=r'^\+?\d{10,15}$',
    message="Phone number must be 10-15 digits, optionally starting with '+'"
)

GHANA_CARD_VALIDATOR = RegexValidator(
    regex=r'^GHA-\d{9}-\d$',
    message="Ghana Card must follow format: GHA-123456789-1"
)


# Abstracts
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
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


class School(models.Model):
    SCHOOL_TYPE_CHOICES = [
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
    school_type = models.CharField(max_length=20, choices=SCHOOL_TYPE_CHOICES)
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

    # Additional information
    has_boarding = models.BooleanField(
        "Offers Boarding Facilities", default=False)

    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = 'School'
        verbose_name_plural = 'Schools'


class Person(TimeStampedModel):
    GENDER_CHOICES = (('M', 'Male'), ('F', 'Female'))
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="%(class)ss"
    )
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


class UserManager(BaseUserManager):
    """Manager for users"""

    def create_user(self, user_id, password=None, **extra_fields):
        """Create, save and return new user"""
        if not user_id:
            raise ValueError('User must have a user ID')
        user = self.model(user_id=user_id, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, user_id, password):
        """Create and return a new superuser"""
        user = self.create_user(user_id, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

    def create_adminuser(self, user_id, password):
        """Create and return a new admin user"""
        user = self.create_user(user_id, password)
        user.is_staff = True
        user.is_admin = True
        user.is_teacher = True
        user.save(using=self._db)
        return user

    def create_teacheruser(self, user_id):
        """Create and return a new teacher user"""
        # Generate random password
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(8))
        user = self.create_user(user_id, password)
        user.is_teacher = True
        user.save(using=self._db)
        return user, password

    def create_studentuser(self, user_id):
        """Create and return a new student user"""
        # Generate random password
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(8))
        user = self.create_user(user_id, password)
        user.is_student = True
        user.save(using=self._db)
        return user, password


class User(AbstractBaseUser, PermissionsMixin):
    """User in the system"""
    school = models.ForeignKey(
        School, on_delete=models.CASCADE,
        related_name='users', blank=True, null=True
    )
    user_id = models.CharField(max_length=32, unique=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_teacher = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'user_id'


class BaseVoucher(models.Model):
    """Base abstract voucher model"""
    serial_number = models.CharField(
        max_length=15, unique=True, editable=False)
    pin = models.CharField(max_length=12, editable=False)
    school = models.ForeignKey(
        School, on_delete=models.CASCADE, related_name='+')
    can_signin = models.BooleanField(default=False)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'core.User', on_delete=models.SET_NULL,
        null=True, related_name='+'
    )
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['serial_number']),
            models.Index(fields=['is_used']),
        ]
        ordering = ['-created_at']

    def mark_as_used(self):
        """Mark voucher as used"""
        from django.utils import timezone
        self.is_used = True
        self.used_at = timezone.now()
        self.save(update_fields=['is_used', 'used_at'])

    def _generate_serial_number(self, prefix):
        """Generate a unique serial number with the given prefix"""
        school_prefix = self.school.name[:3].upper()
        unique_id = uuid.uuid4().hex[:8].upper()
        return f"{prefix}{school_prefix}-{unique_id}"

    def _generate_pin(self):
        """Generate a PIN number"""
        return ''.join(random.choices(string.digits, k=12))

    def save(self, *args, **kwargs):
        """
        Override save method to automatically generate serial_number and pin
        Child classes should call super().save() after setting their prefix
        """
        # If no serial_number exists, generate one using child class's prefix
        if not self.serial_number:
            # This method should be overridden by child classes to provide their prefix
            prefix = self.get_prefix()
            self.serial_number = self._generate_serial_number(prefix)

        # If no pin exists, generate one
        if not self.pin:
            self.pin = self._generate_pin()

        super().save(*args, **kwargs)

    def get_prefix(self):
        """
        Method to be implemented by child classes to specify their prefix
        """
        raise NotImplementedError("Child classes must implement get_prefix()")
