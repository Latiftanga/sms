from typing import Dict, List, Optional, Union, Any
from django.db.models import QuerySet
from django.core.exceptions import ValidationError
from student.models import Programme


class ProgrammeService:
    @staticmethod
    def get_all_programmes(school) -> QuerySet:
        """Get all programmes for a specific school"""
        return Programme.objects.filter(school=school)

    @staticmethod
    def get_active_programmes(school) -> QuerySet:
        """Get only active programmes for a specific school"""
        return Programme.objects.filter(school=school, is_active=True)

    @staticmethod
    def get_programme_by_id(school, programme_id: int) -> Optional[Programme]:
        """Get programme by ID within a specific school"""
        try:
            return Programme.objects.get(id=programme_id, school=school)
        except Programme.DoesNotExist:
            return None

    @staticmethod
    def create_programme(
        school, data: Dict[str, Any]
        ) -> Union[Programme, Dict[str, List[str]]]:
        """Create a new programme for the specified school"""
        try:
            # Create a copy of data to avoid modifying the original
            data = data.copy()

            # Set the school explicitly
            data['school'] = school

            # Create the programme instance
            programme = Programme(**data)
            programme.save()
            return programme
        except ValidationError as e:
            # Return validation errors
            return e.message_dict
        except Exception as e:
            # Return generic error
            return {'non_field_errors': [str(e)]}

    @staticmethod
    def update_programme(
        school, programme_id: int, data: Dict[str, Any]
        ) -> Union[Optional[Programme], Dict[str, List[str]]]:
        """Update an existing programme within a specific school"""
        try:
            # Fetch programme from the specified school
            programme = Programme.objects.get(id=programme_id, school=school)

            # Update the programme fields
            for key, value in data.items():
                setattr(programme, key, value)

            # Save the programme
            programme.save()
            return programme
        except Programme.DoesNotExist:
            return None
        except ValidationError as e:
            # Return validation errors
            return e.message_dict
        except Exception as e:
            # Return generic error
            return {'non_field_errors': [str(e)]}

    @staticmethod
    def delete_programme(school, programme_id: int) -> bool:
        """Delete a programme within a specific school"""
        try:
            # Only delete programme from the specified school
            programme = Programme.objects.get(id=programme_id, school=school)
            programme.delete()
            return True
        except Programme.DoesNotExist:
            return False

    @staticmethod
    def toggle_programme_status(school, programme_id: int) -> Optional[Programme]:
        """Toggle programme active status within a specific school"""
        try:
            # Only toggle status for programme from the specified school
            programme = Programme.objects.get(id=programme_id, school=school)
            programme.is_active = not programme.is_active
            programme.save()
            return programme
        except Programme.DoesNotExist:
            return None
