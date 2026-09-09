from django.urls import path

from . import views

app_name = 'de'

urlpatterns = [
    path('dashboard/', views.dashboard_saya, name='dashboard'),
    path('', views.penugasan_list, name='penugasan_list'),
    path('tugaskan/', views.penugasan_create, name='penugasan_create'),
    path('<int:penugasan_id>/', views.penugasan_detail, name='penugasan_detail'),
    path('<int:penugasan_id>/butir/<int:butir_id>/', views.penilaian_edit, name='penilaian_edit'),
]
