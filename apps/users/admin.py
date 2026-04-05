from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
USER_MODEL = get_user_model()
# Register your custom UserAdmin
@admin.register(USER_MODEL)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'is_staff', 'date_joined')
    readonly_fields = ('date_joined',)

admin.site.site_header = _("SolarPod admin")
admin.site.unregister(Group)