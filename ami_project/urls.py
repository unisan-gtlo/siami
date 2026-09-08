"""
URL configuration for ami_project (SI-AMI UNISAN).
"""

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, re_path, include
from django.views.generic import RedirectView
from django.views.static import serve as serve_static
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
    path('identitas/', include('apps.ami_master.urls', namespace='identitas')),
    path('self-assessment/', include('apps.ami_assessment.urls', namespace='self_assessment')),
    path('dashboard/', include('apps.ami_dashboard.urls', namespace='dashboard')),
    path('de/', include('apps.ami_de.urls', namespace='de')),
    path('visitasi/', include('apps.ami_visitasi.urls', namespace='visitasi')),
    path('temuan/', include('apps.ami_temuan.urls', namespace='temuan')),
    path('rtm/', include('apps.ami_rtm.urls', namespace='rtm')),
    path('laporan/', include('apps.ami_pelaporan.urls', namespace='laporan')),
    path('user-auditor/', include('apps.ami_user.urls', namespace='user_auditor')),
    path('arsip/', include('apps.ami_arsip.urls', namespace='arsip')),
    path('instrumen/', include('apps.ami_core.urls', namespace='instrumen')),
]

# Media (dokumen bukti, dll) disajikan langsung oleh Django -- MEDIA_ROOT ada
# di Docker named volume (bukan bind mount ke path host), jadi nginx tidak
# punya jalur mudah untuk alias langsung ke sana. Trafik upload dokumen audit
# di sistem ini kecil, sehingga performa serving lewat Django cukup.
#
# django.conf.urls.static.static() TIDAK bisa dipakai di sini -- fungsi itu
# selalu me-return [] kalau settings.DEBUG=False, di manapun dipanggil.
# Panggil view serve bawaan Django secara langsung supaya jalan juga di prod.
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve_static, {'document_root': settings.MEDIA_ROOT}),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Django Debug Toolbar (only in DEBUG mode)
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]