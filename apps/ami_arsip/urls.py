from django.urls import path

from . import views

app_name = 'arsip'

urlpatterns = [
    path('', views.arsip_list, name='arsip_list'),
    path('upload/', views.arsip_upload, name='arsip_upload'),
    path('siklus/<int:siklus_id>/', views.arsip_siklus_detail, name='arsip_siklus_detail'),
]
