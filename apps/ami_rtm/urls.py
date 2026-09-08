from django.urls import path

from . import views

app_name = 'rtm'

urlpatterns = [
    path('', views.rtm_list, name='rtm_list'),
    path('<int:rtm_id>/', views.rtm_detail, name='rtm_detail'),
    path('<int:rtm_id>/pdf/', views.rtm_export_pdf, name='rtm_export_pdf'),
    path('agenda/<int:agenda_id>/vote/', views.rtm_vote, name='rtm_vote'),
    path('agenda/<int:agenda_id>/keputusan/', views.rtm_agenda_keputusan, name='rtm_agenda_keputusan'),
]
