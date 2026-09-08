from django.urls import path

from . import views

app_name = 'laporan'

urlpatterns = [
    path('', views.laporan_list, name='laporan_list'),
    path('temuan-ptk/pdf/', views.laporan_temuan_pdf, name='laporan_temuan_pdf'),
    path('naratif/pdf/', views.laporan_naratif_pdf, name='laporan_naratif_pdf'),
    path('daftar-tilik/<int:penugasan_id>/pdf/', views.laporan_daftar_tilik_pdf, name='laporan_daftar_tilik_pdf'),
]
