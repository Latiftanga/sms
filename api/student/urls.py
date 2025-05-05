from django.urls import path, include
from rest_framework.routers import DefaultRouter
from student.views.class_views import ClassViewSet
from student.views.programme_views import ProgrammeViewSet

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'programmes', ProgrammeViewSet, basename='programme')
router.register(r'classes', ClassViewSet, basename='class')

# API URLs
urlpatterns = [
    path('', include(router.urls)),
]