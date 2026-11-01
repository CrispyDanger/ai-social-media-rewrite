from django.db.models.signals import pre_delete
from django.dispatch import receiver

from apps.bots.services.personas.personas import delete_space_bot_accounts
from apps.space.models import Space


@receiver(pre_delete, sender=Space)
def remove_space_bots(sender, instance, **kwargs):
    delete_space_bot_accounts(instance)
