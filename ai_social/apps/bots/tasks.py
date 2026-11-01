from celery import shared_task

from apps.bots.models import BotPersona
from apps.bots.services.scheduling import enqueue_due_turns
from apps.bots.services.turns import run_scheduled_turn


@shared_task
def schedule_bot_turns() -> None:
    enqueue_due_turns()


@shared_task
def run_bot_turn(persona_id: int) -> None:
    persona = BotPersona.objects.select_related('user', 'space').filter(pk=persona_id).first()
    if persona is not None:
        run_scheduled_turn(persona)
