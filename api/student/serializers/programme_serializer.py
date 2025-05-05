# apps/school/api/serializers.py

from rest_framework import serializers
from student.models import Programme


class ProgrammeSerializer(serializers.ModelSerializer):
    """Serializer for reading programme details"""

    class Meta:
        model = Programme
        fields = ['id', 'name', 'code', 'description',
                  'is_active']
        read_only_fields = ['id', 'is_active']


class ProgrammeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating programmes"""

    class Meta:
        model = Programme
        fields = ['id', 'name', 'code', 'description', 'is_active']
        extra_kwargs = {
            # Make code optional for auto-generation
            'code': {'required': False},
        }

    def validate(self, data):
        """Additional validation for programme creation"""
        # If code is provided, check if it's unique
        # School filtering is now automatic through the middleware
        code = data.get('code')
        if code:
            code = code.upper()  # Convert to uppercase for comparison
            if Programme.objects.filter(code=code).exists():
                raise serializers.ValidationError({
                    'code': "Programme with this code already exists"
                })

        # If name is provided, check if it's unique
        name = data.get('name')
        if name and Programme.objects.filter(name=name).exists():
            raise serializers.ValidationError({
                'name': "Programme with this name already exists"
            })

        return data


class ProgrammeUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating programmes"""

    class Meta:
        model = Programme
        fields = ['name', 'code', 'description', 'is_active']
        extra_kwargs = {
            'name': {'required': False},
            'code': {'required': False},
        }

    def validate(self, data):
        """Additional validation for programme updates"""
        # If code is provided, check if it's unique
        # School filtering is now automatic through the middleware
        code = data.get('code')
        if code:
            code = code.upper()  # Convert to uppercase for comparison
            if Programme.objects.filter(
                code=code
            ).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError({
                    'code': "Programme with this code already exists"
                })

        # If name is provided, check if it's unique
        name = data.get('name')
        if name and Programme.objects.filter(
            name=name
        ).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError({
                'name': "Programme with this name already exists"
            })

        return data
