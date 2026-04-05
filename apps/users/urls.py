from django.urls import path
from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView
from . import views

app_name = 'users'

urlpatterns = [
    path('login/', LoginView.as_view(template_name="users/login.html") , name='login'),
    path('api/wifi/scan/', views.api_scan_wifi, name='api_scan_wifi'),
    path('api/wifi/connect/', views.api_connect_wifi, name='api_connect_wifi'),
    path('api/wifi/status/', views.api_wifi_status, name='api_wifi_status'),
    path('api/wifi/disconnect/', views.api_wifi_disconnect, name='api_wifi_disconnect'),
]