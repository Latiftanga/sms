from django.urls import path
from django.contrib.auth.decorators import login_required
from core import views

urlpatterns = [
    # Authentication URLs
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('dashboard/', login_required(views.dashboard), name='dashboard'),
    
    # Settings
    path('settings/', views.school_settings, name='school_settings'),
    path('settings/school/', views.school_settings, name='school_settings'),
    
    # Profile
    path('profile/', views.profile_view, name='profile'),

]
