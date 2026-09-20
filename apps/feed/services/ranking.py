from collections import Counter
from datetime import timedelta

from django.db.models import Count
from django.utils import timezone

from apps.interaction.models import Like
from apps.post.models import Post, Repost

DECAY_OFFSET = 2
DECAY_EXPONENT = 1.5
REPOST_WEIGHT = 2
AFFINITY_MULTIPLIER = 1.5
AFFINITY_WINDOW_DAYS = 30
AFFINITY_MIN_INTERACTIONS = 3
CANDIDATE_WINDOW_DAYS = 7
CANDIDATE_LIMIT = 500


def engagement_from_counts(like_count, repost_count, reply_count):
    return like_count + REPOST_WEIGHT * repost_count + reply_count


def age_hours(created_at, now):
    return (now - created_at).total_seconds() / 3600


def compute_score(engagement, age_hours_value, has_affinity):
    score = engagement / ((age_hours_value + DECAY_OFFSET) ** DECAY_EXPONENT)
    if has_affinity:
        score *= AFFINITY_MULTIPLIER
    return score


def score_post(post, now, affinity_ids):
    engagement = engagement_from_counts(
        post.like_count,
        post.repost_count,
        post.reply_count,
    )
    has_affinity = post.author_id in affinity_ids
    hours = age_hours(post.created_at, now)
    return compute_score(engagement, hours, has_affinity)


def author_ids_user_interacts_often_with(user, now=None):
    now = now or timezone.now()
    since = now - timedelta(days=AFFINITY_WINDOW_DAYS)
    counts = _interaction_counts_by_author(user, since)
    return {
        author_id
        for author_id, total in counts.items()
        if total >= AFFINITY_MIN_INTERACTIONS
    }


def _interaction_counts_by_author(user, since):
    counts = Counter()
    counts.update(_liked_author_counts(user, since))
    counts.update(_reposted_author_counts(user, since))
    counts.update(_replied_author_counts(user, since))
    return counts


def _liked_author_counts(user, since):
    rows = (
        Like.objects.filter(user=user, created_at__gte=since)
        .exclude(post__author=user)
        .values('post__author_id')
        .annotate(n=Count('id'))
    )
    return {row['post__author_id']: row['n'] for row in rows}


def _reposted_author_counts(user, since):
    rows = (
        Repost.objects.filter(author=user, created_at__gte=since)
        .exclude(post__author=user)
        .values('post__author_id')
        .annotate(n=Count('id'))
    )
    return {row['post__author_id']: row['n'] for row in rows}


def _replied_author_counts(user, since):
    rows = (
        Post.objects.filter(
            author=user,
            parent__isnull=False,
            created_at__gte=since,
        )
        .exclude(parent__author=user)
        .values('parent__author_id')
        .annotate(n=Count('id'))
    )
    return {row['parent__author_id']: row['n'] for row in rows}
