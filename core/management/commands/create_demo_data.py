# File: apps/school/management/commands/create_demo_data.py
from django.db import transaction
from django.core.management.base import BaseCommand
import random
from datetime import date, timedelta
from school.models import (
    School, AcademicYear, Programme, House, Class, Subject,
    Student, Teacher
)
from account.models import create_student_with_user, create_teacher_with_user

class Command(BaseCommand):
    help = 'Create demo data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--students',
            type=int,
            default=50,
            help='Number of students to create',
        )
        parser.add_argument(
            '--teachers',
            type=int,
            default=10,
            help='Number of teachers to create',
        )

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                self.stdout.write('Creating demo data...')

                # Ensure we have basic data
                school = School.get_current_school()
                academic_year = AcademicYear.objects.filter(
                    is_current=True).first()
                if not academic_year:
                    self.stdout.write(
                        self.style.ERROR(
                            'No current academic year found. Run setup_school first.')
                    )
                    return

                # Create classes if they don't exist
                programmes = Programme.objects.all()
                houses = House.objects.all()

                if not programmes.exists():
                    self.stdout.write(
                        self.style.ERROR(
                            'No programmes found. Run setup_school first.')
                    )
                    return

                # Create some classes
                levels = [1, 2, 3]
                sections = ['A', 'B']

                for level in levels:
                    for programme in programmes[:3]:  # First 3 programmes
                        for section in sections:
                            Class.objects.get_or_create(
                                level=level,
                                programme=programme,
                                name=section,
                                defaults={'capacity': 45}
                            )

                self.stdout.write(
                    self.style.SUCCESS('Created classes')
                )

                # Create demo teachers
                teacher_names = [
                    ('John', 'Doe', 'Mathematics Education'),
                    ('Jane', 'Smith', 'English Literature'),
                    ('Michael', 'Johnson', 'Physics'),
                    ('Sarah', 'Williams', 'Chemistry'),
                    ('David', 'Brown', 'Biology'),
                    ('Lisa', 'Davis', 'History'),
                    ('Robert', 'Miller', 'Geography'),
                    ('Mary', 'Wilson', 'Economics'),
                    ('James', 'Moore', 'Computer Science'),
                    ('Patricia', 'Taylor', 'Art Education'),
                ]

                subjects = list(Subject.objects.all())

                for i, (first_name, last_name, qualification) in enumerate(teacher_names[:options['teachers']]):
                    if not Teacher.objects.filter(first_name=first_name, last_name=last_name).exists():
                        employment_date = date.today() - timedelta(days=random.randint(30, 1000))

                        teacher_data = create_teacher_with_user(
                            first_name=first_name,
                            last_name=last_name,
                            date_of_employment=employment_date,
                            gender=random.choice(['M', 'F']),
                            date_of_birth=date.today() - timedelta(days=random.randint(8000, 15000)),
                            qualification=qualification,
                            years_of_experience=random.randint(1, 15),
                            phone=f"024{random.randint(1000000, 9999999)}",
                            email=f"{first_name.lower()}.{last_name.lower()}@school.edu.gh"
                        )

                        # Assign random subjects
                        teacher = teacher_data['teacher']
                        teacher.subjects.set(random.sample(
                            subjects, random.randint(1, 3)))

                        self.stdout.write(
                            f'Created teacher: {teacher.get_full_name()}')

                # Create demo students
                student_first_names = [
                    'Kwame', 'Ama', 'Kofi', 'Akosua', 'Kwaku', 'Adwoa', 'Yaw', 'Afia',
                    'Kwadwo', 'Akua', 'Fiifi', 'Efua', 'Kwabena', 'Abena', 'Kwesi', 'Esi',
                    'Emmanuel', 'Grace', 'Daniel', 'Patience', 'Samuel', 'Joyce', 'Isaac',
                    'Mercy', 'Joseph', 'Priscilla', 'Benjamin', 'Elizabeth', 'Francis',
                    'Mary', 'Prince', 'Ruth', 'Richard', 'Sarah', 'Stephen', 'Rebecca'
                ]

                student_last_names = [
                    'Asante', 'Boateng', 'Mensah', 'Owusu', 'Osei', 'Appiah', 'Adjei',
                    'Agyei', 'Frimpong', 'Gyamfi', 'Nkrumah', 'Bediako', 'Amoah',
                    'Wiredu', 'Donkor', 'Darkwa', 'Bonsu', 'Adusei', 'Yeboah', 'Acheampong'
                ]

                classes = list(Class.objects.all())
                houses_list = list(houses)

                for i in range(options['students']):
                    first_name = random.choice(student_first_names)
                    last_name = random.choice(student_last_names)

                    # Check if student already exists
                    if Student.objects.filter(first_name=first_name, last_name=last_name).exists():
                        continue

                    birth_date = date.today() - timedelta(days=random.randint(5000, 7000))

                    student_data = create_student_with_user(
                        first_name=first_name,
                        last_name=last_name,
                        year_admitted=academic_year.year,
                        gender=random.choice(['M', 'F']),
                        date_of_birth=birth_date,
                        phone=f"055{random.randint(1000000, 9999999)}",
                        guardian_name=f"{random.choice(['Mr.', 'Mrs.', 'Dr.'])} {random.choice(student_last_names)}",
                        guardian_phone=f"024{random.randint(1000000, 9999999)}",
                        relationship_to_guardian=random.choice(
                            ['Father', 'Mother', 'Guardian', 'Uncle', 'Aunt'])
                    )

                    student = student_data['student']

                    # Assign to random class and house
                    if classes:
                        student.current_class = random.choice(classes)
                    if houses_list:
                        student.house = random.choice(houses_list)
                    student.save()

                    if i % 10 == 0:
                        self.stdout.write(f'Created {i+1} students...')

                self.stdout.write(
                    self.style.SUCCESS(f'\nDemo data created successfully!')
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created {Teacher.objects.count()} teachers')
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created {Student.objects.count()} students')
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created {Class.objects.count()} classes')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Demo data creation failed: {str(e)}')
            )
