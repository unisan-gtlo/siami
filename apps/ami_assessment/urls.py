from django.urls import path

from . import views

app_name = 'self_assessment'

urlpatterns = [
    path('', views.pengisian_detail, name='pengisian_detail'),
    path('butir/<int:butir_id>/', views.jawaban_edit, name='jawaban_edit'),
]
