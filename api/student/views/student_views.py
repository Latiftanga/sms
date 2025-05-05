# views.py
from core.permissions import IsSchoolAdmin
from api.student.services.student_service import AdminStudentService
from api.student.serializers.student_serializers import AdminStudentListSerializer, AdminStudentDetailSerializer
from student.models import Student
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, status, filters
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from ..serializers.student_serializers import StudentRegistrationSerializer
from ..services.student_service import StudentRegistrationService


class SchoolScopedViewSetMixin:
    """Mixin to get the school_id from the request"""

    def get_school_id(self):
        """
        Get the school ID from the request.
        This implementation assumes a school field on the user model.
        """
        if not hasattr(self.request.user, 'school'):
            raise ValueError("User does not have an associated school")

        if not self.request.user.school:
            raise ValueError("User's school is not set")

        return self.request.user.school.id


class StudentRegistrationAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = StudentRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            # Get validated data including the voucher
            validated_data = serializer.validated_data
            voucher = validated_data.pop('voucher')

            # Use the service layer to handle registration logic
            try:
                student = StudentRegistrationService.register_student(
                    data=validated_data,
                    voucher=voucher
                )

                return Response({
                    'message': 'Student registered successfully',
                    'student_id': student.student_id,
                    'login_enabled': voucher.can_signin and 'email' in validated_data
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response({
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminStudentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for administrators to manage students
    """
    permission_classes = [permissions.IsAuthenticated, IsSchoolAdmin]
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['current_status', 'gender',
                        'grade_level', 'programme', 'year_admitted']
    search_fields = ['student_id', 'first_name', 'last_name', 'email', 'phone']
    ordering_fields = ['student_id', 'first_name', 'last_name',
                       'grade_level', 'year_admitted', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return AdminStudentListSerializer
        return AdminStudentDetailSerializer

    def get_queryset(self):
        """Return students belonging to the admin's school"""
        return Student.objects.filter(school=self.request.user.school)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Use the service to create the student
        student = AdminStudentService.create_student(
            data=serializer.validated_data,
            school=request.user.school
        )

        # Return the newly created student
        return Response(
            self.get_serializer(student).data,
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # Use the service to update the student
        student = AdminStudentService.update_student(
            student=instance,
            data=serializer.validated_data
        )

        # Return the updated student
        return Response(self.get_serializer(student).data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # Use the service to "delete" (mark as inactive) the student
        AdminStudentService.delete_student(instance)

        return Response(
            {"detail": "Student record has been marked as withdrawn"},
            status=status.HTTP_200_OK
        )
