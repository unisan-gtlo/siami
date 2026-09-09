from django.urls import path

from . import views

app_name = 'user_auditor'

urlpatterns = [
    path('', views.user_auditor_list, name='user_auditor_list'),
    path('pakta-integritas/tandatangani/', views.sign_pakta_integritas, name='sign_pakta_integritas'),
    path('<int:user_id>/', views.user_detail, name='user_detail'),
    path('<int:user_id>/konfirmasi-pakta/', views.konfirmasi_pakta, name='konfirmasi_pakta'),
    path('tambah/', views.tambah_auditor, name='tambah_auditor'),
    path('import-excel/', views.import_excel_auditor, name='import_excel'),
    path('import-excel/template/', views.download_template_excel, name='download_template_excel'),
    path('generate-sk/', views.generate_sk, name='generate_sk'),
]
