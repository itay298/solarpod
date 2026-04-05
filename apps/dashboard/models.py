from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
# Create your models here.

USER_MODEL = get_user_model()

class Device(models.Model):
    name = models.CharField(_("Device name"), max_length=31)
    mac_address = models.CharField(_("Mac address"), max_length=31, unique=True)
    owner = models.ForeignKey(USER_MODEL, on_delete=models.CASCADE, related_name="devices", related_query_name="device", verbose_name=_("owner"))
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    def __str__(self):
        return f"{self.name} - {self.mac_address} - {self.owner.username}"
    
    @property
    def latest_telemetry(self):
        return self.telemetries.order_by('-timestamp').first()
    class Meta:
        verbose_name = _("Device")
        verbose_name_plural = _("Devices")


class Telemetry(models.Model):    
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="telemetries", related_query_name="telemetry", verbose_name=_("device"))
    timestamp = models.DateTimeField(_("Timestamp"), auto_now_add=True)
    voltage = models.DecimalField(_("Voltage"), max_digits=5, decimal_places=2, help_text=_("Voltage in [v]"))
    current = models.DecimalField(_("Current[A]"), max_digits=7, decimal_places=4, help_text=_("Current in [A]"))
    power = models.DecimalField(_("Power"), max_digits=6, decimal_places=3, help_text=_("Power in [W]"), blank=True)
    battery_level = models.IntegerField(_("battery level")) # אחוזים מ-0 עד 100
    tracker_angle_x = models.IntegerField(_("Tracker angle horizontal"),null=True, blank=True)
    tracker_angle_y = models.IntegerField(_("Tracker angle vertical"),null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if self.voltage is not None and self.current is not None:
            self.power = round(self.voltage * self.current, 3)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.device.name} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        verbose_name = _("Telemetry")
        verbose_name_plural = _("Telemetries")
        
class ServerHealth(models.Model):
    timestamp = models.DateTimeField(_("Timestamp"), auto_now_add=True)
    battery_level = models.IntegerField(_("Battery level"))
    
    def __str__(self):
        return f"{self.timestamp.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        verbose_name = _("Server Health")
        verbose_name_plural = _("Servers Health")
