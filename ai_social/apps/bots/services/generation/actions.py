from django.db import transaction
from django.utils import timezone

from apps.bots.models import BotPersona
from apps.bots.services.generation import schemas
from apps.interaction.models import Like
from apps.post.models import Post, Repost


def publish_post(persona: BotPersona, text: str) -> Post:
    with transaction.atomic():
        post = Post.objects.create(author_id=persona.user_id,
                                   text=text,
                                   space_id=persona.space_id)
        mark_acted(persona)
    return post


def execute_decisions(persona: BotPersona, post: Post, decisions: list[schemas.Decision]) -> None:
    if not decisions:
        return
    user_id = persona.user_id
    with transaction.atomic():
        for decision in decisions:
            match decision:
                case schemas.Reply(text=text):
                    Post.objects.create(author_id=user_id, text=text, parent=post, space_id=post.space_id)
                case schemas.Like():
                    Like.objects.get_or_create(user_id=user_id, post=post)
                case schemas.Repost():
                    Repost.objects.get_or_create(author_id=user_id, post=post)
        mark_acted(persona)


def mark_acted(persona: BotPersona) -> None:
    persona.last_action_at = timezone.now()
    persona.save(update_fields=['last_action_at', 'updated_at'])
