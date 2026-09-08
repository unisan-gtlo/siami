from django.urls import path

from . import views

app_name = 'user_auditor'

urlpatterns = [
    path('', views.user_auditor_list, name='user_auditor_list'),
    path('pakta-integritas/tandatangani/', views.sign_pakta_integritas, name='sign_pakta_integritas'),
]
