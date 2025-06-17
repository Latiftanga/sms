from django.urls import path
from core import views as core_views

app_name = 'teacher'

urlpatterns = [
    path('', core_views.teacher_dashboard, name='teacher_dashboard'),
]
