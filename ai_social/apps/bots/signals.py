from functools import partial

from django.db import transaction
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from apps.bots.services.guards import is_bot_user
from apps.bots.services.personas.personas import delete_space_bot_accounts
from apps.bots.services.targeting.targeting import resolve_target_bot_ids
from apps.bots.tasks import react_to_post
from apps.post.models import Post
from apps.space.models import Space


@receiver(post_save, sender=Post)
def schedule_bot_reactions(sender, instance, created, **kwargs):
    if not created or is_bot_user(instance.author_id):
        return
    for persona_id in resolve_target_bot_ids(instance):
        transaction.on_commit(partial(react_to_post.delay, persona_id, instance.pk))


@receiver(pre_delete, sender=Space)
def remove_space_bots(sender, instance, **kwargs):
    delete_space_bot_accounts(instance)
