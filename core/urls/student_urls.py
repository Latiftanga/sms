from django.urls import path
from core import views as core_views

app_name = 'student'

urlpatterns = [
    path('', core_views.student_dashboard, name='student_dashboard'),
]
