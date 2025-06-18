from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from school.models import Student
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(post_save, sender=Student)
def student_post_save(sender, instance, created, **kwargs):
    """Handle post-save operations for Student model"""
    if created and not instance.user:
        # Auto-create user account for new students
        try:
            from account.models import create_student_with_user
            create_student_with_user(
                first_name=instance.first_name,
                last_name=instance.last_name,
                year_admitted=instance.year_admitted,
                email=instance.email
            )
        except Exception:
            # Fail silently if user creation fails
            pass


@receiver(pre_delete, sender=Student)
def student_pre_delete(sender, instance, **kwargs):
    """Handle pre-delete operations for Student model"""
    # Deactivate associated user account instead of deleting
    if instance.user:
        instance.user.is_active = False
        instance.user.save()
