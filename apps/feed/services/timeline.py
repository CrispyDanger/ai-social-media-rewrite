from datetime import timedelta

from django.db.models import Count
from django.utils import timezone

from apps.feed.services.ranking import (
    CANDIDATE_LIMIT,
    CANDIDATE_WINDOW_DAYS,
    author_ids_user_interacts_often_with,
    score_post,
)
from apps.post.models import Post


def following_posts(user):
    author_ids = _followed_author_ids(user)
    queryset = original_posts().filter(author_id__in=author_ids)
    return annotate_engagement_counts(queryset).order_by('-created_at')


def for_you_posts(user):
    now = timezone.now()
    candidates = list(_for_you_candidates(user, now))
    affinity_ids = author_ids_user_interacts_often_with(user, now=now)
    return _rank_posts(candidates, now, affinity_ids)


def original_posts():
    return Post.objects.filter(parent__isnull=True).select_related('author')


def annotate_engagement_counts(queryset):
    return queryset.annotate(
        like_count=Count('likes', distinct=True),
        repost_count=Count('reposts', distinct=True),
        reply_count=Count('replies', distinct=True),
    )


def _followed_author_ids(user):
    following_ids = user.following.values_list('id', flat=True)
    return {*following_ids, user.id}


def _for_you_candidates(user, now):
    since = now - timedelta(days=CANDIDATE_WINDOW_DAYS)
    queryset = (
        original_posts()
        .exclude(author=user)
        .filter(created_at__gte=since)
    )
    annotated = annotate_engagement_counts(queryset)
    return annotated.order_by('-created_at')[:CANDIDATE_LIMIT]


def _rank_key(post, now, affinity_ids):
    return (-score_post(post, now, affinity_ids), -post.created_at.timestamp())


def _rank_posts(posts, now, affinity_ids):
    return sorted(posts, key=lambda post: _rank_key(post, now, affinity_ids))
