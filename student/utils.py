# File: student/utils.py
import csv
import io
from datetime import datetime
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from school.models import Student, Class, House, Programme
from account.models import create_student_with_user


def process_bulk_student_upload(csv_file, default_class=None, default_house=None):
    """
    Process bulk student upload from CSV file

    Args:
        csv_file: Uploaded CSV file
        default_class: Default class for students without class specified
        default_house: Default house for students without house specified

    Returns:
        dict: Results with success_count, error_count, and errors list
    """
    results = {
        'success_count': 0,
        'error_count': 0,
        'errors': [],
        'created_students': []
    }

    try:
        # Read and decode CSV file
        csv_file.seek(0)
        content = csv_file.read().decode('utf-8')
        reader = csv.DictReader(io.StringIO(content))

        # Cache classes and houses for efficiency
        classes_cache = {cls.name: cls for cls in Class.objects.all()}
        houses_cache = {house.name: house for house in House.objects.all()}
        programmes_cache = {
            prog.name: prog for prog in Programme.objects.all()}

        row_number = 1

        for row in reader:
            row_number += 1

            try:
                with transaction.atomic():
                    # Extract and validate required fields
                    first_name = row.get('first_name', '').strip()
                    last_name = row.get('last_name', '').strip()
                    gender = row.get('gender', '').strip().upper()
                    date_of_birth_str = row.get('date_of_birth', '').strip()
                    year_admitted_str = row.get('year_admitted', '').strip()

                    if not all([first_name, last_name, gender, date_of_birth_str, year_admitted_str]):
                        raise ValueError(
                            f"Row {row_number}: Missing required fields "
                            "(first_name, last_name, gender, date_of_birth, year_admitted)"
                        )

                    # Validate gender
                    if gender not in ['M', 'F']:
                        raise ValueError(
                            f"Row {row_number}: Gender must be 'M' or 'F'")

                    # Parse date of birth
                    try:
                        date_of_birth = datetime.strptime(
                            date_of_birth_str, '%Y-%m-%d').date()
                    except ValueError:
                        try:
                            date_of_birth = datetime.strptime(
                                date_of_birth_str, '%d/%m/%Y').date()
                        except ValueError:
                            raise ValueError(
                                f"Row {row_number}: Invalid date format. Use YYYY-MM-DD or DD/MM/YYYY"
                            )

                    # Validate date of birth
                    today = timezone.now().date()
                    if date_of_birth > today:
                        raise ValueError(
                            f"Row {row_number}: Date of birth cannot be in the future")

                    age = today.year - date_of_birth.year - (
                        (today.month, today.day) < (
                            date_of_birth.month, date_of_birth.day)
                    )
                    if age < 10 or age > 25:
                        raise ValueError(
                            f"Row {row_number}: Student age should be between 10 and 25 years"
                        )

                    # Parse year admitted
                    try:
                        year_admitted = int(year_admitted_str)
                    except ValueError:
                        raise ValueError(
                            f"Row {row_number}: Invalid year_admitted")

                    current_year = timezone.now().year
                    if year_admitted < 2000 or year_admitted > current_year + 1:
                        raise ValueError(
                            f"Row {row_number}: Year admitted must be between 2000 and {current_year + 1}"
                        )

                    # Get class
                    current_class = None
                    class_name = row.get('class_name', '').strip()
                    if class_name:
                        current_class = classes_cache.get(class_name)
                        if not current_class:
                            raise ValueError(
                                f"Row {row_number}: Class '{class_name}' not found")
                    elif default_class:
                        current_class = default_class

                    # Get house
                    house = None
                    house_name = row.get('house_name', '').strip()
                    if house_name:
                        house = houses_cache.get(house_name)
                        if not house:
                            raise ValueError(
                                f"Row {row_number}: House '{house_name}' not found")
                    elif default_house:
                        house = default_house

                    # Optional fields
                    middle_name = row.get('middle_name', '').strip() or None
                    email = row.get('email', '').strip() or None
                    phone = row.get('phone', '').strip() or None
                    address = row.get('address', '').strip() or None
                    ghana_card_number = row.get(
                        'ghana_card_number', '').strip() or None

                    # Guardian information
                    guardian_name = row.get(
                        'guardian_name', '').strip() or None
                    guardian_phone = row.get(
                        'guardian_phone', '').strip() or None
                    guardian_email = row.get(
                        'guardian_email', '').strip() or None
                    relationship_to_guardian = row.get(
                        'relationship_to_guardian', '').strip() or None

                    # Check for existing student with same email or Ghana Card
                    if email and Student.objects.filter(email=email).exists():
                        raise ValueError(
                            f"Row {row_number}: Student with email '{email}' already exists")

                    if ghana_card_number and Student.objects.filter(ghana_card_number=ghana_card_number).exists():
                        raise ValueError(
                            f"Row {row_number}: Student with Ghana Card '{ghana_card_number}' already exists"
                        )

                    # Create student using the helper function
                    student_data = {
                        'middle_name': middle_name,
                        'gender': gender,
                        'date_of_birth': date_of_birth,
                        'phone': phone,
                        'address': address,
                        'ghana_card_number': ghana_card_number,
                        'current_class': current_class,
                        'house': house,
                        'guardian_name': guardian_name,
                        'guardian_phone': guardian_phone,
                        'guardian_email': guardian_email,
                        'relationship_to_guardian': relationship_to_guardian
                    }

                    result = create_student_with_user(
                        first_name=first_name,
                        last_name=last_name,
                        year_admitted=year_admitted,
                        email=email,
                        **student_data
                    )

                    results['created_students'].append({
                        'student': result['student'],
                        'username': result['username'],
                        'password': result['password']
                    })
                    results['success_count'] += 1

            except Exception as e:
                results['error_count'] += 1
                results['errors'].append(str(e))
                continue

    except Exception as e:
        results['errors'].append(f"Error reading CSV file: {str(e)}")
        results['error_count'] += 1

    return results


def promote_students(students_queryset, to_class):
    """
    Promote selected students to a new class

    Args:
        students_queryset: QuerySet of students to promote
        to_class: Class object to promote students to

    Returns:
        dict: Results with success_count and errors
    """
    results = {
        'success_count': 0,
        'errors': []
    }

    for student in students_queryset:
        try:
            with transaction.atomic():
                # Check if the target class has capacity
                if to_class.is_full():
                    results['errors'].append(
                        f"{student.get_full_name()}: Target class {to_class} is at capacity"
                    )
                    continue

                # Update student's class
                old_class = student.current_class
                student.current_class = to_class
                student.save()

                results['success_count'] += 1

        except Exception as e:
            results['errors'].append(
                f"{student.get_full_name()}: Error during promotion - {str(e)}"
            )

    return results


def demote_students(students_queryset, to_class):
    """
    Demote selected students to a different class (typically lower level)

    Args:
        students_queryset: QuerySet of students to demote
        to_class: Class object to demote students to

    Returns:
        dict: Results with success_count and errors
    """
    results = {
        'success_count': 0,
        'errors': []
    }

    for student in students_queryset:
        try:
            with transaction.atomic():
                # Check if the target class has capacity
                if to_class.is_full():
                    results['errors'].append(
                        f"{student.get_full_name()}: Target class {to_class} is at capacity"
                    )
                    continue

                # Update student's class
                old_class = student.current_class
                student.current_class = to_class
                student.save()

                results['success_count'] += 1

        except Exception as e:
            results['errors'].append(
                f"{student.get_full_name()}: Error during demotion - {str(e)}"
            )

    return results


def generate_student_report(filters=None):
    """
    Generate comprehensive student report based on filters

    Args:
        filters: Dictionary of filters to apply

    Returns:
        dict: Report data
    """
    queryset = Student.objects.filter(is_active=True).select_related(
        'current_class', 'house', 'current_class__programme'
    )

    if filters:
        if filters.get('class_id'):
            queryset = queryset.filter(current_class_id=filters['class_id'])

        if filters.get('house_id'):
            queryset = queryset.filter(house_id=filters['house_id'])

        if filters.get('programme_id'):
            queryset = queryset.filter(
                current_class__programme_id=filters['programme_id'])

        if filters.get('year_admitted'):
            queryset = queryset.filter(year_admitted=filters['year_admitted'])

        if filters.get('gender'):
            queryset = queryset.filter(gender=filters['gender'])

    # Generate statistics
    total_students = queryset.count()

    # Group by level
    students_by_level = {}
    for level in [1, 2, 3]:
        level_students = queryset.filter(current_class__level=level)
        students_by_level[f'Level {level}'] = {
            'count': level_students.count(),
            'male': level_students.filter(gender='M').count(),
            'female': level_students.filter(gender='F').count()
        }

    # Group by house
    students_by_house = {}
    for house in House.objects.all():
        house_students = queryset.filter(house=house)
        students_by_house[house.name] = {
            'count': house_students.count(),
            'male': house_students.filter(gender='M').count(),
            'female': house_students.filter(gender='F').count()
        }

    # Group by programme
    students_by_programme = {}
    for programme in Programme.objects.all():
        prog_students = queryset.filter(current_class__programme=programme)
        students_by_programme[programme.name] = {
            'count': prog_students.count(),
            'male': prog_students.filter(gender='M').count(),
            'female': prog_students.filter(gender='F').count()
        }

    return {
        'total_students': total_students,
        'male_students': queryset.filter(gender='M').count(),
        'female_students': queryset.filter(gender='F').count(),
        'students_by_level': students_by_level,
        'students_by_house': students_by_house,
        'students_by_programme': students_by_programme,
        'students': queryset.order_by('current_class__level', 'last_name', 'first_name')
    }


def validate_student_data(data):
    """
    Validate student data for bulk operations

    Args:
        data: Dictionary of student data

    Returns:
        dict: Validation results with is_valid and errors
    """
    errors = []

    # Required fields
    required_fields = ['first_name', 'last_name',
                       'gender', 'date_of_birth', 'year_admitted']
    for field in required_fields:
        if not data.get(field):
            errors.append(f"Missing required field: {field}")

    # Gender validation
    if data.get('gender') and data['gender'] not in ['M', 'F']:
        errors.append("Gender must be 'M' or 'F'")

    # Date validation
    if data.get('date_of_birth'):
        try:
            dob = datetime.strptime(
                str(data['date_of_birth']), '%Y-%m-%d').date()
            if dob > timezone.now().date():
                errors.append("Date of birth cannot be in the future")
        except (ValueError, TypeError):
            errors.append("Invalid date of birth format")

    # Year validation
    if data.get('year_admitted'):
        try:
            year = int(data['year_admitted'])
            current_year = timezone.now().year
            if year < 2000 or year > current_year + 1:
                errors.append(
                    f"Year admitted must be between 2000 and {current_year + 1}")
        except (ValueError, TypeError):
            errors.append("Invalid year admitted")

    # Email validation
    if data.get('email'):
        if Student.objects.filter(email=data['email']).exists():
            errors.append("Student with this email already exists")

    # Ghana Card validation
    if data.get('ghana_card_number'):
        if Student.objects.filter(ghana_card_number=data['ghana_card_number']).exists():
            errors.append("Student with this Ghana Card number already exists")

    return {
        'is_valid': len(errors) == 0,
        'errors': errors
    }


def export_students_to_csv(students_queryset):
    """
    Export students to CSV format

    Args:
        students_queryset: QuerySet of students to export

    Returns:
        str: CSV content
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Write headers
    headers = [
        'Student ID', 'First Name', 'Middle Name', 'Last Name', 'Gender',
        'Date of Birth', 'Email', 'Phone', 'Address', 'Ghana Card Number',
        'Year Admitted', 'Current Class', 'House', 'Guardian Name',
        'Guardian Phone', 'Guardian Email', 'Relationship to Guardian',
        'Created At', 'Updated At'
    ]
    writer.writerow(headers)

    # Write student data
    for student in students_queryset:
        row = [
            student.student_id,
            student.first_name,
            student.middle_name or '',
            student.last_name,
            student.get_gender_display(),
            student.date_of_birth.strftime(
                '%Y-%m-%d') if student.date_of_birth else '',
            student.email or '',
            student.phone or '',
            student.address or '',
            student.ghana_card_number or '',
            student.year_admitted,
            str(student.current_class) if student.current_class else '',
            str(student.house) if student.house else '',
            student.guardian_name or '',
            student.guardian_phone or '',
            student.guardian_email or '',
            student.relationship_to_guardian or '',
            student.created_at.strftime(
                '%Y-%m-%d %H:%M:%S') if student.created_at else '',
            student.updated_at.strftime(
                '%Y-%m-%d %H:%M:%S') if student.updated_at else ''
        ]
        writer.writerow(row)

    return output.getvalue()
