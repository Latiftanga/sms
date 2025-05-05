from student.models import (
    StudentVoucher, Student,
    Guardian, StudentGuardian,
    Programme, Class
)
from django.contrib.auth import get_user_model
from rest_framework import serializers


User = get_user_model()


class ProgrammeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Programme
        fields = ['id', 'name', 'code', 'description', 'is_active']
        extra_kwargs = {
            'code': {'required': False},  # Make code optional
        }
        read_only_fields = ('id', )


class ProgrammeCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Programme
        fields = ['name', 'code', 'description', 'is_active']
        extra_kwargs = {
            'code': {'required': False},  # Make code optional
        }

    def validate(self, data):
        """Validate that the code is unique within the school"""
        # This validation will be run in addition to the model's clean method
        # but provides better error messages
        code = data.get('code')
        request = self.context.get('request')

        if code and request and hasattr(request.user, 'school'):
            school_id = request.user.school.id

            # Exclude current instance when validating on update
            instance_id = None
            if self.instance:
                instance_id = self.instance.id

            # Check if the code already exists in this school
            if Programme.objects.filter(
                school_id=school_id,
                code=code.upper()
            ).exclude(id=instance_id).exists():
                raise serializers.ValidationError({
                    'code': f"Programme with code '{code}' already exists in your school"
                })

        return data


class ClassCreateUpdateSerializer(serializers.ModelSerializer):
    programme_id = serializers.IntegerField(required=False, write_only=True)

    class Meta:
        model = Class
        fields = ['stage', 'level', 'programme_id', 'stream']

    def validate_programme_id(self, value):
        """Validate that the programme belongs to the user's school"""
        request = self.context.get('request')

        if request and hasattr(request.user, 'school'):
            school_id = request.user.school.id

            # Check if the programme exists in this school
            if not Programme.objects.filter(
                id=value,
                school_id=school_id
            ).exists():
                raise serializers.ValidationError(
                    "This programme does not exist in your school"
                )

        return value


class GuardianVoucherGenerationSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1, max_value=300)
    can_signin = serializers.BooleanField(default=True)


class GuardianSerializer(serializers.ModelSerializer):
    # Add relationship fields to each guardian
    relationship = serializers.ChoiceField(
        choices=StudentGuardian.RELATIONSHIP_CHOICES,
        default='guardian'
    )
    is_primary = serializers.BooleanField(default=False)
    can_pickup = serializers.BooleanField(default=True)
    emergency_contact = serializers.BooleanField(default=False)

    class Meta:
        model = Guardian
        fields = [
            'title', 'name', 'phone', 'email', 'address',
            'relationship', 'is_primary', 'can_pickup', 'emergency_contact'
        ]


class StudentRegistrationSerializer(serializers.ModelSerializer):
    voucher_serial = serializers.CharField(write_only=True)
    voucher_pin = serializers.CharField(write_only=True)

    # Add nested guardians serializer as a list
    guardians = GuardianSerializer(many=True, required=False)

    class Meta:
        model = Student
        fields = [
            'voucher_serial', 'voucher_pin', 'first_name', 'middle_name',
            'last_name', 'gender', 'date_of_birth', 'phone', 'email',
            'address', 'ghana_card_number' 'guardians'
        ]

    def validate(self, data):
        # Validate voucher
        serial_number = data.pop('voucher_serial')
        pin = data.pop('voucher_pin')

        try:
            voucher = StudentVoucher.objects.get(
                serial_number=serial_number, pin=pin)
            if voucher.is_used:
                raise serializers.ValidationError(
                    "Voucher has already been used")

            # Store the voucher for use in create method
            data['voucher'] = voucher

            # Make sure Email is provided if voucher allows sign-in
            if voucher.can_signin and 'email' not in data:
                raise serializers.ValidationError({
                    'Email': 'Email is required for registration with sign-in capability'
                })

            # Validate guardians - ensure only one is marked as primary
            guardians = data.get('guardians', [])
            primary_count = sum(
                1 for guardian in guardians if guardian.get('is_primary', False))

            if primary_count > 1:
                raise serializers.ValidationError({
                    'guardians': 'Only one guardian can be marked as primary'
                })

        except StudentVoucher.DoesNotExist:
            raise serializers.ValidationError(
                "Invalid student voucher credentials")

        return data

    def create(self, validated_data):
        voucher = validated_data.pop('voucher')
        email = validated_data.get('email')

        # Extract guardians data
        guardians_data = validated_data.pop('guardians', [])

        # Create student
        student = Student(
            school=voucher.school,
            grade_level=voucher.grade_level,
            **validated_data
        )
        student.save()  # Save to generate student_id

        # Create user if can_signin is True
        if voucher.can_signin and email:
            # Use create_studentuser method which takes student_id
            user, password = User.objects.create_studentuser(
                user_id=student.student_id
            )
            student.user = user
            student.save(update_fields=['user'])

        # Mark voucher as used by this specific student
        voucher.mark_as_used_by(student)

        # Process all guardians
        for guardian_data in guardians_data:
            # Extract relationship data
            relationship = guardian_data.pop('relationship', 'guardian')
            is_primary = guardian_data.pop('is_primary', False)
            can_pickup = guardian_data.pop('can_pickup', True)
            emergency_contact = guardian_data.pop('emergency_contact', False)

            # Check if guardian with this email or phone already exists
            guardian_email = guardian_data.get('email')
            guardian_phone = guardian_data.get('phone')

            guardian = None

            if guardian_email:
                try:
                    guardian = Guardian.objects.get(
                        email=guardian_email, school=voucher.school)
                except Guardian.DoesNotExist:
                    pass

            if not guardian and guardian_phone:
                try:
                    guardian = Guardian.objects.get(
                        phone=guardian_phone, school=voucher.school)
                except Guardian.DoesNotExist:
                    pass

            # If guardian doesn't exist, create one
            if not guardian:
                guardian = Guardian.objects.create(
                    school=voucher.school,
                    **guardian_data
                )

            # Create the relationship between student and guardian
            StudentGuardian.objects.create(
                student=student,
                guardian=guardian,
                relationship=relationship,
                is_primary=is_primary,
                can_pickup=can_pickup,
                emergency_contact=emergency_contact
            )

        # Return both the student and metadata for the view
        # Include metadata needed for email or other post-processing
        return student, {
            'created_user': voucher.can_signin and email is not None,
            'password': password,
            'school_name': voucher.school.name
        }


class AdminStudentListSerializer(serializers.ModelSerializer):
    """Serializer for listing students in admin panel"""
    grade_level_name = serializers.CharField(
        source='grade_level.display_name', read_only=True
    )

    class Meta:
        model = Student
        fields = [
            'id', 'student_id', 'first_name', 'middle_name', 'last_name',
            'grade_level', 'grade_level_name', 'status', 'year_admitted'
        ]
        read_only_fields = ['id', 'student_id']


class AdminStudentDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed student view/edit in admin panel"""
    grade_level_name = serializers.CharField(
        source='grade_level.display_name', read_only=True
    )
    programme_name = serializers.CharField(
        source='programme.name', read_only=True
    )

    class Meta:
        model = Student
        fields = [
            'id', 'student_id', 'first_name', 'middle_name', 'last_name',
            'gender', 'date_of_birth', 'email', 'phone', 'address',
            'grade_level', 'grade_level_name', 'year_admitted',
            'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'student_id', 'created_at', 'updated_at']

    def validate(self, data):
        """Validate student data including grade and programme compatibility"""
        grade_level = data.get(
            'grade_level') or self.instance.grade_level if self.instance else None
        programme = data.get(
            'programme') or self.instance.programme if self.instance else None

        if grade_level and programme:
            # Ensure programme is only specified for SHS classes
            if grade_level.stage != grade_level.EducationalStage.SHS and programme:
                raise serializers.ValidationError({
                    'programme': 'Programme should only be specified for Senior High School students'
                })

            # Ensure programme is specified for SHS classes
            if grade_level.stage == grade_level.EducationalStage.SHS and not programme:
                raise serializers.ValidationError({
                    'programme': 'Programme is required for Senior High School students'
                })

        return data
