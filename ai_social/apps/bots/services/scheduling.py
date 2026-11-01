import random
from collections.abc import Callable
from datetime import datetime

from django.core.cache import cache
from django.utils import timezone

from apps.bots.models import BotPersona
from apps.bots.services.guards import can_act

COUNTDOWN_MAX_SECONDS = 50


def enqueue_due_turns(now: datetime | None = None) -> None:
    from apps.bots.tasks import run_bot_turn

    now = now or timezone.now()
    for persona in due_personas(now):
        enqueue_turn(persona, run_bot_turn)


def due_personas(now: datetime) -> list[BotPersona]:
    active = BotPersona.objects.filter(is_active=True).select_related('user')
    return [persona for persona in active if can_act(persona, now)]


def enqueue_turn(persona: BotPersona, task: Callable) -> None:
    if reserve_turn(persona):
        countdown = random.randint(0, COUNTDOWN_MAX_SECONDS)
        task.apply_async((persona.pk,), countdown=countdown)


def reserve_turn(persona: BotPersona) -> bool:
    return cache.add(turn_lock_key(persona.pk), 1, COUNTDOWN_MAX_SECONDS)


def release_reservation(persona: BotPersona) -> None:
    cache.delete(turn_lock_key(persona.pk))


def turn_lock_key(persona_id: int) -> str:
    return f'bots:turn:{persona_id}'
