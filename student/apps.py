from django.apps import AppConfig


class StudentConfig(AppConfig):
    name = 'student'
    verbose_name = 'Student Management'

    def ready(self):
        """Import signals when the app is ready"""
        try:
            import student.signals
        except ImportError:
            pass