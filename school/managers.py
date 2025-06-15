from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    """Custom user manager for Django authentication"""

    def create_user(self, username, email=None, password=None, **extra_fields):
        """Create and save a regular user"""
        if not username:
            raise ValueError('The username field must be set')

        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)

        if email:
            email = self.normalize_email(email)

        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """Create and save a superuser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)

    # Convenience methods for school-specific user creation
    def create_student_user(self, student_id, password, email=None):
        """Create a student user"""
        if not student_id:
            raise ValueError('Students must have a student_id')

        return self.create_user(
            username=student_id,
            email=email,
            password=password,
            is_student=True
        )

    def create_teacher_user(self, teacher_id, password, email=None, is_admin=False):
        """Create a teacher user"""
        if not teacher_id:
            raise ValueError('Teachers must have a teacher_id')

        return self.create_user(
            username=teacher_id,
            email=email,
            password=password,
            is_teacher=True,
            is_admin=is_admin,
            is_staff=is_admin
        )
