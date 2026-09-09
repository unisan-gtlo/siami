from django.urls import path

from . import views

app_name = 'visitasi'

urlpatterns = [
    path('dashboard/', views.dashboard_saya, name='dashboard'),
    path('', views.visitasi_saya, name='visitasi_saya'),
    path('<int:visitasi_id>/konfirmasi/', views.konfirmasi_kehadiran, name='konfirmasi_kehadiran'),
]
