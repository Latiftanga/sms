from school.models import (
    School, AcademicYear, Programme, House, Subject,
)
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from school.models import School, AcademicYear, Programme, House, Subject
from account.models import User


class Command(BaseCommand):
    help = 'Set up initial school data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--school-name',
            default='T. I. Ahmadiyya SHS',
            help='School name',
        )
        parser.add_argument(
            '--school-code',
            default='TTEK',
            help='School code',
        )
        parser.add_argument(
            '--admin-username',
            default='admin',
            help='Admin username',
        )
        parser.add_argument(
            '--admin-password',
            default='admin123',
            help='Admin password',
        )
        parser.add_argument(
            '--academic-year',
            type=int,
            default=timezone.now().year,
            help='Academic year',
        )

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                # Update school information
                school = School.get_current_school()
                school.name = options['school_name']
                school.code = options['school_code']
                school.email = 'admin@school.edu.gh'
                school.phone = '0244000000'
                school.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Updated school: {school.name}')
                )

                # Create academic year
                year = options['academic_year']
                academic_year, created = AcademicYear.objects.get_or_create(
                    year=year,
                    defaults={
                        'start_date': timezone.datetime(year, 9, 1).date(),
                        'end_date': timezone.datetime(year + 1, 8, 31).date(),
                        'is_current': True
                    }
                )
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'Created academic year: {year}')
                    )

                # Create programmes
                programmes_data = [
                    'General Arts',
                    'Business',
                    'General Science',
                    'Visual Arts',
                ]

                for prog_name in programmes_data:
                    programme, created = Programme.objects.get_or_create(
                        name=prog_name
                    )
                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Created programme: {prog_name}')
                        )

                # Create houses
                houses_data = [
                    ('Red House', '#DC2626'),
                    ('Blue House', '#2563EB'),
                    ('Green House', '#16A34A'),
                    ('Yellow House', '#EAB308'),
                ]

                for house_name, color in houses_data:
                    house, created = House.objects.get_or_create(
                        name=house_name,
                        defaults={'color': color}
                    )
                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(f'Created house: {house_name}')
                        )

                # Create basic subjects
                subjects_data = [
                    ('English Language', 'core'),
                    ('Mathematics', 'core'),
                    ('Integrated Science', 'core'),
                    ('Social Studies', 'core'),
                    ('Physics', 'elective'),
                    ('Chemistry', 'elective'),
                    ('Biology', 'elective'),
                    ('Literature', 'elective'),
                    ('Economics', 'elective'),
                    ('Geography', 'elective'),
                    ('History', 'elective'),
                    ('Government', 'elective'),
                ]

                for subject_name, subject_type in subjects_data:
                    subject, created = Subject.objects.get_or_create(
                        name=subject_name,
                        defaults={'subject_type': subject_type}
                    )
                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Created subject: {subject_name}')
                        )

                # Create admin user
                username = options['admin_username']
                password = options['admin_password']

                if not User.objects.filter(username=username).exists():
                    user = User.objects.create_user(
                        username=username,
                        password=password,
                        email='admin@school.edu.gh',
                        is_admin=True,
                        is_staff=True,
                        is_superuser=True
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f'Created admin user: {username}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Admin user {username} already exists')
                    )

                self.stdout.write(
                    self.style.SUCCESS(
                        '\nSchool setup completed successfully!')
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'You can now login with username: {username}')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Setup failed: {str(e)}')
            )
