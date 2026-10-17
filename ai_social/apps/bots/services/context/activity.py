from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from itertools import chain
from operator import attrgetter

from django.db.models import QuerySet

from apps.account.models import Follow
from apps.bots.models import BotPersona
from apps.feed.services.timeline import following_posts
from apps.interaction.models import Like
from apps.post.models import Post, Repost

SECTION_LIMIT = 5


@dataclass(frozen=True)
class Event:
    at: datetime
    text: str


def recent_activity(user_id: int) -> list[Event]:
    posts = _latest(Post.objects.filter(author_id=user_id).select_related('parent__author'))
    likes = _latest(Like.objects.filter(user_id=user_id).select_related('post__author'))
    reposts = _latest(Repost.objects.filter(author_id=user_id).select_related('post__author'))
    return _newest_first(chain(
        (Event(post.created_at, f'posted "{post.text}"' if post.parent_id is None
               else f'replied to @{post.parent.author.username}: "{post.text}"') for post in posts),
        (Event(like.created_at, f'liked a post by @{like.post.author.username}') for like in likes),
        (Event(repost.created_at, f'reposted a post by @{repost.post.author.username}')
         for repost in reposts),
    ))


def new_notifications(persona: BotPersona) -> list[Event]:
    user_id, since = persona.user_id, persona.last_action_at
    replies = Post.objects.filter(parent__author_id=user_id).exclude(author_id=user_id)
    likes = Like.objects.filter(post__author_id=user_id).exclude(user_id=user_id)
    reposts = Repost.objects.filter(post__author_id=user_id).exclude(author_id=user_id)
    follows = Follow.objects.filter(following_id=user_id)
    return _newest_first(chain(
        (Event(reply.created_at, f'@{reply.author.username} replied to their post: "{reply.text}"')
         for reply in _latest(replies.select_related('author'), since)),
        (Event(like.created_at, f'@{like.user.username} liked their post: "{like.post.text}"')
         for like in _latest(likes.select_related('user', 'post'), since)),
        (Event(repost.created_at, f'@{repost.author.username} reposted their post: "{repost.post.text}"')
         for repost in _latest(reposts.select_related('author', 'post'), since)),
        (Event(follow.created_at, f'@{follow.follower.username} followed them')
         for follow in _latest(follows.select_related('follower'), since)),
    ))


def timeline_posts(persona: BotPersona, space_id: int | None) -> list[Post]:
    posts = following_posts(persona.user).exclude(author_id=persona.user_id)
    return list(posts.filter(space_id=space_id)[:SECTION_LIMIT])


def _latest(queryset: QuerySet, since: datetime | None = None) -> QuerySet:
    if since is not None:
        queryset = queryset.filter(created_at__gt=since)
    return queryset.order_by('-created_at')[:SECTION_LIMIT]


def _newest_first(events: Iterable[Event]) -> list[Event]:
    return sorted(events, key=attrgetter('at'), reverse=True)[:SECTION_LIMIT]
