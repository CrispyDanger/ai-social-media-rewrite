from django.conf import settings
from django.db import models

from apps.core.fields import EncryptedTextField


class UserSettings(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='settings',
    )
    openrouter_api_key = EncryptedTextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Settings of {self.user}'

    @property
    def has_openrouter_api_key(self):
        return bool(self.openrouter_api_key)

    def set_openrouter_api_key(self, value):
        self.openrouter_api_key = (value or '').strip()
