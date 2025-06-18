# File: student/tests.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from datetime import date
import io
import csv

from school.models import Student, Class, House, Programme, School
from account.models import User
from .forms import StudentForm, BulkUploadForm
from .utils import process_bulk_student_upload, promote_students

User = get_user_model()


class StudentModelTest(TestCase):
    """Test cases for Student model"""

    def setUp(self):
        """Set up test data"""
        # Create school
        self.school = School.objects.create(
            name='Test School',
            code='TEST',
            phone='0244123456',
            email='test@school.com'
        )

        # Create programme and house
        self.programme = Programme.objects.create(name='Science', code='SCI')
        self.house = House.objects.create(name='Blue House')

        # Create class
        self.test_class = Class.objects.create(
            name='A',
            programme=self.programme,
            level=1
        )

    def test_student_creation(self):
        """Test student creation with auto-generated ID"""
        student = Student.objects.create(
            first_name='John',
            last_name='Doe',
            gender='M',
            date_of_birth=date(2008, 5, 15),
            year_admitted=2024,
            current_class=self.test_class,
            house=self.house,
            guardian_name='Jane Doe',
            guardian_phone='0244987654'
        )

        self.assertTrue(student.student_id.startswith('STUTEST'))
        self.assertEqual(student.get_full_name(), 'John Doe')
        self.assertTrue(student.is_active)

    def test_student_id_generation(self):
        """Test unique student ID generation"""
        student1 = Student.objects.create(
            first_name='John',
            last_name='Doe',
            gender='M',
            date_of_birth=date(2008, 5, 15),
            year_admitted=2024,
            guardian_name='Jane Doe',
            guardian_phone='0244987654'
        )

        student2 = Student.objects.create(
            first_name='Jane',
            last_name='Smith',
            gender='F',
            date_of_birth=date(2008, 8, 20),
            year_admitted=2024,
            guardian_name='John Smith',
            guardian_phone='0244123456'
        )

        self.assertNotEqual(student1.student_id, student2.student_id)
        self.assertTrue(student1.student_id.endswith('24'))
        self.assertTrue(student2.student_id.endswith('24'))

    def test_student_str_representation(self):
        """Test student string representation"""
        student = Student.objects.create(
            first_name='John',
            last_name='Doe',
            gender='M',
            date_of_birth=date(2008, 5, 15),
            year_admitted=2024,
            guardian_name='Jane Doe',
            guardian_phone='0244987654'
        )

        expected = f"John Doe ({student.student_id})"
        self.assertEqual(str(student), expected)


class StudentFormTest(TestCase):
    """Test cases for StudentForm"""

    def setUp(self):
        """Set up test data"""
        self.programme = Programme.objects.create(name='Science', code='SCI')
        self.house = House.objects.create(name='Blue House')
        self.test_class = Class.objects.create(
            name='A',
            programme=self.programme,
            level=1
        )

    def test_valid_form(self):
        """Test form with valid data"""
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'gender': 'M',
            'date_of_birth': '2008-05-15',
            'year_admitted': 2024,
            'current_class': self.test_class.id,
            'house': self.house.id,
            'guardian_name': 'Jane Doe',
            'guardian_phone': '0244987654'
        }

        form = StudentForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_date_of_birth(self):
        """Test form with future date of birth"""
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'gender': 'M',
            'date_of_birth': '2030-05-15',  # Future date
            'year_admitted': 2024,
            'guardian_name': 'Jane Doe',
            'guardian_phone': '0244987654'
        }

        form = StudentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('date_of_birth', form.errors)

    def test_invalid_year_admitted(self):
        """Test form with invalid year admitted"""
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'gender': 'M',
            'date_of_birth': '2008-05-15',
            'year_admitted': 1999,  # Too old
            'guardian_name': 'Jane Doe',
            'guardian_phone': '0244987654'
        }

        form = StudentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('year_admitted', form.errors)


class StudentViewTest(TestCase):
    """Test cases for Student views"""

    def setUp(self):
        """Set up test data"""
        # Create user and login
        self.user = User.objects.create_user(
            username='admin',
            password='testpass123',
            is_admin=True
        )
        self.client = Client()
        self.client.login(username='admin', password='testpass123')

        # Create test data
        self.programme = Programme.objects.create(name='Science', code='SCI')
        self.house = House.objects.create(name='Blue House')
        self.test_class = Class.objects.create(
            name='A',
            programme=self.programme,
            level=1
        )

        # Create test student
        self.student = Student.objects.create(
            first_name='John',
            last_name='Doe',
            gender='M',
            date_of_birth=date(2008, 5, 15),
            year_admitted=2024,
            current_class=self.test_class,
            house=self.house,
            guardian_name='Jane Doe',
            guardian_phone='0244987654'
        )

    def test_student_list_view(self):
        """Test student list view"""
        response = self.client.get(reverse('student:student_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'John Doe')

    def test_student_detail_view(self):
        """Test student detail view"""
        response = self.client.get(
            reverse('student:student_detail', kwargs={'pk': self.student.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'John Doe')

    def test_student_create_view(self):
        """Test student create view"""
        response = self.client.get(reverse('student:student_create'))
        self.assertEqual(response.status_code, 200)

        # Test form submission
        form_data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'gender': 'F',
            'date_of_birth': '2008-08-20',
            'year_admitted': 2024,
            'current_class': self.test_class.id,
            'house': self.house.id,
            'guardian_name': 'John Smith',
            'guardian_phone': '0244123456'
        }

        response = self.client.post(
            reverse('student:student_create'), data=form_data)
        # Redirect after successful creation
        self.assertEqual(response.status_code, 302)

        # Check if student was created
        self.assertTrue(Student.objects.filter(
            first_name='Jane', last_name='Smith').exists())

    def test_student_update_view(self):
        """Test student update view"""
        response = self.client.get(
            reverse('student:student_edit', kwargs={'pk': self.student.pk})
        )
        self.assertEqual(response.status_code, 200)

        # Test form submission
        form_data = {
            'first_name': 'John Updated',
            'last_name': 'Doe',
            'gender': 'M',
            'date_of_birth': '2008-05-15',
            'year_admitted': 2024,
            'current_class': self.test_class.id,
            'house': self.house.id,
            'guardian_name': 'Jane Doe',
            'guardian_phone': '0244987654'
        }

        response = self.client.post(
            reverse('student:student_edit', kwargs={'pk': self.student.pk}),
            data=form_data
        )
        self.assertEqual(response.status_code, 302)

        # Check if student was updated
        self.student.refresh_from_db()
        self.assertEqual(self.student.first_name, 'John Updated')

    def test_student_delete_view(self):
        """Test student delete (deactivate) view"""
        response = self.client.post(
            reverse('student:student_delete', kwargs={'pk': self.student.pk})
        )
        self.assertEqual(response.status_code, 302)

        # Check if student was deactivated
        self.student.refresh_from_db()
        self.assertFalse(self.student.is_active)


class BulkUploadTest(TestCase):
    """Test cases for bulk upload functionality"""

    def setUp(self):
        """Set up test data"""
        self.programme = Programme.objects.create(name='Science', code='SCI')
        self.house = House.objects.create(name='Blue House')
        self.test_class = Class.objects.create(
            name='A',
            programme=self.programme,
            level=1
        )

    def test_bulk_upload_form_valid_csv(self):
        """Test bulk upload form with valid CSV"""
        csv_content = (
            "first_name,last_name,gender,date_of_birth,year_admitted\n"
            "John,Doe,M,2008-05-15,2024\n"
            "Jane,Smith,F,2008-08-20,2024\n"
        )

        csv_file = SimpleUploadedFile(
            "students.csv",
            csv_content.encode('utf-8'),
            content_type="text/csv"
        )

        form = BulkUploadForm(data={}, files={'csv_file': csv_file})
        self.assertTrue(form.is_valid())

    def test_bulk_upload_form_invalid_csv(self):
        """Test bulk upload form with invalid CSV"""
        csv_content = "invalid,csv,content\n"

        csv_file = SimpleUploadedFile(
            "students.csv",
            csv_content.encode('utf-8'),
            content_type="text/csv"
        )

        form = BulkUploadForm(data={}, files={'csv_file': csv_file})
        self.assertFalse(form.is_valid())

    def test_process_bulk_student_upload(self):
        """Test bulk student upload processing"""
        csv_content = (
            "first_name,last_name,gender,date_of_birth,year_admitted,guardian_name,guardian_phone\n"
            "John,Doe,M,2008-05-15,2024,Jane Doe,0244987654\n"
            "Jane,Smith,F,2008-08-20,2024,John Smith,0244123456\n"
        )

        csv_file = io.StringIO(csv_content)
        csv_file.name = 'students.csv'

        result = process_bulk_student_upload(csv_file)

        self.assertEqual(result['success_count'], 2)
        self.assertEqual(result['error_count'], 0)
        self.assertEqual(Student.objects.count(), 2)


class PromotionTest(TestCase):
    """Test cases for student promotion functionality"""

    def setUp(self):
        """Set up test data"""
        self.programme = Programme.objects.create(name='Science', code='SCI')
        self.house = House.objects.create(name='Blue House')

        # Create classes
        self.class_1a = Class.objects.create(
            name='A',
            programme=self.programme,
            level=1
        )
        self.class_2a = Class.objects.create(
            name='A',
            programme=self.programme,
            level=2
        )

        # Create students
        self.student1 = Student.objects.create(
            first_name='John',
            last_name='Doe',
            gender='M',
            date_of_birth=date(2008, 5, 15),
            year_admitted=2023,
            current_class=self.class_1a,
            house=self.house,
            guardian_name='Jane Doe',
            guardian_phone='0244987654'
        )

        self.student2 = Student.objects.create(
            first_name='Jane',
            last_name='Smith',
            gender='F',
            date_of_birth=date(2008, 8, 20),
            year_admitted=2023,
            current_class=self.class_1a,
            house=self.house,
            guardian_name='John Smith',
            guardian_phone='0244123456'
        )

    def test_promote_students(self):
        """Test student promotion functionality"""
        students = Student.objects.filter(current_class=self.class_1a)

        result = promote_students(students, self.class_2a)

        self.assertEqual(result['success_count'], 2)
        self.assertEqual(len(result['errors']), 0)

        # Check if students were promoted
        self.student1.refresh_from_db()
        self.student2.refresh_from_db()

        self.assertEqual(self.student1.current_class, self.class_2a)
        self.assertEqual(self.student2.current_class, self.class_2a)


class StudentUtilsTest(TestCase):
    """Test cases for student utility functions"""

    def setUp(self):
        """Set up test data"""
        self.programme = Programme.objects.create(name='Science', code='SCI')
        self.house = House.objects.create(name='Blue House')
        self.test_class = Class.objects.create(
            name='A',
            programme=self.programme,
            level=1
        )

    def test_export_students_to_csv(self):
        """Test student export to CSV"""
        # Create test students
        Student.objects.create(
            first_name='John',
            last_name='Doe',
            gender='M',
            date_of_birth=date(2008, 5, 15),
            year_admitted=2024,
            current_class=self.test_class,
            house=self.house,
            guardian_name='Jane Doe',
            guardian_phone='0244987654'
        )

        from .utils import export_students_to_csv

        students = Student.objects.all()
        csv_content = export_students_to_csv(students)

        self.assertIn('John', csv_content)
        self.assertIn('Doe', csv_content)
        self.assertIn('Student ID', csv_content)  # Check headers
