from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.account.models import Profile, User


@receiver(post_save, sender=User)
def create_user_related_rows(sender, instance, created, **kwargs):
    if not created:
        return
    Profile.objects.create(user=instance)
