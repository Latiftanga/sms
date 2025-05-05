from rest_framework import serializers
from student.models import Class, Programme


class ProgrammeReferenceSerializer(serializers.ModelSerializer):
    """Simple serializer for programme references"""

    class Meta:
        model = Programme
        fields = ['id', 'name', 'code']


class ClassSerializer(serializers.ModelSerializer):
    """Serializer for reading class details"""
    programme = ProgrammeReferenceSerializer(read_only=True)
    stage_display = serializers.CharField(
        source='get_stage_display', read_only=True)
    display_name = serializers.CharField(read_only=True)
    current_enrollment = serializers.IntegerField(read_only=True)
    available_seats = serializers.IntegerField(read_only=True)
    capacity_percentage = serializers.FloatField(read_only=True)

    class Meta:
        model = Class
        exclude = ['school']
        read_only_fields = ['display_name', 'current_enrollment',
                            'available_seats', 'capacity_percentage']


class ClassCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating classes"""
    programme_id = serializers.IntegerField(required=False, write_only=True)

    class Meta:
        model = Class
        fields = ['stage', 'level', 'stream',
                  'programme_id', 'max_students', 'is_active']

    def validate_programme_id(self, value):
        """Validate that the programme exists and belongs to the user's school"""
        request = self.context.get('request')
        if not request or not hasattr(request.user, 'school'):
            raise serializers.ValidationError(
                "Cannot validate programme without school context")

        school = request.user.school

        if not Programme.objects.filter(id=value, school=school).exists():
            raise serializers.ValidationError(
                "Invalid programme or programme doesn't belong to this school"
            )
        return value


class ClassUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating classes"""
    programme_id = serializers.IntegerField(required=False, write_only=True)

    class Meta:
        model = Class
        fields = ['stage', 'level', 'stream',
                  'programme_id', 'max_students', 'is_active']
        extra_kwargs = {
            'stage': {'required': False},
            'level': {'required': False},
            'stream': {'required': False},
        }

    def validate_programme_id(self, value):
        """Validate that the programme exists and belongs to the user's school"""
        request = self.context.get('request')
        if not request or not hasattr(request.user, 'school'):
            raise serializers.ValidationError(
                "Cannot validate programme without school context")

        school = request.user.school

        if not Programme.objects.filter(id=value, school=school).exists():
            raise serializers.ValidationError(
                "Invalid programme or programme doesn't belong to this school"
            )
        return value
