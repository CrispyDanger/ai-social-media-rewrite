from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone

from apps.bots.models import BotPersona
from apps.bots.services.context.context import thread_depth
from apps.interaction.models import Like
from apps.post.models import Post, Repost

DAILY_WINDOW = timedelta(days=1)


def is_bot_user(user_id: int) -> bool:
    return BotPersona.objects.filter(user_id=user_id).exists()


def can_act(persona: BotPersona, now: datetime | None = None) -> bool:
    now = now or timezone.now()
    if not persona.is_active:
        return False
    cooldown = timedelta(seconds=persona.cooldown_seconds)
    if persona.last_action_at is not None and now - persona.last_action_at < cooldown:
        return False
    user_id, since = persona.user_id, now - DAILY_WINDOW
    recent_actions = (
        Post.objects.filter(author_id=user_id, created_at__gte=since).count()
        + Like.objects.filter(user_id=user_id, created_at__gte=since).count()
        + Repost.objects.filter(author_id=user_id, created_at__gte=since).count()
    )
    return recent_actions < persona.daily_action_limit


def should_react(persona: BotPersona, post: Post) -> bool:
    max_depth = settings.BOT_MAX_THREAD_DEPTH
    return (
        post.author_id != persona.user_id
        and not is_bot_user(post.author_id)
        and thread_depth(post, max_depth) < max_depth
    )
