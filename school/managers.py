from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    """"Manage for users"""

    def create_user(self, email, password=None, **extra_fields):
        """Create, save and return new user"""
        if not email:
            raise ValueError('User must have an email address')
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        """Create and return a new superuser"""
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

    def create_adminuser(self, email, password):
        """Create and return a new admin user"""
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_admin = True
        user.save(using=self._db)
        return user

    def create_teacheruser(self, email, password):
        """Create and return a new teacher user"""
        user = self.create_user(email, password)
        user.is_teacher = True
        user.save(using=self._db)
        return user

    def create_studentuser(self, email, password):
        """Create and return a new student user"""
        user = self.create_user(email, password)
        user.is_teacher = True
        user.save(using=self._db)
        return user
