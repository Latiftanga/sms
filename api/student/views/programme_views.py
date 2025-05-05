# apps/school/api/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from student.models import Programme
from student.services.programme_service import ProgrammeService
from student.serializers.programme_serializer import (
    ProgrammeSerializer,
    ProgrammeCreateSerializer,
    ProgrammeUpdateSerializer
)
from core.permissions import IsSchoolAdmin


class ProgrammeViewSet(viewsets.ViewSet):
    """ViewSet for Programme operations, accessible only to school admins"""
    permission_classes = [IsAuthenticated, IsSchoolAdmin]

    def get_school(self):
        """Get the current user's school"""
        if not hasattr(self.request.user, 'school'):
            raise ValueError("User does not have an associated school")

        if not self.request.user.school:
            raise ValueError("User's school is not set")

        return self.request.user.school

    @swagger_auto_schema(
        operation_description="List all programmes",
        operation_summary="List programmes",
        manual_parameters=[
            openapi.Parameter(
                'active_only',
                openapi.IN_QUERY,
                description="Filter to show only active programmes",
                type=openapi.TYPE_BOOLEAN,
                required=False
            )
        ],
        responses={200: ProgrammeSerializer(many=True)}
    )
    def list(self, request):
        """List all programmes"""
        try:
            school = self.get_school()

            # Get query param for active only
            active_only = request.query_params.get(
                'active_only', 'false').lower() == 'true'

            if active_only:
                programmes = ProgrammeService.get_active_programmes(school)
            else:
                programmes = ProgrammeService.get_all_programmes(school)

            serializer = ProgrammeSerializer(programmes, many=True)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Get a single programme by ID",
        operation_summary="Retrieve a programme",
        responses={
            200: ProgrammeSerializer,
            404: "Programme not found"
        }
    )
    def retrieve(self, request, pk=None):
        """Get a single programme"""
        try:
            school = self.get_school()
            programme = ProgrammeService.get_programme_by_id(school, pk)
            if not programme:
                return Response(
                    {"detail": "Programme not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            serializer = ProgrammeSerializer(programme)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Create a new programme",
        operation_summary="Create a programme",
        request_body=ProgrammeCreateSerializer,
        responses={
            201: ProgrammeSerializer,
            400: "Bad request, validation error"
        }
    )
    def create(self, request):
        """Create a new programme"""
        serializer = ProgrammeCreateSerializer(data=request.data)

        if serializer.is_valid():
            try:
                school = self.get_school()
                result = ProgrammeService.create_programme(
                    school, serializer.validated_data)

                # Check if result is a Programme instance or an error dict
                if isinstance(result, Programme):
                    return Response(
                        ProgrammeSerializer(result).data,
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
        operation_description="Replace all fields of an existing programme",
        operation_summary="Full update of a programme",
        request_body=ProgrammeUpdateSerializer,
        responses={
            200: ProgrammeSerializer,
            404: "Programme not found",
            400: "Bad request, validation error"
        }
    )
    def update(self, request, pk=None):
        """Update an existing programme"""
        try:
            school = self.get_school()
            programme = ProgrammeService.get_programme_by_id(school, pk)

            if not programme:
                return Response(
                    {"detail": "Programme not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            serializer = ProgrammeUpdateSerializer(
                programme,
                data=request.data,
                partial=False  # PUT requires all fields
            )

            if serializer.is_valid():
                result = ProgrammeService.update_programme(
                    school, pk, serializer.validated_data
                )

                # Check if result is a Programme instance or an error dict
                if isinstance(result, Programme):
                    return Response(ProgrammeSerializer(result).data)
                elif result is None:
                    return Response(
                        {"detail": "Programme not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )
                else:
                    # Result is an error dict
                    return Response(result, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Update one or more fields of an existing programme",
        operation_summary="Partial update of a programme",
        request_body=ProgrammeUpdateSerializer,
        responses={
            200: ProgrammeSerializer,
            404: "Programme not found",
            400: "Bad request, validation error"
        }
    )
    def partial_update(self, request, pk=None):
        """Partially update an existing programme"""
        try:
            school = self.get_school()
            programme = ProgrammeService.get_programme_by_id(school, pk)

            if not programme:
                return Response(
                    {"detail": "Programme not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            serializer = ProgrammeUpdateSerializer(
                programme,
                data=request.data,
                partial=True  # PATCH allows partial update
            )

            if serializer.is_valid():
                result = ProgrammeService.update_programme(
                    school, pk, serializer.validated_data
                )

                # Check if result is a Programme instance or an error dict
                if isinstance(result, Programme):
                    return Response(ProgrammeSerializer(result).data)
                elif result is None:
                    return Response(
                        {"detail": "Programme not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )
                else:
                    # Result is an error dict
                    return Response(result, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Delete an existing programme",
        operation_summary="Delete a programme",
        responses={
            204: "No content, programme deleted successfully",
            404: "Programme not found"
        }
    )
    def destroy(self, request, pk=None):
        """Delete a programme"""
        try:
            school = self.get_school()
            success = ProgrammeService.delete_programme(school, pk)
            if not success:
                return Response(
                    {"detail": "Programme not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        operation_description="Toggle the active status of a programme",
        operation_summary="Toggle programme status",
        responses={
            200: ProgrammeSerializer,
            404: "Programme not found"
        }
    )
    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        """Toggle active status of a programme"""
        try:
            school = self.get_school()
            programme = ProgrammeService.toggle_programme_status(school, pk)
            if not programme:
                return Response(
                    {"detail": "Programme not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response(ProgrammeSerializer(programme).data)
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
