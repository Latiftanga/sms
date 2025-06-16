# File: apps/accounts/models.py
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from account.managers import UserManager
import string
import random
from school.models import Teacher


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User model for Django authentication"""

    # Core fields required by Django
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)

    # Permission fields (from PermissionsMixin)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    # School-specific fields
    is_teacher = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    # Timestamps
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Required for Django authentication
    objects = UserManager()
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

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

    def get_user_type(self):
        """Get user type as string"""
        if self.is_superuser:
            return 'Super Admin'
        elif self.is_admin:
            return 'Admin'
        elif self.is_teacher:
            return 'Teacher'
        elif self.is_student:
            return 'Student'
        return 'User'

    def __str__(self):
        full_name = self.get_full_name()
        if full_name != self.username:
            return f"{full_name} ({self.username})"
        return self.username


# Helper Functions
def generate_random_password(length=8):
    """Generate a random password"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


def create_student_with_user(
    first_name, last_name, year_admitted,
    password=None, email=None, **student_data):
    """Create both User account AND Student profile"""
    from school.models import Student
    from account.models import User

    if not password:
        password = generate_random_password()

    student = Student(
        first_name=first_name,
        last_name=last_name,
        year_admitted=year_admitted,
        email=email,
        **student_data
    )
    student.save()

    user = User.objects.create_student_user(
        student_id=student.student_id,
        password=password,
        email=email
    )

    student.user = user
    student.save()

    return {
        'student': student,
        'username': student.student_id,
        'password': password,
        'student_id': student.student_id
    }


def create_teacher_with_user(
    first_name, last_name, date_of_employment,
    password=None, email=None, is_admin=False, **teacher_data
):
    """Create both User account AND Teacher profile"""
    from account.models import User

    if not password:
        password = generate_random_password()

    teacher = Teacher(
        first_name=first_name,
        last_name=last_name,
        date_of_employment=date_of_employment,
        email=email,
        **teacher_data
    )
    teacher.save()

    user = User.objects.create_teacher_user(
        teacher_id=teacher.teacher_id,
        password=password,
        email=email,
        is_admin=is_admin
    )

    teacher.user = user
    teacher.save()

    return {
        'teacher': teacher,
        'username': teacher.teacher_id,
        'password': password,
        'teacher_id': teacher.teacher_id
    }
