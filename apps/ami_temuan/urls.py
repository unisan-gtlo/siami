from django.urls import path

from . import views

app_name = 'temuan'

urlpatterns = [
    path('', views.temuan_list, name='temuan_list'),
    path('fvtb/<int:fvtb_id>/', views.fvtb_update, name='fvtb_update'),
    path('dari-de/<int:penilaian_id>/', views.temuan_create_from_de, name='temuan_create_from_de'),
]
