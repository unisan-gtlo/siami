from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.lp3m_dashboard, name='lp3m'),
]
