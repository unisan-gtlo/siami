from django.urls import path

from . import views

app_name = 'laporan'

urlpatterns = [
    path('', views.laporan_list, name='laporan_list'),
    path('temuan-ptk/pdf/', views.laporan_temuan_pdf, name='laporan_temuan_pdf'),
]
