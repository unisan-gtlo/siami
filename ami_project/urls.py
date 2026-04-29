"""
URL configuration for ami_project (SI-AMI UNISAN).
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # Django Admin Panel
    path('admin/', admin.site.urls),
    
    # API Documentation (drf-spectacular)
    # Akan diaktifkan saat Deliverable #2 (API REST)
    
    # SI-AMI Apps URLs
    # Akan ditambahkan saat masing-masing modul dikembangkan
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