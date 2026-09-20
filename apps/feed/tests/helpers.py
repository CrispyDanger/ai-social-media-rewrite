from datetime import timedelta

from django.utils import timezone

from apps.account.models import Follow, User
from apps.interaction.models import Like
from apps.post.models import Post, Repost


def create_user(username):
    return User.objects.create_user(
        email=f'{username}@example.com',
        username=username,
        password='password',
        display_name=username.title(),
    )


def create_post(author, text='hello', created_at=None, parent=None):
    post = Post.objects.create(author=author, text=text, parent=parent)
    if created_at is not None:
        set_created_at(post, created_at)
    return post


def set_created_at(instance, when):
    type(instance).objects.filter(pk=instance.pk).update(created_at=when)
    instance.refresh_from_db()


def hours_ago(hours, now=None):
    now = now or timezone.now()
    return now - timedelta(hours=hours)


def days_ago(days, now=None):
    now = now or timezone.now()
    return now - timedelta(days=days)


def follow(follower, following):
    return Follow.objects.create(follower=follower, following=following)


def like_post(user, post, created_at=None):
    like = Like.objects.create(user=user, post=post)
    if created_at is not None:
        set_created_at(like, created_at)
    return like


def repost_post(user, post, created_at=None):
    repost = Repost.objects.create(author=user, post=post)
    if created_at is not None:
        set_created_at(repost, created_at)
    return repost
