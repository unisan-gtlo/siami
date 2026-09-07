"""
URL configuration for ami_project (SI-AMI UNISAN).
"""

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # Halaman utama -> arahkan ke portal (yang belum login otomatis diarahkan ke /login/)
    path('', RedirectView.as_view(pattern_name='self_assessment:pengisian_detail', permanent=False)),

    # Django Admin Panel
    path('admin/', admin.site.urls),

    # Login/logout portal (bukan /admin/)
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # API Documentation (drf-spectacular)
    # Akan diaktifkan saat Deliverable #2 (API REST)

    # SI-AMI Apps URLs
    path('self-assessment/', include('apps.ami_assessment.urls', namespace='self_assessment')),
    path('dashboard/', include('apps.ami_dashboard.urls', namespace='dashboard')),
]

# Serve static & media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Django Debug Toolbar (only in DEBUG mode)
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]