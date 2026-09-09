from django.urls import path

from . import views

app_name = 'instrumen'

urlpatterns = [
    path('', views.butir_list, name='butir_list'),
    path('tambah/', views.butir_create, name='butir_create'),
    path('<int:butir_id>/ubah/', views.butir_edit, name='butir_edit'),
    path('<int:butir_id>/hapus/', views.butir_delete, name='butir_delete'),
    path('siklus/', views.siklus_list, name='siklus_list'),
    path('siklus/tambah/', views.siklus_create, name='siklus_create'),
    path('siklus/<int:siklus_id>/ubah/', views.siklus_edit, name='siklus_edit'),
    path('siklus/<int:siklus_id>/aktifkan/', views.siklus_aktifkan, name='siklus_aktifkan'),
]
