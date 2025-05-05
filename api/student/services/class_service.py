from typing import Dict, List, Optional, Union, Any
from django.db.models import QuerySet, Count, F, Q
from django.core.exceptions import ValidationError
from student.models import Class, Programme


class ClassService:
    @staticmethod
    def get_all_classes(school) -> QuerySet:
        """Get all classes for a specific school"""
        return Class.objects.filter(school=school)

    @staticmethod
    def get_active_classes(school) -> QuerySet:
        """Get only active classes for a specific school"""
        return Class.objects.filter(school=school, is_active=True)

    @staticmethod
    def get_classes_by_stage(school, stage: str) -> QuerySet:
        """Get classes by educational stage for a specific school"""
        return Class.objects.filter(school=school, stage=stage)

    @staticmethod
    def get_classes_with_enrollment(school) -> QuerySet:
        """Get classes with enrollment counts for a specific school"""
        return Class.objects.filter(school=school).annotate(
            enrollment_count=Count('students')
        ).select_related('programme')

    @staticmethod
    def get_available_classes(school) -> QuerySet:
        """Get classes that are not full"""
        return Class.objects.filter(school=school).annotate(
            enrollment_count=Count('students')
        ).filter(
            enrollment_count__lt=F('max_students'),
            is_active=True
        )

    @staticmethod
    def get_class_by_id(school, class_id: int) -> Optional[Class]:
        """Get class by ID within a specific school"""
        try:
            return Class.objects.get(id=class_id, school=school)
        except Class.DoesNotExist:
            return None

    @staticmethod
    def create_class(school, data: Dict[str, Any]) -> Union[Class, Dict[str, List[str]]]:
        """Create a new class for a specific school"""
        try:
            # Create a copy of data to avoid modifying the original
            data = data.copy()

            # Set the school explicitly
            data['school'] = school

            # Handle programme FK if present in data
            programme_id = data.pop('programme_id', None)
            if programme_id:
                try:
                    # Ensure programme belongs to the same school
                    programme = Programme.objects.get(
                        id=programme_id, school=school)
                    data['programme'] = programme
                except Programme.DoesNotExist:
                    raise ValidationError({
                        'programme_id': _("Invalid programme or programme doesn't belong to this school")
                    })

            # Create the class instance
            class_obj = Class(**data)
            class_obj.save()
            return class_obj
        except ValidationError as e:
            # Return validation errors
            return e.message_dict
        except Exception as e:
            # Return generic error
            return {'non_field_errors': [str(e)]}

    @staticmethod
    def update_class(
        school, class_id: int, data: Dict[str, Any]
        ) -> Union[Optional[Class], Dict[str, List[str]]]:
        """Update an existing class within a specific school"""
        try:
            # Fetch class from the specified school
            class_obj = Class.objects.get(id=class_id, school=school)

            # Create a copy of data to avoid modifying the original
            data = data.copy()

            # Handle programme FK if present in data
            programme_id = data.pop('programme_id', None)
            if programme_id:
                try:
                    # Ensure programme belongs to the same school
                    programme = Programme.objects.get(
                        id=programme_id, school=school)
                    data['programme'] = programme
                except Programme.DoesNotExist:
                    raise ValidationError({
                        'programme_id': _("Invalid programme or programme doesn't belong to this school")
                    })

            # Update the class fields
            for key, value in data.items():
                setattr(class_obj, key, value)

            # Save the class
            class_obj.save()
            return class_obj
        except Class.DoesNotExist:
            return None
        except ValidationError as e:
            # Return validation errors
            return e.message_dict
        except Exception as e:
            # Return generic error
            return {'non_field_errors': [str(e)]}

    @staticmethod
    def delete_class(school, class_id: int) -> bool:
        """Delete a class within a specific school"""
        try:
            # Only delete class from the specified school
            class_obj = Class.objects.get(id=class_id, school=school)
            class_obj.delete()
            return True
        except Class.DoesNotExist:
            return False

    @staticmethod
    def toggle_class_status(school, class_id: int) -> Optional[Class]:
        """Toggle class active status within a specific school"""
        try:
            # Only toggle status for class from the specified school
            class_obj = Class.objects.get(id=class_id, school=school)
            class_obj.is_active = not class_obj.is_active
            class_obj.save(update_fields=['is_active'])  # Optimized save
            return class_obj
        except Class.DoesNotExist:
            return None

    @staticmethod
    def get_classes_by_programme(school, programme_id: int) -> QuerySet:
        """Get all classes for a specific programme within a specific school"""
        return Class.objects.filter(
            school=school,
            programme_id=programme_id
        )

    @staticmethod
    def get_classes_with_available_seats(school, min_seats: int = 1) -> QuerySet:
        """Get classes with at least the specified number of available seats"""
        return Class.objects.filter(school=school, is_active=True).annotate(
            enrollment_count=Count('students')
        ).filter(
            max_students__gte=F('enrollment_count') + min_seats
        )
