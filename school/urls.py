from django.urls import path
from . import views

app_name = 'school'

urlpatterns = [
    # Configuration
    path('configuration/', views.school_configuration_view, name='configuration'),
    path('setup/', views.quick_setup_view, name='quick_setup'),
    path('setup-dashboard/', views.setup_dashboard_view, name='setup_dashboard'),
    
    # Academic Years
    path('academic-years/', views.AcademicYearListView.as_view(), name='academic_years'),
    path('academic-years/create/', views.AcademicYearCreateView.as_view(), name='academic_year_create'),
    path('academic-years/<int:pk>/edit/', views.AcademicYearUpdateView.as_view(), name='academic_year_edit'),
    path('academic-years/<int:pk>/delete/', views.AcademicYearDeleteView.as_view(), name='academic_year_delete'),
    
    # Programmes
    path('programmes/', views.ProgrammeListView.as_view(), name='programmes'),
    path('programmes/create/', views.ProgrammeCreateView.as_view(), name='programme_create'),
    path('programmes/<int:pk>/edit/', views.ProgrammeUpdateView.as_view(), name='programme_edit'),
    path('programmes/<int:pk>/delete/', views.ProgrammeDeleteView.as_view(), name='programme_delete'),
    
    # Houses
    path('houses/', views.HouseListView.as_view(), name='houses'),
    path('houses/create/', views.HouseCreateView.as_view(), name='house_create'),
    path('houses/<int:pk>/', views.HouseDetailView.as_view(), name='house_detail'),
    path('houses/<int:pk>/edit/', views.HouseUpdateView.as_view(), name='house_edit'),
    path('houses/<int:pk>/delete/', views.HouseDeleteView.as_view(), name='house_delete'),
    
    # Subjects
    path('subjects/', views.SubjectListView.as_view(), name='subjects'),
    path('subjects/create/', views.SubjectCreateView.as_view(), name='subject_create'),
    path('subjects/<int:pk>/edit/', views.SubjectUpdateView.as_view(), name='subject_edit'),
    path('subjects/<int:pk>/delete/', views.SubjectDeleteView.as_view(), name='subject_delete'),
    
    # Classes
    path('classes/', views.ClassListView.as_view(), name='classes'),
    path('classes/create/', views.ClassCreateView.as_view(), name='class_create'),
    path('classes/<int:pk>/edit/', views.ClassUpdateView.as_view(), name='class_edit'),
    path('classes/<int:pk>/delete/', views.ClassDeleteView.as_view(), name='class_delete'),
]