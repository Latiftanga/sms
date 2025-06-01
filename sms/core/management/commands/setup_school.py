# management/commands/setup_school.py
import csv
import secrets
import string
import random
from django.utils import timezone
from django.core.management.base import BaseCommand
import os
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.conf import settings
from core.models import School

User = get_user_model()


class Command(BaseCommand):
    help = 'Setup initial school data for T. I. Ahmadiyya SHS'

    def add_arguments(self, parser):
        parser.add_argument(
            '--admin-username',
            type=str,
            default='admin',
            help='Username for the admin user'
        )
        parser.add_argument(
            '--admin-password',
            type=str,
            default='adminpass123',
            help='Password for the admin user'
        )
        parser.add_argument(
            '--skip-superuser',
            action='store_true',
            help='Skip creating superuser'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(
            'Setting up T. I. Ahmadiyya SHS...'))

        # Create school record
        self.create_school()

        # Create superuser if requested
        if not options['skip_superuser']:
            self.create_admin_user(
                options['admin_username'], options['admin_password'])

        self.stdout.write(self.style.SUCCESS(
            'School setup completed successfully!'))

    def create_school(self):
        """Create the school record"""
        school, created = School.objects.get_or_create(
            name="T. I. Ahmadiyya Senior High School, Wa",
            defaults={
                'school_type': 'shs',
                'ownership': 'mission',
                'region': 'upper_west',
                'district': 'Wa Municipal',
                'town': 'Wa',
                'headmaster_name': 'To Be Updated',
                'email': 'info@ahmadiyyashs-wa.edu.gh',
                'phone_primary': '',
                'motto': 'Love for All, Hatred for None',
                'is_active': True,
                'has_boarding': True,
            }
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created school: {school.name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'School already exists: {school.name}')
            )

    def create_admin_user(self, username, password):
        """Create admin user"""
        try:
            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(
                        f'Admin user "{username}" already exists')
                )
                return

            admin_user = User.objects.create_user(
                username=username,
                password=password,
                email='admin@ahmadiyyashs-wa.edu.gh'
            )
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.is_admin = True
            admin_user.save()

            self.stdout.write(
                self.style.SUCCESS(f'Created admin user: {username}')
            )
            self.stdout.write(
                self.style.WARNING(f'Admin password: {password}')
            )
            self.stdout.write(
                self.style.WARNING(
                    'Please change the admin password after first login!')
            )

        except Exception as e:
            raise CommandError(f'Error creating admin user: {e}')


# management/commands/create_demo_data.py

User = get_user_model()


class Command(BaseCommand):
    help = 'Create demo data for testing the school management system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--teachers',
            type=int,
            default=10,
            help='Number of demo teachers to create'
        )
        parser.add_argument(
            '--students',
            type=int,
            default=50,
            help='Number of demo students to create'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating demo data...'))

        # Ensure school exists
        school = School.objects.first()
        if not school:
            self.stdout.write(
                self.style.ERROR(
                    'No school found. Please run setup_school command first.')
            )
            return

        # Create demo teachers
        self.create_demo_teachers(options['teachers'])

        # Create demo students
        self.create_demo_students(options['students'])

        self.stdout.write(self.style.SUCCESS(
            'Demo data created successfully!'))

    def create_demo_teachers(self, count):
        """Create demo teacher accounts"""
        teacher_names = [
            'John Doe', 'Jane Smith', 'Michael Johnson', 'Sarah Wilson',
            'David Brown', 'Emma Davis', 'Robert Miller', 'Lisa Anderson',
            'William Taylor', 'Jennifer Thomas', 'James Jackson', 'Mary White',
            'Christopher Harris', 'Patricia Martin', 'Daniel Thompson'
        ]

        created_count = 0
        for i in range(count):
            if i < len(teacher_names):
                full_name = teacher_names[i]
            else:
                full_name = f"Teacher {i+1}"

            first_name = full_name.split()[0]
            last_name = full_name.split()[-1]
            username = f"teacher_{first_name.lower()}_{last_name.lower()}"

            if not User.objects.filter(username=username).exists():
                user, password = User.objects.create_teacheruser(username)
                user.email = f"{username}@ahmadiyyashs-wa.edu.gh"
                user.save()
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Created {created_count} demo teachers')
        )

    def create_demo_students(self, count):
        """Create demo student accounts"""
        first_names = [
            'Amina', 'Kwame', 'Fatima', 'Ibrahim', 'Aisha', 'Kofi', 'Zainab', 'Abdul',
            'Salamatu', 'Mohammed', 'Mariam', 'Yusuf', 'Khadija', 'Ahmed', 'Hafsa',
            'Idris', 'Rukaya', 'Suleiman', 'Aishah', 'Abdulrahman', 'Maryam', 'Usman',
            'Zulaiha', 'Ismail', 'Halima', 'Yakubu', 'Safiya', 'Musa', 'Amara', 'Dawud'
        ]

        last_names = [
            'Mohammed', 'Abdul', 'Ibrahim', 'Ahmed', 'Yusuf', 'Hassan', 'Hussein',
            'Ali', 'Omar', 'Fatima', 'Kone', 'Diallo', 'Bello', 'Salihu', 'Yakubu',
            'Musa', 'Dawud', 'Ismail', 'Suleiman', 'Abdulrahman', 'Aminu', 'Salisu'
        ]

        created_count = 0
        for i in range(count):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            username = f"student_{first_name.lower()}_{last_name.lower()}_{i+1}"

            if not User.objects.filter(username=username).exists():
                user, password = User.objects.create_studentuser(username)
                user.email = f"{username}@student.ahmadiyyashs-wa.edu.gh"
                user.save()
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Created {created_count} demo students')
        )


# management/commands/reset_passwords.py

User = get_user_model()


class Command(BaseCommand):
    help = 'Reset passwords for users and generate new ones'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-type',
            choices=['teacher', 'student', 'admin', 'all'],
            default='all',
            help='Type of users to reset passwords for'
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Reset password for specific user'
        )

    def handle(self, *args, **options):
        if options['username']:
            self.reset_user_password(options['username'])
        else:
            self.reset_passwords_by_type(options['user_type'])

    def reset_user_password(self, username):
        """Reset password for specific user"""
        try:
            user = User.objects.get(username=username)
            new_password = self.generate_password()
            user.set_password(new_password)
            user.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f'Password reset for {username}: {new_password}')
            )
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User {username} not found')
            )

    def reset_passwords_by_type(self, user_type):
        """Reset passwords by user type"""
        if user_type == 'teacher':
            users = User.objects.filter(is_teacher=True)
        elif user_type == 'student':
            users = User.objects.filter(is_student=True)
        elif user_type == 'admin':
            users = User.objects.filter(is_admin=True)
        else:
            users = User.objects.filter(
                is_active=True).exclude(is_superuser=True)

        reset_count = 0
        for user in users:
            new_password = self.generate_password()
            user.set_password(new_password)
            user.save()

            self.stdout.write(
                self.style.SUCCESS(f'{user.username}: {new_password}')
            )
            reset_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Reset passwords for {reset_count} users')
        )

    def generate_password(self):
        """Generate a random password"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(8))


# management/commands/export_users.py

User = get_user_model()


class Command(BaseCommand):
    help = 'Export user data to CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='users_export.csv',
            help='Output CSV file name'
        )
        parser.add_argument(
            '--user-type',
            choices=['teacher', 'student', 'admin', 'all'],
            default='all',
            help='Type of users to export'
        )

    def handle(self, *args, **options):
        filename = options['output']
        user_type = options['user_type']

        # Filter users based on type
        if user_type == 'teacher':
            users = User.objects.filter(is_teacher=True)
        elif user_type == 'student':
            users = User.objects.filter(is_student=True)
        elif user_type == 'admin':
            users = User.objects.filter(is_admin=True)
        else:
            users = User.objects.all()

        # Export to CSV
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'username', 'email', 'user_type', 'is_active',
                'date_joined', 'last_login'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for user in users:
                user_type_display = 'Superuser' if user.is_superuser else \
                    'Admin' if user.is_admin else \
                    'Teacher' if user.is_teacher else \
                    'Student' if user.is_student else 'User'

                writer.writerow({
                    'username': user.username,
                    'email': user.email or '',
                    'user_type': user_type_display,
                    'is_active': user.is_active,
                    'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                    'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never'
                })

        self.stdout.write(
            self.style.SUCCESS(f'Exported {users.count()} users to {filename}')
        )
