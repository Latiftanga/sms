# services.py
from django.db import transaction
from django.contrib.auth import get_user_model
from student.models import (
    Student, Guardian, StudentGuardian, Class
)
from core.utils import send_credentials_email

User = get_user_model()


class StudentRegistrationService:
    @staticmethod
    @transaction.atomic
    def student_register_with_voucher(data, voucher):
        """
        Service method to handle student registration business logic
        """
        email = data.get('email')
        guardians_data = data.get('guardians', [])

        # Create student
        student = Student(
            school=voucher.school,
            grade_level=voucher.grade_level,
            first_name=data.get('first_name'),
            middle_name=data.get('middle_name'),
            last_name=data.get('last_name'),
            gender=data.get('gender'),
            date_of_birth=data.get('date_of_birth'),
            email=email,
            phone=data.get('phone'),
            address=data.get('address')
        )
        student.save()  # Save to generate student_id

        # Create user if voucher allows signin
        user = None
        password = None
        if voucher.can_signin and email:
            user, password = User.objects.create_studentuser(
                user_id=student.student_id
            )
            student.user = user
            student.save(update_fields=['user'])

        # Mark voucher as used
        voucher.mark_as_used_by(student)

        # Process all guardians
        for guardian_data in guardians_data:
            # Extract relationship data
            relationship = guardian_data.get('relationship', 'guardian')
            is_primary = guardian_data.get('is_primary', False)
            can_pickup = guardian_data.get('can_pickup', True)
            emergency_contact = guardian_data.get('emergency_contact', False)

            # Check if guardian exists
            guardian = StudentRegistrationService._find_or_create_guardian(
                voucher.school, guardian_data
            )

            # Create relationship
            StudentGuardian.objects.create(
                student=student,
                guardian=guardian,
                relationship=relationship,
                is_primary=is_primary,
                can_pickup=can_pickup,
                emergency_contact=emergency_contact
            )

        # Send email notification if user was created
        if user:
            student_name = f"{student.get_full_name()}"
            send_credentials_email(
                email=email,
                username=student.student_id,
                password=password,
                student_name=student_name,
                student_id=student.student_id,
                school_name=voucher.school.name
            )

        return student

    @staticmethod
    def _find_or_create_guardian(school, guardian_data):
        """Find existing guardian or create a new one"""
        guardian = None
        guardian_email = guardian_data.get('email')
        guardian_phone = guardian_data.get('phone')

        if guardian_email:
            try:
                guardian = Guardian.objects.get(
                    email=guardian_email, school=school)
            except Guardian.DoesNotExist:
                pass

        if not guardian and guardian_phone:
            try:
                guardian = Guardian.objects.get(
                    phone=guardian_phone, school=school)
            except Guardian.DoesNotExist:
                pass

        if not guardian:
            guardian = Guardian.objects.create(
                school=school,
                title=guardian_data.get('title'),
                name=guardian_data.get('name'),
                phone=guardian_data.get('phone'),
                email=guardian_data.get('email'),
                address=guardian_data.get('address')
            )

        return guardian


class AdminStudentService:
    @staticmethod
    @transaction.atomic
    def create_student(data, school):
        """
        Create a new student record (admin operation)

        Args:
            data: Validated student data
            school: School the admin belongs to

        Returns:
            Student: The created student instance
        """
        # Extract grade level and programme
        grade_level = data.get('grade_level')

        # Create the student record
        student = Student(
            school=school,
            current_class=grade_level,
            first_name=data.get('first_name'),
            middle_name=data.get('middle_name'),
            last_name=data.get('last_name'),
            gender=data.get('gender'),
            date_of_birth=data.get('date_of_birth'),
            phone=data.get('phone'),
            email=data.get('email'),
            address=data.get('address'),
            digital_address=data.get('digital_address'),
            ghana_card_number=data.get('ghana_card_number'),
            year_admitted=data.get('year_admitted'),
            status=data.get('status', 'active')
        )
        student.save()  # This will generate the student_id through the save method

        # If email is provided, we can optionally create a user account
        if data.get('can_signin', False) and data.get('email') and data.get('password'):
            password = None

            user, password = User.objects.create_studentuser(
                user_id=student.student_id
            )
            student.user = user
            student.save(update_fields=['user'])

        return student, password

    @staticmethod
    @transaction.atomic
    def update_student(student, data):
        """
        Update a student record (admin operation)

        Args:
            student: Existing student instance to update
            data: Validated student data

        Returns:
            Student: The updated student instance
        """
        # Update basic student fields
        for field, value in data.items():
            if field != 'user' and hasattr(student, field):
                setattr(student, field, value)

        student.save()
        return student

    @staticmethod
    def withdraw_student(student):
        """
        Withdraw a student record (admin operation)

        This doesn't actually delete the record but marks it as inactive

        Args:
            student: Student instance to mark as inactive
        """
        student.status = 'withdrawn'
        student.save(update_fields=['status'])

        # If the student has a user account, disable it
        if student.user:
            student.user.is_active = False
            student.user.save(update_fields=['is_active'])