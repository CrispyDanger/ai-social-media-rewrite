from django.conf import settings
from django.db import models


def avatar_upload_to(instance, filename):
    return f'avatars/{instance.user_id}/{filename}'


def header_upload_to(instance, filename):
    return f'headers/{instance.user_id}/{filename}'


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    bio = models.CharField(max_length=160, blank=True)
    avatar = models.ImageField(upload_to=avatar_upload_to, blank=True, null=True)
    header = models.ImageField(upload_to=header_upload_to, blank=True, null=True)
    location = models.CharField(max_length=30, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Profile of {self.user}'
