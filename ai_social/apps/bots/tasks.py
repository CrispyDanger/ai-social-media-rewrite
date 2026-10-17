from celery import shared_task

from apps.bots.models import BotPersona
from apps.bots.services.generation import generation
from apps.bots.services.guards import can_act
from apps.post.models import Post


@shared_task
def schedule_bot_posts() -> None:
    for persona in BotPersona.objects.filter(is_active=True):
        if can_act(persona):
            generate_bot_post.delay(persona.pk)


@shared_task
def generate_bot_post(persona_id: int) -> None:
    persona = BotPersona.objects.select_related('user').filter(pk=persona_id).first()
    if persona is not None:
        generation.generate_post(persona)


@shared_task
def react_to_post(persona_id: int, post_id: int) -> None:
    persona = BotPersona.objects.select_related('user').filter(pk=persona_id).first()
    post = Post.objects.select_related('author', 'parent', 'space').filter(pk=post_id).first()
    if persona is not None and post is not None:
        generation.react_to_post(persona, post)
