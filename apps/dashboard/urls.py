from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_view, name='index'),
    path('api/chart-data/<int:device_id>/<str:metric>/', views.get_chart_data, name='api_chart_data'),
    path('api/receive_telemetry/', views.api_receive_telemetry, name='api_receive_telemetry'),
    path('api/telemetry/latest/all/', views.api_get_all_latest, name='api_get_all_latest'),
    path('api/server/receive/', views.api_receive_server, name='api_receive_server'),
    path('api/time/sync/', views.api_sync_time, name='api_sync_time'),
]