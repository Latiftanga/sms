from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from core.models import School
from core.serializers import (
    SchoolUpdateSerializer, MyTokenObtainPairSerializer,
    LogoUploadSerializer
)
from core.permissions import IsSchoolAdmin
from rest_framework_simplejwt.views import TokenObtainPairView


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class SchoolAdminViewSet(viewsets.GenericViewSet):
    """
    ViewSet for school admins to view and partially update their own school.
    Only allows viewing the school and performing partial updates to specific fields.
    """
    serializer_class = SchoolUpdateSerializer
    permission_classes = [IsAuthenticated, IsSchoolAdmin]

    def get_queryset(self):
        """Return only the school associated with the current admin user"""
        if self.request.user.is_authenticated \
            and self.request.user.is_admin and self.request.user.school:
            return School.objects.filter(id=self.request.user.school.id)
        return School.objects.none()

    @action(
        detail=False, methods=['get'],
        url_name='school_info', url_path='school'
    )
    def info(self, request):
        """Return the school associated with the current admin user"""
        if request.user.school:
            serializer = self.get_serializer(request.user.school)
            return Response(serializer.data)
        return Response(
            {"detail": "You do not have a school associated with your account."},
            status=status.HTTP_404_NOT_FOUND
        )

    @action(
        detail=False, methods=['patch'],
        url_name='update_contact_info', url_path='school/update-contact'
    )
    def update_contact_info(self, request):
        """Update only contact information of the admin's school"""
        if not request.user.school:
            return Response(
                {"detail": "You do not have a school associated with your account."},
                status=status.HTTP_404_NOT_FOUND
            )

        school = request.user.school

        # Extract only contact fields
        contact_data = {}
        contact_fields = ['headmaster_name', 'email',
                          'phone_primary', 'phone_secondary', 'website']

        for field in contact_fields:
            if field in request.data:
                contact_data[field] = request.data[field]

        serializer = self.get_serializer(
            school, data=contact_data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    @action(detail=False, methods=['patch'], url_path='school/update-location')
    def update_location(self, request):
        """Update only location information of the admin's school"""
        if not request.user.school:
            return Response(
                {"detail": "You do not have a school associated with your account."},
                status=status.HTTP_404_NOT_FOUND
            )

        school = request.user.school

        # Extract only location fields
        location_data = {}
        location_fields = ['digital_address', 'physical_address']

        for field in location_fields:
            if field in request.data:
                location_data[field] = request.data[field]

        serializer = self.get_serializer(
            school, data=location_data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    @action(detail=False, methods=['patch'], url_path='school/update-basic-info')
    def update_basic_info(self, request):
        """Update basic information of the admin's school"""
        if not request.user.school:
            return Response(
                {"detail": "You do not have a school associated with your account."},
                status=status.HTTP_404_NOT_FOUND
            )

        school = request.user.school

        # Extract only basic info fields
        basic_data = {}
        basic_fields = ['name', 'motto', 'has_boarding']

        for field in basic_fields:
            if field in request.data:
                basic_data[field] = request.data[field]

        serializer = self.get_serializer(school, data=basic_data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    @action(
        detail=False,
        methods=['post'],
        parser_classes=[MultiPartParser, FormParser],
        # Use this serializer for this action only
        serializer_class=LogoUploadSerializer,
        url_path='school/upload-logo'
    )
    def upload_logo(self, request):
        """Upload a new logo for the admin's school"""
        if not request.user.school:
            return Response(
                {"detail": "You do not have a school associated with your account."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = LogoUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Update the logo
        school = request.user.school
        school.logo = serializer.validated_data['logo']
        school.save()

        return Response({
            "success": True,
            "message": "Logo uploaded successfully"
        })

        # Return just the logo URL in the response
        return Response({
            "logo": request.build_absolute_uri(school.logo.url) if school.logo else None
        })
