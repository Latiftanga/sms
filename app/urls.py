from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import home_view


urlpatterns = [
    path('admin/', include('core.urls.admin_urls')),
    path('student/', include('core.urls.student_urls')),
    path('teacher/', include('core.urls.teacher_urls')),
    path('', include('account.urls')),
    path('', home_view, name='home'),
]


# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0]
    )
