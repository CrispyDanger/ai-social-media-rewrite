from datetime import datetime

from django.db.models import QuerySet
from django.utils import timezone

from apps.bots.models import BotPersona
from apps.bots.services.context import activity
from apps.bots.services.generation.generation import apply_reaction, write_post
from apps.bots.services.guards import can_act, should_react
from apps.bots.services.scheduling import release_reservation
from apps.bots.services.targeting.mentions import extract_handles
from apps.post.models import Post


def run_scheduled_turn(persona: BotPersona) -> None:
    if not can_act(persona):
        release_reservation(persona)
        return
    take_turn(persona)


def take_turn(persona: BotPersona) -> None:
    addressed = addressed_posts(persona)
    started = begin_turn(persona)
    release_reservation(persona)
    if not started:
        return
    if addressed:
        react_to_addressed(persona, addressed)
        return
    write_post(persona)


def react_to_addressed(persona: BotPersona, addressed: list[Post]) -> None:
    for post in reaction_targets(persona, addressed):
        apply_reaction(persona, post)


def addressed_posts(persona: BotPersona) -> list[Post]:
    posts = posts_since(human_posts(), persona.last_action_at)
    replies = posts.filter(parent__author_id=persona.user_id)
    mentions = mentioned_posts(posts, persona.user.username)
    return unique_posts([*mentions, *replies])


def reaction_targets(persona: BotPersona, addressed: list[Post]) -> list[Post]:
    timeline = activity.timeline_posts(persona, persona.space_id)
    return unseen_reactable(persona, [*addressed, *timeline])


def unseen_reactable(persona: BotPersona, posts: list[Post]) -> list[Post]:
    seen: set[int] = set()
    targets: list[Post] = []
    for post in posts:
        if post.pk in seen or not should_react(persona, post):
            continue
        seen.add(post.pk)
        targets.append(post)
    return targets


def human_posts() -> QuerySet[Post]:
    bot_user_ids = BotPersona.objects.values('user_id')
    return Post.objects.exclude(author_id__in=bot_user_ids).select_related('author', 'parent', 'space')


def posts_since(posts: QuerySet[Post], since: datetime | None) -> QuerySet[Post]:
    if since is None:
        return posts
    return posts.filter(created_at__gt=since)


def mentioned_posts(posts: QuerySet[Post], username: str) -> list[Post]:
    handle = username.lower()
    candidates = posts.filter(text__icontains=f'@{username}')
    return [post for post in candidates if handle in extract_handles(post.text)]


def unique_posts(posts: list[Post]) -> list[Post]:
    seen: set[int] = set()
    unique: list[Post] = []
    for post in posts:
        if post.pk in seen:
            continue
        seen.add(post.pk)
        unique.append(post)
    return unique


def begin_turn(persona: BotPersona) -> bool:
    now = timezone.now()
    updated = (
        BotPersona.objects.filter(pk=persona.pk)
        .filter(**last_action_lookup(persona))
        .update(last_action_at=now)
    )
    if not updated:
        return False
    persona.last_action_at = now
    return True


def last_action_lookup(persona: BotPersona) -> dict[str, object]:
    if persona.last_action_at is None:
        return {'last_action_at__isnull': True}
    return {'last_action_at': persona.last_action_at}
