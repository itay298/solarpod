from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
# Create your models here.

class SolarpodUser(AbstractUser):
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')