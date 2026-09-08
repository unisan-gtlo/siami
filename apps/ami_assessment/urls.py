from django.urls import path

from . import views

app_name = 'self_assessment'

urlpatterns = [
    path('', views.pengisian_detail, name='pengisian_detail'),
    path('butir/<int:butir_id>/', views.jawaban_edit, name='jawaban_edit'),
    path('upload-bukti/', views.upload_bukti, name='upload_bukti'),
    path('verifikasi/', views.dokumen_verifikasi_list, name='dokumen_verifikasi_list'),
    path('verifikasi/<int:dokumen_id>/', views.dokumen_verifikasi_action, name='dokumen_verifikasi_action'),
]
