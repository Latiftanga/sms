from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from core.models import School
from django.contrib.auth import get_user_model
from student.models import (
    StudentVoucher, Class
)


class SchoolUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating specific school fields by admin users"""

    class Meta:
        model = School
        fields = [
            # Basic information
            'name', 'motto',

            # Contact information
            'headmaster_name', 'email', 'phone_primary', 'phone_secondary', 'website',

            # Location information
            'digital_address', 'physical_address',

            # Additional information
            'has_boarding', 'logo'
        ]
        # Generated from name but shouldn't be directly editable
        read_only_fields = ['slug']


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'user_id'


class LogoUploadSerializer(serializers.Serializer):
    logo = serializers.ImageField(required=True)


User = get_user_model()

class VoucherValidationSerializer(serializers.Serializer):
    serial_number = serializers.CharField(max_length=15)
    pin = serializers.CharField(max_length=12)

# Student Voucher Serializers
class StudentVoucherSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentVoucher
        fields = ['id', 'serial_number', 'pin', 'school', 'grade_level', 
                  'programme', 'is_used', 'created_at']
        read_only_fields = ['serial_number', 'pin', 'is_used', 'created_at']


class StudentVoucherGenerationSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1, max_value=500)
    school = serializers.PrimaryKeyRelatedField(queryset=School.objects.all())
    grade_level = serializers.PrimaryKeyRelatedField(queryset=Class.objects.all())
    can_signin = serializers.BooleanField(default=True)


class TeacherVoucherGenerationSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1, max_value=100)
    school = serializers.PrimaryKeyRelatedField(queryset=School.objects.all())
    department = serializers.CharField(max_length=128, required=False, allow_blank=True)
    position = serializers.CharField(max_length=128, required=False, allow_blank=True)
    can_signin = serializers.BooleanField(default=True)

