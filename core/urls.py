from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('', include('apps.dashboard.urls', 'dashboard')),
    path('users/', include('apps.users.urls', 'users')),
]
