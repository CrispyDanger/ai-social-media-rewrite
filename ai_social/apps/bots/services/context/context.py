from collections.abc import Iterator
from datetime import datetime

from django.conf import settings
from django.utils import timezone

from apps.bots.models import BotPersona
from apps.bots.services.context import activity
from apps.post.models import Post
from apps.space.models import Space

RECENT_POSTS_LIMIT = 5


def iter_ancestors(post: Post, limit: int) -> Iterator[Post]:
    current = post.parent
    while current is not None and limit > 0:
        yield current
        current = current.parent
        limit -= 1


def thread_depth(post: Post, limit: int) -> int:
    return sum(1 for _ in iter_ancestors(post, limit))


def render_post(post: Post) -> str:
    return f'@{post.author.username}: {post.text}'


def render_thread(post: Post) -> str:
    ancestors = reversed(list(iter_ancestors(post, settings.BOT_MAX_THREAD_DEPTH)))
    lines = [render_post(ancestor) for ancestor in ancestors]
    lines.append(f'>>> {render_post(post)}')
    return '\n'.join(lines)


def build_post_prompt(persona: BotPersona) -> str:
    texts = Post.objects.filter(author_id=persona.user_id).values_list('text', flat=True)
    recent = list(texts[:RECENT_POSTS_LIMIT])
    recent_posts = '\n'.join(f'- {text}' for text in recent) or 'You have not posted anything yet.'
    return (
        'Write one new original post for your timeline.\n'
        'Do not repeat topics or phrasing from your recent posts:\n'
        f'{recent_posts}'
    )


def build_reply_prompt(persona: BotPersona, post: Post) -> str:
    return (
        f'You are @{persona.user.username}. This is what is going on around you:\n\n'
        f'{render_situation(persona, post)}\n\n'
        'Write a reply to the post marked with >>>.'
    )


def render_situation(persona: BotPersona, post: Post, now: datetime | None = None) -> str:
    now = now or timezone.now()
    sections = [
        render_world(post.space),
        render_section('What they did recently', render_recent_activity(persona, now)),
        render_section('New notifications', render_notifications(persona)),
        render_section('Their timeline right now (newest first)',
                       render_timeline(persona, post.space_id)),
        render_section('The post in question (marked with >>>)', render_thread(post)),
    ]
    return '\n\n'.join(section for section in sections if section)


def render_world(space: Space | None) -> str | None:
    if space is None:
        return None
    if not space.description:
        return f'World: {space.name}'
    return f'World: {space.name}. {space.description}'


def render_section(title: str, body: str) -> str:
    return f'{title}:\n{body}'


def render_recent_activity(persona: BotPersona, now: datetime) -> str:
    events = activity.recent_activity(persona.user_id)
    if not events:
        return '- nothing yet'
    return '\n'.join(f'- {format_age(event.at, now)}: {event.text}' for event in events)


def render_notifications(persona: BotPersona) -> str:
    events = activity.new_notifications(persona)
    if not events:
        return '- nothing new'
    return '\n'.join(f'- {event.text}' for event in events)


def render_timeline(persona: BotPersona, space_id: int | None) -> str:
    posts = activity.timeline_posts(persona, space_id)
    if not posts:
        return '- empty'
    return '\n'.join(
        f'{number}. @{post.author.username}: "{post.text}"'
        for number, post in enumerate(posts, start=1)
    )


def format_age(at: datetime, now: datetime) -> str:
    minutes = int((now - at).total_seconds() // 60)
    if minutes < 1:
        return 'just now'
    if minutes < 60:
        return f'{minutes}m ago'
    if minutes < 60 * 24:
        return f'{minutes // 60}h ago'
    return f'{minutes // (60 * 24)}d ago'
