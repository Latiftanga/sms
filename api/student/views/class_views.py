from django.db.models import Count, F
from django.utils.translation import gettext_lazy as _  # Add this import
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from student.models import Class
from student.services.class_service import ClassService
from student.serializers.class_serializers import (
    ClassSerializer,
    ClassCreateSerializer,
    ClassUpdateSerializer
)
from core.permissions import IsSchoolAdmin


class ClassViewSet(viewsets.ViewSet):
    """ViewSet for Class operations, accessible only to school admins"""
    permission_classes = [IsAuthenticated, IsSchoolAdmin]

    def get_school(self):
        """Get the current user's school"""
        if not hasattr(self.request.user, 'school'):
            raise ValueError("User does not have an associated school")

        if not self.request.user.school:
            raise ValueError("User's school is not set")

        return self.request.user.school

    @swagger_auto_schema(
        operation_description="List all classes",
        operation_summary="List classes",
        manual_parameters=[
            openapi.Parameter(
                'active_only',
                openapi.IN_QUERY,
                description="Filter to show only active classes",
                type=openapi.TYPE_BOOLEAN,
                required=False
            ),
            openapi.Parameter(
                'stage',
                openapi.IN_QUERY,
                description="Filter by educational stage (KG, PR, JHS, SHS)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'programme_id',
                openapi.IN_QUERY,
                description="Filter by programme ID (for SHS only)",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                'available_seats',
                openapi.IN_QUERY,
                description="Filter classes with at least this many available seats",
                type=openapi.TYPE_INTEGER,
                required=False
            )
        ],
        responses={200: ClassSerializer(many=True)}
    )
    def list(self, request):
        """List all classes with optional filtering"""
        try:
            school = self.get_school()

            # Start with all classes for this school
            queryset = ClassService.get_all_classes(school)

            # Apply filters based on query parameters
            active_only = request.query_params.get(
                'active_only', 'false').lower() == 'true'
            if active_only:
                queryset = queryset.filter(is_active=True)

            stage = request.query_params.get('stage')
            if stage:
                queryset = queryset.filter(stage=stage)

            programme_id = request.query_params.get('programme_id')
            if programme_id:
                queryset = queryset.filter(programme_id=programme_id)

            available_seats = request.query_params.get('available_seats')
            if available_seats and available_seats.isdigit():
                # Get classes with enrollment counts
                queryset = queryset.annotate(
                    enrollment_count=Count('students')
                ).filter(
                    max_students__gte=F('enrollment_count') +
                    int(available_seats)
                )

            # Optimize query with select_related
            queryset = queryset.select_related('programme')

            serializer = ClassSerializer(queryset, many=True)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Get a single class by ID",
        operation_summary="Retrieve a class",
        responses={
            200: ClassSerializer,
            404: "Class not found"
        }
    )
    def retrieve(self, request, pk=None):
        """Get a single class"""
        try:
            school = self.get_school()
            class_obj = ClassService.get_class_by_id(school, pk)
            if not class_obj:
                return Response(
                    {"detail": "Class not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Get enrollment count for the class
            class_obj._enrollment_count = class_obj.students.count()

            serializer = ClassSerializer(class_obj)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Create a new class",
        operation_summary="Create a class",
        request_body=ClassCreateSerializer,
        responses={
            201: ClassSerializer,
            400: "Bad request, validation error"
        }
    )
    def create(self, request):
        """Create a new class"""
        serializer = ClassCreateSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            try:
                school = self.get_school()
                result = ClassService.create_class(
                    school, serializer.validated_data)

                # Check if result is a Class instance or an error dict
                if isinstance(result, Class):
                    return Response(
                        ClassSerializer(result).data,
                        status=status.HTTP_201_CREATED
                    )
                else:
                    # Result is an error dict
                    return Response(
                        result,
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except ValueError as e:
                return Response(
                    {"detail": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Update an existing class",
        operation_summary="Update a class",
        request_body=ClassUpdateSerializer,
        responses={
            200: ClassSerializer,
            404: "Class not found",
            400: "Bad request, validation error"
        }
    )
    def update(self, request, pk=None):
        """Update an existing class"""
        try:
            school = self.get_school()
            class_obj = ClassService.get_class_by_id(school, pk)

            if not class_obj:
                return Response(
                    {"detail": "Class not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            serializer = ClassUpdateSerializer(
                class_obj,
                data=request.data,
                partial=True,
                context={'request': request}
            )

            if serializer.is_valid():
                result = ClassService.update_class(
                    school, pk, serializer.validated_data
                )

                # Check if result is a Class instance or an error dict
                if isinstance(result, Class):
                    return Response(ClassSerializer(result).data)
                elif result is None:
                    return Response(
                        {"detail": "Class not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )
                else:
                    # Result is an error dict
                    return Response(result, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        """Alias for update with partial=True"""
        return self.update(request, pk)

    @swagger_auto_schema(
        operation_description="Delete an existing class",
        operation_summary="Delete a class",
        responses={
            204: "No content, class deleted successfully",
            404: "Class not found"
        }
    )
    def destroy(self, request, pk=None):
        """Delete a class"""
        try:
            school = self.get_school()
            success = ClassService.delete_class(school, pk)
            if not success:
                return Response(
                    {"detail": "Class not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        operation_description="Toggle the active status of a class",
        operation_summary="Toggle class active status",
        responses={
            200: ClassSerializer,
            404: "Class not found"
        }
    )
    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        """Toggle active status of a class"""
        try:
            school = self.get_school()
            class_obj = ClassService.toggle_class_status(school, pk)
            if not class_obj:
                return Response(
                    {"detail": "Class not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response(ClassSerializer(class_obj).data)
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        operation_description="Get classes for a specific educational stage",
        operation_summary="Get classes by stage",
        manual_parameters=[
            openapi.Parameter(
                'stage',
                openapi.IN_PATH,
                description="Educational stage (KG, PR, JHS, SHS)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={200: ClassSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='stage/(?P<stage>[^/.]+)')
    def by_stage(self, request, stage=None):
        """Get classes by educational stage"""
        try:
            school = self.get_school()

            # Validate stage
            valid_stages = [choice[0]
                            for choice in Class.EducationalStage.choices]
            if stage not in valid_stages:
                return Response(
                    {"detail": f"Invalid stage. Must be one of {', '.join(valid_stages)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            classes = ClassService.get_classes_by_stage(school, stage)
            serializer = ClassSerializer(classes, many=True)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
