from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SchoolAdminViewSet

router = DefaultRouter()
router.register(r'', SchoolAdminViewSet, basename='school')

urlpatterns = [
    path('', include(router.urls)),
]