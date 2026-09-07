from django.urls import path

from . import views

app_name = 'rtm'

urlpatterns = [
    path('', views.rtm_list, name='rtm_list'),
    path('<int:rtm_id>/', views.rtm_detail, name='rtm_detail'),
]
