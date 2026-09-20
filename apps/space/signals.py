from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.space.models import Membership, Space


@receiver(post_save, sender=Space)
def add_creator_as_member(sender, instance, created, **kwargs):
    if created and instance.created_by_id:
        Membership.objects.get_or_create(
            space=instance,
            user_id=instance.created_by_id,
        )
