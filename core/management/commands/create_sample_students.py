# File: student/management/commands/create_sample_students.py
import os
from student.utils import export_students_to_csv
from school.models import Student
from student.utils import promote_students
from school.models import Student, Class
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from faker import Faker
import random

from school.models import Student, Class, House
from account.models import create_student_with_user


class Command(BaseCommand):
    help = 'Create sample students for testing purposes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Number of students to create (default: 50)'
        )
        parser.add_argument(
            '--year',
            type=int,
            default=timezone.now().year,
            help='Year admitted (default: current year)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing sample students before creating new ones'
        )

    def handle(self, *args, **options):
        fake = Faker()
        count = options['count']
        year_admitted = options['year']
        clear_existing = options['clear']

        if clear_existing:
            self.stdout.write('Clearing existing sample students...')
            # Only delete students with fake-looking names or specific pattern
            Student.objects.filter(
                first_name__in=['John', 'Jane', 'Test', 'Sample']
            ).delete()

        # Get available classes and houses
        classes = list(Class.objects.all())
        houses = list(House.objects.all())

        if not classes:
            self.stdout.write(
                self.style.ERROR(
                    'No classes found. Please create classes first.')
            )
            return

        if not houses:
            self.stdout.write(
                self.style.ERROR(
                    'No houses found. Please create houses first.')
            )
            return

        self.stdout.write(f'Creating {count} sample students...')

        success_count = 0
        error_count = 0

        with transaction.atomic():
            for i in range(count):
                try:
                    # Generate fake data
                    gender = random.choice(['M', 'F'])
                    first_name = fake.first_name_male() if gender == 'M' else fake.first_name_female()
                    last_name = fake.last_name()

                    # Generate age-appropriate birth date (14-18 years old)
                    birth_year = timezone.now().year - random.randint(14, 18)
                    date_of_birth = fake.date_between(
                        start_date=f'{birth_year}-01-01',
                        end_date=f'{birth_year}-12-31'
                    )

                    student_data = {
                        'middle_name': fake.first_name() if random.choice([True, False]) else None,
                        'gender': gender,
                        'date_of_birth': date_of_birth,
                        'email': fake.email() if random.choice([True, False]) else None,
                        'phone': fake.phone_number()[:15] if random.choice([True, False]) else None,
                        'address': fake.address() if random.choice([True, False]) else None,
                        'current_class': random.choice(classes),
                        'house': random.choice(houses),
                        'guardian_name': fake.name(),
                        'guardian_phone': fake.phone_number()[:15],
                        'guardian_email': fake.email() if random.choice([True, False]) else None,
                        'relationship_to_guardian': random.choice([
                            'Father', 'Mother', 'Uncle', 'Aunt', 'Grandfather',
                            'Grandmother', 'Brother', 'Sister', 'Guardian'
                        ])
                    }

                    # Create student with user account
                    result = create_student_with_user(
                        first_name=first_name,
                        last_name=last_name,
                        year_admitted=year_admitted,
                        **student_data
                    )

                    success_count += 1

                    if (i + 1) % 10 == 0:
                        self.stdout.write(
                            f'Created {i + 1}/{count} students...')

                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'Error creating student {i + 1}: {str(e)}')
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {success_count} students. '
                f'{error_count} errors occurred.'
            )
        )


# File: student/management/commands/promote_students.py


class Command(BaseCommand):
    help = 'Promote students from one class to another'

    def add_arguments(self, parser):
        parser.add_argument(
            '--from-class',
            type=str,
            required=True,
            help='Source class name or ID'
        )
        parser.add_argument(
            '--to-class',
            type=str,
            required=True,
            help='Target class name or ID'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Promote all students from the source class'
        )
        parser.add_argument(
            '--student-ids',
            nargs='+',
            help='Specific student IDs to promote'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be promoted without making changes'
        )

    def handle(self, *args, **options):
        from_class_identifier = options['from_class']
        to_class_identifier = options['to_class']
        promote_all = options['all']
        student_ids = options.get('student_ids', [])
        dry_run = options['dry_run']

        # Get classes
        try:
            # Try to get class by ID first, then by name
            try:
                from_class = Class.objects.get(id=int(from_class_identifier))
            except (ValueError, Class.DoesNotExist):
                from_class = Class.objects.get(name=from_class_identifier)

            try:
                to_class = Class.objects.get(id=int(to_class_identifier))
            except (ValueError, Class.DoesNotExist):
                to_class = Class.objects.get(name=to_class_identifier)

        except Class.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f'Class not found: {str(e)}'))
            return

        # Get students to promote
        if promote_all:
            students = Student.objects.filter(
                current_class=from_class, is_active=True)
        elif student_ids:
            students = Student.objects.filter(
                student_id__in=student_ids,
                current_class=from_class,
                is_active=True
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    'Please specify either --all or --student-ids')
            )
            return

        if not students.exists():
            self.stdout.write(
                self.style.WARNING('No students found matching criteria')
            )
            return

        self.stdout.write(f'Found {students.count()} students to promote:')
        for student in students:
            self.stdout.write(
                f'  - {student.get_full_name()} ({student.student_id})')

        self.stdout.write(f'From: {from_class}')
        self.stdout.write(f'To: {to_class}')

        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN: No changes will be made')
            )
            return

        # Confirm promotion
        confirm = input('Proceed with promotion? (y/N): ')
        if confirm.lower() != 'y':
            self.stdout.write('Promotion cancelled')
            return

        # Perform promotion
        result = promote_students(students, to_class)

        if result['errors']:
            self.stdout.write(self.style.WARNING('Errors occurred:'))
            for error in result['errors']:
                self.stdout.write(f'  - {error}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully promoted {result["success_count"]} students'
            )
        )


# File: student/management/commands/export_students.py


class Command(BaseCommand):
    help = 'Export students to CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default=None,
            help='Output file path (default: students_export_YYYYMMDD.csv)'
        )
        parser.add_argument(
            '--class',
            type=str,
            dest='class_filter',
            help='Filter by class name or ID'
        )
        parser.add_argument(
            '--house',
            type=str,
            help='Filter by house name'
        )
        parser.add_argument(
            '--year',
            type=int,
            help='Filter by year admitted'
        )
        parser.add_argument(
            '--active-only',
            action='store_true',
            help='Export only active students'
        )

    def handle(self, *args, **options):
        # Build queryset based on filters
        queryset = Student.objects.all().select_related(
            'current_class', 'house', 'current_class__programme'
        )

        if options['active_only']:
            queryset = queryset.filter(is_active=True)

        if options['class_filter']:
            try:
                # Try by ID first, then by name
                try:
                    class_id = int(options['class_filter'])
                    queryset = queryset.filter(current_class_id=class_id)
                except ValueError:
                    queryset = queryset.filter(
                        current_class__name=options['class_filter'])
            except:
                self.stdout.write(
                    self.style.ERROR(
                        f"Class '{options['class_filter']}' not found")
                )
                return

        if options['house']:
            queryset = queryset.filter(house__name=options['house'])

        if options['year']:
            queryset = queryset.filter(year_admitted=options['year'])

        # Generate output filename
        if options['output']:
            output_file = options['output']
        else:
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'students_export_{timestamp}.csv'

        # Export to CSV
        try:
            csv_content = export_students_to_csv(queryset)

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(csv_content)

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully exported {queryset.count()} students to {output_file}'
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error exporting students: {str(e)}')
            )


# File: student/management/commands/fix_student_accounts.py


class Command(BaseCommand):
    help = 'Fix missing user accounts for students'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes'
        )
        parser.add_argument(
            '--create-missing',
            action='store_true',
            help='Create user accounts for students without accounts'
        )
        parser.add_argument(
            '--sync-data',
            action='store_true',
            help='Sync student data with user accounts'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        create_missing = options['create_missing']
        sync_data = options['sync_data']

        # Find students without user accounts
        students_without_accounts = Student.objects.filter(user__isnull=True)

        # Find students with inactive user accounts
        students_with_inactive_accounts = Student.objects.filter(
            user__isnull=False,
            user__is_active=False,
            is_active=True
        )

        self.stdout.write(
            f'Students without user accounts: {students_without_accounts.count()}')
        self.stdout.write(
            f'Students with inactive accounts: {students_with_inactive_accounts.count()}')

        if dry_run:
            self.stdout.write(self.style.WARNING(
                'DRY RUN: No changes will be made'))

            for student in students_without_accounts:
                self.stdout.write(
                    f'  Would create account for: {student.get_full_name()} ({student.student_id})')

            for student in students_with_inactive_accounts:
                self.stdout.write(
                    f'  Would activate account for: {student.get_full_name()} ({student.student_id})')

            return

        created_count = 0
        activated_count = 0
        error_count = 0

        # Create missing user accounts
        if create_missing:
            self.stdout.write('Creating missing user accounts...')

            for student in students_without_accounts:
                try:
                    with transaction.atomic():
                        from account.models import generate_random_password
                        from account.models import User

                        # Create user account
                        user = User.objects.create_student_user(
                            student_id=student.student_id,
                            password=generate_random_password(),
                            email=student.email
                        )

                        # Link to student
                        student.user = user
                        student.save()

                        created_count += 1
                        self.stdout.write(
                            f'  Created account for: {student.get_full_name()}')

                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'  Error creating account for {student.get_full_name()}: {str(e)}')
                    )

        # Activate inactive accounts for active students
        if sync_data:
            self.stdout.write('Syncing account status...')

            for student in students_with_inactive_accounts:
                try:
                    student.user.is_active = True
                    student.user.save()
                    activated_count += 1
                    self.stdout.write(
                        f'  Activated account for: {student.get_full_name()}')

                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'  Error activating account for {student.get_full_name()}: {str(e)}')
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'Completed: {created_count} accounts created, '
                f'{activated_count} accounts activated, '
                f'{error_count} errors'
            )
        )
