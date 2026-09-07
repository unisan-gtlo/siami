from django.urls import path

from . import views

app_name = 'identitas'

urlpatterns = [
    path('', views.identitas_prodi, name='prodi'),
]
