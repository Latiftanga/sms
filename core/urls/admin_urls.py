# ===== dashboard/urls/admin.py - Admin Routes =====
from django.urls import path
from core import views
from school import views as school_views
from student import views as student_views

app_name = 'admin'

urlpatterns = [
    # Admin Dashboard
    path('', views.admin_dashboard, name='admin_dashboard'),

    path('configuration/', school_views.school_configuration_view, name='configuration'),
    path('setup/', school_views.quick_setup_view, name='quick_setup'),
    path('setup-school/', school_views.setup_school_view, name='setup_school'),

     # Academic Years
    path('academic-years/', school_views.AcademicYearListView.as_view(), name='academic_years'),
    path('academic-years/create/', school_views.AcademicYearCreateView.as_view(), name='academic_year_create'),
    path('academic-years/<int:pk>/edit/', school_views.AcademicYearUpdateView.as_view(), name='academic_year_edit'),
    path('academic-years/<int:pk>/delete/', school_views.AcademicYearDeleteView.as_view(), name='academic_year_delete'),
    
    # Programmes
    path('programmes/', school_views.ProgrammeListView.as_view(), name='programmes'),
    path('programmes/create/', school_views.ProgrammeCreateView.as_view(), name='programme_create'),
    path('programmes/<int:pk>/edit/', school_views.ProgrammeUpdateView.as_view(), name='programme_edit'),
    path('programmes/<int:pk>/delete/', school_views.ProgrammeDeleteView.as_view(), name='programme_delete'),
    
    # Houses
    path('houses/', school_views.HouseListView.as_view(), name='houses'),
    path('houses/create/', school_views.HouseCreateView.as_view(), name='house_create'),
    path('houses/<int:pk>/', school_views.HouseDetailView.as_view(), name='house_detail'),
    path('houses/<int:pk>/edit/', school_views.HouseUpdateView.as_view(), name='house_edit'),
    path('houses/<int:pk>/delete/', school_views.HouseDeleteView.as_view(), name='house_delete'),
    
    # Subjects
    path('subjects/', school_views.SubjectListView.as_view(), name='subjects'),
    path('subjects/create/', school_views.SubjectCreateView.as_view(), name='subject_create'),
    path('subjects/<int:pk>/edit/', school_views.SubjectUpdateView.as_view(), name='subject_edit'),
    path('subjects/<int:pk>/delete/', school_views.SubjectDeleteView.as_view(), name='subject_delete'),
    
    # Classes
    path('classes/', school_views.ClassListView.as_view(), name='classes'),
    path('classes/create/', school_views.ClassCreateView.as_view(), name='class_create'),
    path('classes/<int:pk>/edit/', school_views.ClassUpdateView.as_view(), name='class_edit'),
    path('classes/<int:pk>/delete/', school_views.ClassDeleteView.as_view(), name='class_delete'),

    # Student CRUD URLs
    path('students/', student_views.StudentListView.as_view(), name='student_list'),
    path('students//create/', student_views.StudentCreateView.as_view(), name='student_create'),
    path('students/<int:pk>/', student_views.StudentDetailView.as_view(), name='student_detail'),
    path('students/<int:pk>/edit/', student_views.StudentUpdateView.as_view(), name='student_edit'),
    path('students/<int:pk>/delete/', student_views.StudentDeleteView.as_view(), name='student_delete'),
    path('students/bulk-upload/', student_views.BulkUploadView.as_view(), name='bulk_upload'),
    path('students/download-template/', student_views.download_template, name='download_template'),
    path('students/promotion/', student_views.PromotionView.as_view(), name='promotion'),
    path('students/ajax/students-by-class/', student_views.ajax_get_students_by_class, name='ajax_students_by_class'),
    path('students/statistics/', student_views.student_statistics, name='statistics'),
    path('students/inactive/', student_views.InactiveStudentsView.as_view(), name='inactive_students'),
    path('students/<int:pk>/reactivate/', student_views.reactivate_student, name='reactivate_student'),
]
