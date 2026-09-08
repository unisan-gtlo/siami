from django.urls import path

from . import views

app_name = 'instrumen'

urlpatterns = [
    path('', views.butir_list, name='butir_list'),
    path('tambah/', views.butir_create, name='butir_create'),
    path('<int:butir_id>/ubah/', views.butir_edit, name='butir_edit'),
    path('<int:butir_id>/hapus/', views.butir_delete, name='butir_delete'),
]
