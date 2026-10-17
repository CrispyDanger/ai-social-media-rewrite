from django.contrib.auth import get_user_model
from django.db import transaction

from apps.bots.models import BotPersona
from apps.bots.services.personas.handles import provision_bot_user
from apps.space.models import Membership, Space


class BotLimitReached(Exception):
    pass


def create_owned_persona(*, owner, space, name, persona_prompt) -> BotPersona:
    with transaction.atomic():
        Space.objects.select_for_update().get(pk=space.pk)
        if BotPersona.objects.filter(space_id=space.pk).count() >= BotPersona.MAX_PER_SPACE:
            raise BotLimitReached
        bot_user = provision_bot_user(name)
        Membership.objects.create(space=space, user=bot_user)
        return BotPersona.objects.create(
            user=bot_user,
            owner=owner,
            space=space,
            name=name,
            persona_prompt=persona_prompt,
        )


def sync_bot_display_name(user, name: str) -> None:
    user.display_name = name
    user.save(update_fields=['display_name'])


def delete_persona(persona: BotPersona) -> None:
    persona.user.delete()


def delete_space_bot_accounts(space) -> None:
    user_ids = list(
        BotPersona.objects.filter(space=space).values_list('user_id', flat=True)
    )
    if not user_ids:
        return
    get_user_model().objects.filter(pk__in=user_ids).delete()
